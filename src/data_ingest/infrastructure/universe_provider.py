"""UniverseProvider — S&P 500 + S&P 400 ticker universe management.

Scrapes Wikipedia for current index constituents, excludes Financials
and Utilities sectors, normalizes column names, and caches results
in memory with 24-hour TTL.
"""
from __future__ import annotations

import logging
import time

import pandas as pd

logger = logging.getLogger(__name__)

_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
_SP400_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"

_EXCLUDED_SECTORS = frozenset({"Financials", "Utilities"})

# Standard column mapping for S&P 500 Wikipedia table
_SP500_COL_MAP = {
    "Symbol": "ticker",
    "Security": "name",
    "GICS Sector": "sector",
    "GICS Sub-Industry": "sub_industry",
}

# S&P 400 Wikipedia may use different column names
_SP400_COL_MAP = {
    "Symbol": "ticker",
    "Company": "name",
    "GICS Sector": "sector",
    "GICS Sub-Industry": "sub_industry",
}


class UniverseProvider:
    """Provides the investable universe of S&P 500 + S&P 400 tickers.

    Excludes Financials and Utilities sectors per user decision.
    Caches results in memory for 24 hours to avoid repeated scraping.
    """

    CACHE_TTL = 86400  # 24 hours in seconds

    def __init__(self) -> None:
        self._cache: pd.DataFrame | None = None
        self._cache_time: float | None = None

    def get_sp500_tickers(self) -> pd.DataFrame:
        """Scrape S&P 500 constituents from Wikipedia.

        Returns:
            DataFrame with columns: ticker, name, sector, sub_industry.
        """
        tables = pd.read_html(_SP500_URL)
        df = tables[0]

        # Select and rename columns
        available_cols = {c for c in _SP500_COL_MAP if c in df.columns}
        rename_map = {c: _SP500_COL_MAP[c] for c in available_cols}
        df = df[list(available_cols)].rename(columns=rename_map)

        return df[["ticker", "name", "sector", "sub_industry"]]

    def get_sp400_tickers(self) -> pd.DataFrame:
        """Scrape S&P 400 constituents from Wikipedia.

        Returns:
            DataFrame with columns: ticker, name, sector, sub_industry.
            Returns empty DataFrame if scraping fails.
        """
        try:
            tables = pd.read_html(_SP400_URL)
            df = tables[0]

            # Try S&P 400 column mapping first
            rename_map: dict[str, str] = {}
            for orig, target in _SP400_COL_MAP.items():
                if orig in df.columns:
                    rename_map[orig] = target

            # Fallback: try S&P 500 column mapping
            if "ticker" not in rename_map.values():
                for orig, target in _SP500_COL_MAP.items():
                    if orig in df.columns and target not in rename_map.values():
                        rename_map[orig] = target

            df = df[list(rename_map.keys())].rename(columns=rename_map)

            required_cols = ["ticker", "name", "sector", "sub_industry"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ""

            return df[required_cols]

        except Exception:
            logger.error("Failed to scrape S&P 400 tickers", exc_info=True)
            return pd.DataFrame(columns=["ticker", "name", "sector", "sub_industry"])

    def get_universe(self) -> pd.DataFrame:
        """Return the combined S&P 500 + S&P 400 universe.

        Excludes Financials and Utilities sectors.
        Deduplicates by ticker.
        Caches the result in memory for CACHE_TTL seconds.

        Returns:
            DataFrame with columns: ticker, name, sector, sub_industry.
        """
        # Check cache
        if (
            self._cache is not None
            and self._cache_time is not None
            and (time.time() - self._cache_time) < self.CACHE_TTL
        ):
            return self._cache

        sp500 = self.get_sp500_tickers()
        sp400 = self.get_sp400_tickers()

        combined = pd.concat([sp500, sp400], ignore_index=True)

        # Exclude Financials and Utilities
        combined = combined[~combined["sector"].isin(_EXCLUDED_SECTORS)]

        # Deduplicate by ticker
        combined = combined.drop_duplicates(subset=["ticker"], keep="first")

        combined = combined.reset_index(drop=True)

        # Cache
        self._cache = combined
        self._cache_time = time.time()

        return combined

    def get_sectors(self) -> list[str]:
        """Return unique GICS sectors in the current universe.

        Returns:
            Sorted list of sector names (excluding Financials and Utilities).
        """
        universe = self.get_universe()
        return sorted(universe["sector"].unique().tolist())
