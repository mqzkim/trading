"""Integration tests for DataPipeline -- end-to-end data ingestion.

Tests use DuckDB :memory: and mock YFinanceClient/EdgartoolsClient
to avoid real network calls. Validates the full pipeline flow:
fetch -> validate -> store -> publish events.
"""
from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from src.data_ingest.domain.events import DataIngestedEvent, QualityCheckFailedEvent
from src.data_ingest.infrastructure.duckdb_store import DuckDBStore
from src.data_ingest.infrastructure.pipeline import DataPipeline
from src.data_ingest.infrastructure.quality_checker import QualityChecker
from src.shared.infrastructure.event_bus import AsyncEventBus


def _make_ohlcv_df(ticker: str, rows: int = 100) -> pd.DataFrame:
    """Create a sample OHLCV DataFrame matching YFinanceClient output format.

    Returns DataFrame with DatetimeIndex and columns: open, high, low, close, volume.
    (Pipeline handles conversion to DuckDB schema before storage.)
    """
    dates = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=rows)
    return pd.DataFrame(
        {
            "open": [150.0 + i * 0.1 for i in range(rows)],
            "high": [152.0 + i * 0.1 for i in range(rows)],
            "low": [148.0 + i * 0.1 for i in range(rows)],
            "close": [151.0 + i * 0.1 for i in range(rows)],
            "volume": [1_000_000 + i * 1000 for i in range(rows)],
        },
        index=dates,
    )


def _make_ohlcv_df_bad(ticker: str, rows: int = 100) -> pd.DataFrame:
    """Create an OHLCV DataFrame with >5% missing values (quality fail).

    Returns DatetimeIndex DataFrame matching YFinanceClient format.
    """
    dates = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=rows)
    data = {
        "open": [150.0] * rows,
        "high": [152.0] * rows,
        "low": [148.0] * rows,
        "close": [151.0] * rows,
        "volume": [1_000_000] * rows,
    }
    df = pd.DataFrame(data, index=dates)
    # Introduce >5% missing (set 10% of cells to NaN)
    import numpy as np

    mask = np.random.default_rng(42).random(df.shape) < 0.10
    df = df.mask(mask)
    return df


def _make_financial_records(
    ticker: str, quarters: int = 4
) -> list[dict[str, Any]]:
    """Create sample financial records with filing_date."""
    base_date = date(2025, 3, 15)
    records: list[dict[str, Any]] = []
    for i in range(quarters):
        period_end = base_date - timedelta(days=90 * i)
        filing_date = period_end + timedelta(days=45)
        records.append(
            {
                "ticker": ticker,
                "period_end": period_end,
                "filing_date": filing_date,
                "form_type": "10-Q",
                "revenue": 80_000_000_000 + i * 1_000_000_000,
                "net_income": 20_000_000_000 + i * 500_000_000,
                "total_assets": 300_000_000_000,
                "total_liabilities": 200_000_000_000,
                "working_capital": 100_000_000_000,
                "retained_earnings": 50_000_000_000,
                "ebit": 25_000_000_000,
                "operating_cashflow": 22_000_000_000,
                "free_cashflow": 18_000_000_000,
                "current_ratio": 1.5,
                "debt_to_equity": 0.5,
                "roa": 0.08,
                "roe": 0.15,
            }
        )
    return records


@pytest.fixture
def duckdb_store() -> DuckDBStore:
    """In-memory DuckDB store for testing."""
    store = DuckDBStore()
    store.connect(":memory:")
    yield store
    store.close()


@pytest.fixture
def event_bus() -> AsyncEventBus:
    return AsyncEventBus()


@pytest.fixture
def quality_checker() -> QualityChecker:
    return QualityChecker()


def _build_pipeline(
    duckdb_store: DuckDBStore,
    event_bus: AsyncEventBus,
    quality_checker: QualityChecker,
    yfinance_mock: AsyncMock,
    edgartools_mock: AsyncMock,
) -> DataPipeline:
    """Build a DataPipeline with mocked data clients."""
    return DataPipeline(
        max_concurrent=5,
        db_path=":memory:",
        yfinance_client=yfinance_mock,
        edgartools_client=edgartools_mock,
        duckdb_store=duckdb_store,
        quality_checker=quality_checker,
        event_bus=event_bus,
    )


# ── Single Ticker ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_single_ticker(
    duckdb_store: DuckDBStore,
    event_bus: AsyncEventBus,
    quality_checker: QualityChecker,
) -> None:
    """Pipeline ingests a single ticker: OHLCV + financials stored, event published."""
    ticker = "AAPL"
    events_received: list[Any] = []
    event_bus.subscribe(DataIngestedEvent, lambda e: events_received.append(e))

    yfinance_mock = AsyncMock()
    yfinance_mock.fetch_ohlcv = AsyncMock(return_value=_make_ohlcv_df(ticker))

    edgartools_mock = AsyncMock()
    edgartools_mock.fetch_financials = AsyncMock(
        return_value=_make_financial_records(ticker)
    )

    pipeline = _build_pipeline(
        duckdb_store, event_bus, quality_checker, yfinance_mock, edgartools_mock
    )

    report = await pipeline.ingest_ticker(ticker)

    # Verify quality report
    assert report is not None
    assert report.passed is True

    # Verify OHLCV stored
    ohlcv_result = duckdb_store.get_ohlcv(ticker)
    assert len(ohlcv_result) > 0

    # Verify financials stored
    fin_result = duckdb_store.get_latest_financials(ticker, date(2026, 12, 31))
    assert len(fin_result) > 0

    # Verify event published
    assert len(events_received) == 1
    assert events_received[0].ticker == ticker
    assert events_received[0].ohlcv_rows > 0


# ── Quality Failure ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_quality_failure(
    duckdb_store: DuckDBStore,
    event_bus: AsyncEventBus,
    quality_checker: QualityChecker,
) -> None:
    """Bad OHLCV data -> QualityCheckFailedEvent published, ticker excluded from DuckDB."""
    ticker = "BAD"
    quality_events: list[Any] = []
    event_bus.subscribe(
        QualityCheckFailedEvent, lambda e: quality_events.append(e)
    )
    ingested_events: list[Any] = []
    event_bus.subscribe(
        DataIngestedEvent, lambda e: ingested_events.append(e)
    )

    yfinance_mock = AsyncMock()
    yfinance_mock.fetch_ohlcv = AsyncMock(return_value=_make_ohlcv_df_bad(ticker))

    edgartools_mock = AsyncMock()
    edgartools_mock.fetch_financials = AsyncMock(return_value=[])

    pipeline = _build_pipeline(
        duckdb_store, event_bus, quality_checker, yfinance_mock, edgartools_mock
    )

    report = await pipeline.ingest_ticker(ticker)

    # Quality check should fail
    assert report is not None
    assert report.passed is False

    # QualityCheckFailedEvent should be published
    assert len(quality_events) == 1
    assert quality_events[0].ticker == ticker

    # DataIngestedEvent should NOT be published
    assert len(ingested_events) == 0

    # Ticker should NOT be stored in DuckDB
    ohlcv_result = duckdb_store.get_ohlcv(ticker)
    assert len(ohlcv_result) == 0


# ── Batch Ingestion ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_batch(
    duckdb_store: DuckDBStore,
    event_bus: AsyncEventBus,
    quality_checker: QualityChecker,
) -> None:
    """Batch ingestion of 5 tickers: all stored correctly."""
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    events_received: list[Any] = []
    event_bus.subscribe(DataIngestedEvent, lambda e: events_received.append(e))

    async def mock_ohlcv(ticker: str, days: int = 756) -> pd.DataFrame:
        return _make_ohlcv_df(ticker, rows=50)

    async def mock_financials(
        ticker: str, quarters: int = 12
    ) -> list[dict[str, Any]]:
        return _make_financial_records(ticker, quarters=2)

    yfinance_mock = AsyncMock()
    yfinance_mock.fetch_ohlcv = AsyncMock(side_effect=mock_ohlcv)

    edgartools_mock = AsyncMock()
    edgartools_mock.fetch_financials = AsyncMock(side_effect=mock_financials)

    pipeline = _build_pipeline(
        duckdb_store, event_bus, quality_checker, yfinance_mock, edgartools_mock
    )

    result = await pipeline.ingest_universe(tickers)

    assert result["total"] == 5
    assert result["succeeded_count"] == 5
    assert result["failed_count"] == 0
    assert result["errors_count"] == 0

    # All 5 tickers should have events
    assert len(events_received) == 5
    event_tickers = {e.ticker for e in events_received}
    assert event_tickers == set(tickers)

    # All 5 should be stored
    for ticker in tickers:
        ohlcv = duckdb_store.get_ohlcv(ticker)
        assert len(ohlcv) > 0, f"OHLCV not stored for {ticker}"


# ── Point-in-Time Query ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_point_in_time_query(duckdb_store: DuckDBStore) -> None:
    """Store financials with different filing_dates, verify as_of_date filter."""
    ticker = "PIT"

    records = [
        {
            "ticker": ticker,
            "period_end": date(2025, 3, 31),
            "filing_date": date(2025, 5, 10),
            "form_type": "10-Q",
            "revenue": 80_000_000_000,
            "net_income": 20_000_000_000,
            "total_assets": 300_000_000_000,
            "total_liabilities": 200_000_000_000,
            "working_capital": 100_000_000_000,
            "retained_earnings": 50_000_000_000,
            "ebit": 25_000_000_000,
            "operating_cashflow": 22_000_000_000,
            "free_cashflow": 18_000_000_000,
            "current_ratio": 1.5,
            "debt_to_equity": 0.5,
            "roa": 0.08,
            "roe": 0.15,
        },
        {
            "ticker": ticker,
            "period_end": date(2025, 6, 30),
            "filing_date": date(2025, 8, 15),
            "form_type": "10-Q",
            "revenue": 90_000_000_000,
            "net_income": 25_000_000_000,
            "total_assets": 320_000_000_000,
            "total_liabilities": 210_000_000_000,
            "working_capital": 110_000_000_000,
            "retained_earnings": 55_000_000_000,
            "ebit": 28_000_000_000,
            "operating_cashflow": 24_000_000_000,
            "free_cashflow": 20_000_000_000,
            "current_ratio": 1.6,
            "debt_to_equity": 0.45,
            "roa": 0.09,
            "roe": 0.18,
        },
    ]

    duckdb_store.store_financials(ticker, records)

    # Query as of June 1, 2025: only Q1 filing (May 10) should be visible
    result_june = duckdb_store.get_latest_financials(ticker, date(2025, 6, 1))
    assert len(result_june) == 1
    assert result_june.iloc[0]["revenue"] == 80_000_000_000

    # Query as of Sept 1, 2025: Q2 filing (Aug 15) should be visible
    result_sept = duckdb_store.get_latest_financials(ticker, date(2025, 9, 1))
    assert len(result_sept) == 1
    assert result_sept.iloc[0]["revenue"] == 90_000_000_000

    # Query as of April 1, 2025: no filing yet (earliest is May 10)
    result_april = duckdb_store.get_latest_financials(ticker, date(2025, 4, 1))
    assert len(result_april) == 0
