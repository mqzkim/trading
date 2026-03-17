"""Performance domain -- repository interfaces (ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .entities import ClosedTrade


class ITradeHistoryRepository(ABC):
    """Trade history persistence interface."""

    @abstractmethod
    def save(self, trade: ClosedTrade) -> None: ...

    @abstractmethod
    def find_all(self) -> list[ClosedTrade]: ...

    @abstractmethod
    def count(self) -> int: ...


class IProposalRepository(ABC):
    """Parameter proposal persistence interface."""

    @abstractmethod
    def save(self, proposal: dict) -> None: ...

    @abstractmethod
    def find_pending(self) -> list[dict]: ...

    @abstractmethod
    def find_by_id(self, proposal_id: str) -> Optional[dict]: ...

    @abstractmethod
    def approve(self, proposal_id: str) -> None: ...

    @abstractmethod
    def reject(self, proposal_id: str) -> None: ...

    @abstractmethod
    def list_history(self, limit: int = 5) -> list[dict]: ...
