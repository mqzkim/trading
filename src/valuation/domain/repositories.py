"""Valuation domain -- Repository Interface (ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Optional


class IValuationRepository(ABC):
    """Valuation persistence interface. Implementation in infrastructure/."""

    @abstractmethod
    def save_valuation(self, ticker: str, result_dict: dict[str, Any]) -> None:
        """Persist valuation result for a ticker."""
        ...

    @abstractmethod
    def get_valuation(
        self, ticker: str, as_of_date: Optional[date] = None
    ) -> Optional[dict[str, Any]]:
        """Retrieve latest valuation for a ticker, optionally as-of a date."""
        ...
