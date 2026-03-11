"""DataPipeline -- end-to-end async data ingestion pipeline.

Orchestrates: fetch tickers -> fetch data -> quality check -> store -> publish events.
Uses asyncio.Semaphore for concurrent ingestion (configurable 5-10 parallel).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import pandas as pd

from src.data_ingest.domain.events import DataIngestedEvent, QualityCheckFailedEvent
from src.data_ingest.domain.value_objects import DataQualityReport
from src.data_ingest.infrastructure.duckdb_store import DuckDBStore
from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient
from src.data_ingest.infrastructure.quality_checker import QualityChecker
from src.data_ingest.infrastructure.universe_provider import UniverseProvider
from src.data_ingest.infrastructure.yfinance_client import YFinanceClient
from src.shared.infrastructure.event_bus import AsyncEventBus

logger = logging.getLogger(__name__)


class DataPipeline:
    """End-to-end data ingestion pipeline.

    Fetches OHLCV + financial data, validates quality, stores in DuckDB,
    and publishes domain events for downstream consumers.

    Usage:
        pipeline = DataPipeline(max_concurrent=5, db_path=":memory:")
        result = await pipeline.ingest_universe(["AAPL", "MSFT"])
        await pipeline.close()
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        db_path: str = "data/analytics.duckdb",
        *,
        yfinance_client: YFinanceClient | None = None,
        edgartools_client: EdgartoolsClient | None = None,
        duckdb_store: DuckDBStore | None = None,
        quality_checker: QualityChecker | None = None,
        event_bus: AsyncEventBus | None = None,
        universe_provider: UniverseProvider | None = None,
    ) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent)

        self._yfinance = yfinance_client or YFinanceClient(self._semaphore)
        self._edgartools = edgartools_client or EdgartoolsClient(self._semaphore)
        self._store = duckdb_store or DuckDBStore()
        self._quality = quality_checker or QualityChecker()
        self._event_bus = event_bus or AsyncEventBus()
        self._universe = universe_provider or UniverseProvider()

        if duckdb_store is None:
            self._store.connect(db_path)

    @property
    def event_bus(self) -> AsyncEventBus:
        """Expose event bus for subscribing handlers."""
        return self._event_bus

    async def ingest_ticker(self, ticker: str) -> DataQualityReport | None:
        """Ingest a single ticker: fetch, validate, store, publish.

        Args:
            ticker: Stock symbol (e.g., "AAPL").

        Returns:
            DataQualityReport if ingestion completed (pass or fail),
            None if an unrecoverable error occurred.
        """
        try:
            # 1. Fetch OHLCV
            async with self._semaphore:
                ohlcv_df = await self._yfinance.fetch_ohlcv(ticker)

            # 2. Validate OHLCV
            ohlcv_report = self._quality.validate_ohlcv(ticker, ohlcv_df)
            if not ohlcv_report.passed:
                await self._event_bus.publish(
                    QualityCheckFailedEvent(
                        ticker=ticker,
                        failures=ohlcv_report.failures,
                    )
                )
                logger.warning(
                    "OHLCV quality check failed for %s: %s",
                    ticker,
                    ohlcv_report.failures,
                )
                return ohlcv_report

            # 3. Fetch financials
            async with self._semaphore:
                financial_records = await self._edgartools.fetch_financials(ticker)

            # 4. Validate financials
            fin_report = self._quality.validate_financials(ticker, financial_records)
            if not fin_report.passed:
                logger.warning(
                    "Financial quality check failed for %s: %s (OHLCV still stored)",
                    ticker,
                    fin_report.failures,
                )

            # 5. Store OHLCV -- prepare DataFrame for DuckDB schema
            store_df = self._prepare_ohlcv_for_storage(ticker, ohlcv_df)
            self._store.store_ohlcv(ticker, store_df)

            # 6. Store financials -- store even if validation has warnings
            if financial_records:
                self._store.store_financials(ticker, financial_records)

            # 7. Publish success event
            await self._event_bus.publish(
                DataIngestedEvent(
                    ticker=ticker,
                    ohlcv_rows=len(ohlcv_df),
                    financial_quarters=len(financial_records),
                )
            )

            return ohlcv_report

        except Exception:
            logger.error("Failed to ingest %s", ticker, exc_info=True)
            return None

    async def ingest_universe(
        self, tickers: list[str] | None = None
    ) -> dict[str, Any]:
        """Ingest multiple tickers concurrently.

        Args:
            tickers: List of ticker symbols. If None, uses UniverseProvider.

        Returns:
            Summary dict with succeeded, failed, errors lists and counts.
        """
        if tickers is None:
            universe_df = self._universe.get_universe()
            tickers = universe_df["ticker"].tolist()

        tasks = [self.ingest_ticker(t) for t in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        succeeded: list[str] = []
        failed: list[str] = []
        errors: list[str] = []

        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                errors.append(ticker)
                logger.error("Exception ingesting %s: %s", ticker, result)
            elif result is None:
                errors.append(ticker)
            elif isinstance(result, DataQualityReport) and not result.passed:
                failed.append(ticker)
            else:
                succeeded.append(ticker)

        return {
            "total": len(tickers),
            "succeeded": succeeded,
            "succeeded_count": len(succeeded),
            "failed": failed,
            "failed_count": len(failed),
            "errors": errors,
            "errors_count": len(errors),
        }

    @staticmethod
    def _prepare_ohlcv_for_storage(ticker: str, df: pd.DataFrame) -> pd.DataFrame:
        """Convert OHLCV DataFrame to DuckDB table schema format.

        YFinanceClient returns DataFrame with DatetimeIndex and columns
        (open, high, low, close, volume). DuckDB needs flat DataFrame with
        columns (ticker, date, open, high, low, close, volume).
        """
        result = df.copy()

        # If date is in the index (typical yfinance format), move to column
        if "date" not in result.columns:
            result = result.reset_index()
            # The index might be named 'Date', 'date', or unnamed
            if "Date" in result.columns:
                result = result.rename(columns={"Date": "date"})
            elif "index" in result.columns:
                result = result.rename(columns={"index": "date"})

        # Add ticker column if missing
        if "ticker" not in result.columns:
            result.insert(0, "ticker", ticker)

        # Normalize column names to lowercase
        result.columns = [c.lower() for c in result.columns]

        # Select only the columns DuckDB expects, in order
        expected = ["ticker", "date", "open", "high", "low", "close", "volume"]
        return result[expected]

    async def close(self) -> None:
        """Close DuckDB connection and cleanup resources."""
        self._store.close()
