"""Unit tests for DataPipeline Korean market routing."""
from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pandas as pd

from src.data_ingest.domain.value_objects import DataQualityReport, MarketType
from src.data_ingest.infrastructure.pipeline import DataPipeline


def _make_ohlcv_df() -> pd.DataFrame:
    """Create a minimal OHLCV DataFrame for testing."""
    return pd.DataFrame(
        {
            "open": [70000.0, 70100.0],
            "high": [71000.0, 71100.0],
            "low": [69000.0, 69100.0],
            "close": [70500.0, 70600.0],
            "volume": [1000000, 1100000],
        },
        index=pd.DatetimeIndex([datetime(2026, 3, 10), datetime(2026, 3, 11)]),
    )


def _make_fund_df() -> pd.DataFrame:
    """Create a minimal Korean fundamentals DataFrame for testing."""
    return pd.DataFrame(
        {
            "bps": [50000.0, 50100.0],
            "per": [12.5, 12.6],
            "pbr": [1.2, 1.21],
            "eps": [5000.0, 5010.0],
            "div_yield": [1.8, 1.79],
            "dps": [1000.0, 1000.0],
        },
        index=pd.DatetimeIndex([datetime(2026, 3, 10), datetime(2026, 3, 11)]),
    )


def _make_passing_report(ticker: str) -> DataQualityReport:
    return DataQualityReport(
        ticker=ticker,
        passed=True,
        missing_pct=0.0,
        stale_days=0,
        outlier_count=0,
        failures=(),
    )


class TestPipelineKoreanMarket:
    """Tests for DataPipeline.ingest_ticker with market=MarketType.KR."""

    def test_kr_ticker_uses_pykrx_client(self) -> None:
        """ingest_ticker with KR market uses pykrx_client, not yfinance."""
        mock_pykrx = MagicMock()
        mock_pykrx.fetch_ohlcv = AsyncMock(return_value=_make_ohlcv_df())
        mock_pykrx.fetch_fundamentals = AsyncMock(return_value=_make_fund_df())

        mock_yfinance = MagicMock()
        mock_yfinance.fetch_ohlcv = AsyncMock()

        mock_store = MagicMock()
        mock_store.store_ohlcv = MagicMock()
        mock_store.store_kr_fundamentals = MagicMock()

        mock_quality = MagicMock()
        mock_quality.validate_ohlcv = MagicMock(
            return_value=_make_passing_report("005930")
        )

        pipeline = DataPipeline(
            duckdb_store=mock_store,
            yfinance_client=mock_yfinance,
            quality_checker=mock_quality,
            pykrx_client=mock_pykrx,
        )

        asyncio.run(pipeline.ingest_ticker("005930", market=MarketType.KR))

        mock_pykrx.fetch_ohlcv.assert_awaited_once_with("005930")
        mock_yfinance.fetch_ohlcv.assert_not_awaited()

    def test_kr_ticker_stores_ohlcv(self) -> None:
        """ingest_ticker with KR market stores OHLCV via DuckDB store."""
        mock_pykrx = MagicMock()
        mock_pykrx.fetch_ohlcv = AsyncMock(return_value=_make_ohlcv_df())
        mock_pykrx.fetch_fundamentals = AsyncMock(return_value=_make_fund_df())

        mock_store = MagicMock()
        mock_store.store_ohlcv = MagicMock()
        mock_store.store_kr_fundamentals = MagicMock()

        mock_quality = MagicMock()
        mock_quality.validate_ohlcv = MagicMock(
            return_value=_make_passing_report("005930")
        )

        pipeline = DataPipeline(
            duckdb_store=mock_store,
            quality_checker=mock_quality,
            pykrx_client=mock_pykrx,
        )

        asyncio.run(pipeline.ingest_ticker("005930", market=MarketType.KR))

        mock_store.store_ohlcv.assert_called_once()
        assert mock_store.store_ohlcv.call_args[0][0] == "005930"

    def test_kr_ticker_stores_fundamentals(self) -> None:
        """ingest_ticker with KR market stores fundamentals via store_kr_fundamentals."""
        mock_pykrx = MagicMock()
        mock_pykrx.fetch_ohlcv = AsyncMock(return_value=_make_ohlcv_df())
        mock_pykrx.fetch_fundamentals = AsyncMock(return_value=_make_fund_df())

        mock_store = MagicMock()
        mock_store.store_ohlcv = MagicMock()
        mock_store.store_kr_fundamentals = MagicMock()

        mock_quality = MagicMock()
        mock_quality.validate_ohlcv = MagicMock(
            return_value=_make_passing_report("005930")
        )

        pipeline = DataPipeline(
            duckdb_store=mock_store,
            quality_checker=mock_quality,
            pykrx_client=mock_pykrx,
        )

        asyncio.run(pipeline.ingest_ticker("005930", market=MarketType.KR))

        mock_store.store_kr_fundamentals.assert_called_once()
        assert mock_store.store_kr_fundamentals.call_args[0][0] == "005930"

    def test_kr_ticker_uses_max_stale_days_5(self) -> None:
        """ingest_ticker with KR market passes max_stale_days=5 to QualityChecker."""
        mock_pykrx = MagicMock()
        mock_pykrx.fetch_ohlcv = AsyncMock(return_value=_make_ohlcv_df())
        mock_pykrx.fetch_fundamentals = AsyncMock(return_value=_make_fund_df())

        mock_store = MagicMock()
        mock_store.store_ohlcv = MagicMock()
        mock_store.store_kr_fundamentals = MagicMock()

        mock_quality = MagicMock()
        mock_quality.validate_ohlcv = MagicMock(
            return_value=_make_passing_report("005930")
        )

        pipeline = DataPipeline(
            duckdb_store=mock_store,
            quality_checker=mock_quality,
            pykrx_client=mock_pykrx,
        )

        asyncio.run(pipeline.ingest_ticker("005930", market=MarketType.KR))

        call_args = mock_quality.validate_ohlcv.call_args
        # max_stale_days can be passed as positional arg [2] or keyword
        if "max_stale_days" in call_args.kwargs:
            assert call_args.kwargs["max_stale_days"] == 5
        else:
            assert len(call_args.args) >= 3 and call_args.args[2] == 5

    def test_us_ticker_unchanged(self) -> None:
        """ingest_ticker with US market (default) still uses yfinance."""
        mock_yfinance = MagicMock()
        ohlcv_df = pd.DataFrame(
            {
                "open": [150.0],
                "high": [155.0],
                "low": [149.0],
                "close": [153.0],
                "volume": [1000000],
            },
            index=pd.DatetimeIndex([datetime(2026, 3, 10)]),
        )
        mock_yfinance.fetch_ohlcv = AsyncMock(return_value=ohlcv_df)

        mock_edgartools = MagicMock()
        mock_edgartools.fetch_financials = AsyncMock(return_value=[])

        mock_store = MagicMock()
        mock_store.store_ohlcv = MagicMock()

        mock_quality = MagicMock()
        mock_quality.validate_ohlcv = MagicMock(
            return_value=_make_passing_report("AAPL")
        )
        mock_quality.validate_financials = MagicMock(
            return_value=_make_passing_report("AAPL")
        )

        pipeline = DataPipeline(
            duckdb_store=mock_store,
            yfinance_client=mock_yfinance,
            edgartools_client=mock_edgartools,
            quality_checker=mock_quality,
        )

        asyncio.run(pipeline.ingest_ticker("AAPL", market=MarketType.US))

        mock_yfinance.fetch_ohlcv.assert_awaited_once()
