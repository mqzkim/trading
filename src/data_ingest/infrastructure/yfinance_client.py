"""YFinanceClient — async adapter wrapping core DataClient for OHLCV data.

Wraps the existing core/data/client.py DataClient via asyncio.run_in_executor
so that sync yfinance calls can be used in async ingestion pipelines.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import pandas as pd

from core.data.client import DataClient as CoreDataClient

logger = logging.getLogger(__name__)


class YFinanceClient:
    """DDD infrastructure adapter wrapping core DataClient.

    Provides async interface to the existing sync DataClient for use
    in concurrent ingestion pipelines with semaphore-based rate limiting.
    """

    def __init__(self, semaphore: asyncio.Semaphore | None = None) -> None:
        self._client = CoreDataClient()
        self._semaphore = semaphore

    async def fetch_ohlcv(self, ticker: str, days: int = 756) -> pd.DataFrame:
        """Fetch OHLCV data for a ticker.

        Args:
            ticker: Stock symbol (e.g., "AAPL").
            days: Number of trading days to fetch (default 756 = ~3 years).

        Returns:
            DataFrame with columns: open, high, low, close, volume.
        """
        loop = asyncio.get_running_loop()

        if self._semaphore is not None:
            async with self._semaphore:
                return await loop.run_in_executor(
                    None, self._client.get_price_history, ticker, days
                )

        return await loop.run_in_executor(
            None, self._client.get_price_history, ticker, days
        )

    async def fetch_fundamentals(self, ticker: str) -> dict[str, Any]:
        """Fetch fundamental data for a ticker.

        Args:
            ticker: Stock symbol (e.g., "AAPL").

        Returns:
            Dict with income, balance, cashflow, highlights, valuation data.
        """
        loop = asyncio.get_running_loop()

        if self._semaphore is not None:
            async with self._semaphore:
                return await loop.run_in_executor(
                    None, self._client.get_fundamentals, ticker
                )

        return await loop.run_in_executor(
            None, self._client.get_fundamentals, ticker
        )
