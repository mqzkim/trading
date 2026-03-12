"""Backtest domain -- Repository Interface (ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class IBacktestResultRepository(ABC):
    """Persistence interface for backtest results."""

    @abstractmethod
    def save(self, symbol: str, config: dict, report: dict) -> None: ...

    @abstractmethod
    def find_latest(self, symbol: str) -> Optional[dict]: ...

    @abstractmethod
    def find_all(self) -> list[dict]: ...
