"""PyKRXClient -- async adapter for Korean market data via pykrx.

Fetches KOSPI/KOSDAQ OHLCV and fundamental data from KRX.
Wraps synchronous pykrx calls via asyncio executor.
Enforces 1-second rate limit between requests per RESEARCH pitfall 4.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta

import pandas as pd
from pykrx import stock

logger = logging.getLogger(__name__)

# pykrx returns Korean column names for OHLCV
_OHLCV_COLUMN_MAP = {
    "\uc2dc\uac00": "open",   # 시가
    "\uace0\uac00": "high",   # 고가
    "\uc800\uac00": "low",    # 저가
    "\uc885\uac00": "close",  # 종가
    "\uac70\ub798\ub7c9": "volume",  # 거래량
}

# pykrx fundamental columns: BPS/PER/PBR/EPS already English-ish,
# but DIV needs renaming to div_yield to avoid Python keyword confusion
_FUNDAMENTAL_COLUMN_MAP = {
    "BPS": "bps",
    "PER": "per",
    "PBR": "pbr",
    "EPS": "eps",
    "DIV": "div_yield",
    "DPS": "dps",
}


class PyKRXClient:
    """Korean market data adapter using pykrx.

    Provides async interface to the synchronous pykrx library.
    Enforces 1-second delay between KRX requests to avoid rate limiting.

    Usage:
        client = PyKRXClient()
        ohlcv_df = await client.fetch_ohlcv("005930", days=756)
        fund_df = await client.fetch_fundamentals("005930", days=365)
    """

    def __init__(self, semaphore: asyncio.Semaphore | None = None) -> None:
        self._semaphore = semaphore

    async def fetch_ohlcv(self, ticker: str, days: int = 756) -> pd.DataFrame:
        """Fetch OHLCV data for a Korean ticker.

        Args:
            ticker: Korean stock ticker (e.g., "005930" for Samsung).
            days: Number of calendar days to fetch (default 756 ~ 3 years).

        Returns:
            DataFrame with columns: open, high, low, close, volume.
            Empty DataFrame if no data available.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_ohlcv_sync, ticker, days)

    async def fetch_fundamentals(self, ticker: str, days: int = 365) -> pd.DataFrame:
        """Fetch fundamental data (PER/PBR/EPS/BPS/DIV/DPS) for a Korean ticker.

        Args:
            ticker: Korean stock ticker (e.g., "005930").
            days: Number of calendar days to fetch (default 365).

        Returns:
            DataFrame with columns: bps, per, pbr, eps, div_yield, dps.
            Empty DataFrame if no data available.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self._fetch_fundamentals_sync, ticker, days
        )

    def _fetch_ohlcv_sync(self, ticker: str, days: int) -> pd.DataFrame:
        """Synchronous OHLCV fetch -- runs in executor thread."""
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=int(days * 1.4))).strftime(
            "%Y%m%d"
        )

        logger.debug("Fetching OHLCV for %s: %s to %s", ticker, start_date, end_date)
        df = stock.get_market_ohlcv(start_date, end_date, ticker)

        # Rate limit: 1 second between KRX requests
        time.sleep(1.0)

        if df.empty:
            return df

        # Rename Korean columns to English
        df = df.rename(columns=_OHLCV_COLUMN_MAP)

        # Keep only expected columns (pykrx may include extra like 등락률)
        expected = ["open", "high", "low", "close", "volume"]
        available = [c for c in expected if c in df.columns]
        return df[available]

    def _fetch_fundamentals_sync(self, ticker: str, days: int) -> pd.DataFrame:
        """Synchronous fundamentals fetch -- runs in executor thread."""
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=int(days * 1.4))).strftime(
            "%Y%m%d"
        )

        logger.debug(
            "Fetching fundamentals for %s: %s to %s", ticker, start_date, end_date
        )
        df = stock.get_market_fundamental(start_date, end_date, ticker)

        # Rate limit: 1 second between KRX requests
        time.sleep(1.0)

        if df.empty:
            return df

        # Rename columns to lowercase English with div_yield
        df = df.rename(columns=_FUNDAMENTAL_COLUMN_MAP)

        expected = ["bps", "per", "pbr", "eps", "div_yield", "dps"]
        available = [c for c in expected if c in df.columns]
        return df[available]
