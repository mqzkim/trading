"""Infrastructure adapter for fetching latest market prices.

Wraps DataClient to provide a simple price lookup interface
for the dashboard application layer. Graceful fallback: returns
None if data fetch fails (network error, invalid symbol, API rate limit).
"""
from __future__ import annotations

from typing import Optional


class PriceAdapter:
    """Fetches latest market price per symbol via DataClient.

    Graceful fallback: returns None if data fetch fails (network error,
    invalid symbol, API rate limit). Caller decides fallback behavior.
    """

    def __init__(self, data_client=None):
        self._client = data_client

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Return latest closing price for symbol, or None on failure."""
        if self._client is None:
            return None
        try:
            full = self._client.get_full(symbol, days=5)  # minimal history
            return full.get("price", {}).get("close")
        except Exception:
            return None

    def get_latest_prices(self, symbols: list[str]) -> dict[str, float]:
        """Batch fetch latest prices. Returns {symbol: price} for successful fetches."""
        result: dict[str, float] = {}
        for sym in symbols:
            price = self.get_latest_price(sym)
            if price is not None:
                result[sym] = price
        return result
