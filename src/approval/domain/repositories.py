"""Approval Domain -- Repository Interfaces.

Infrastructure implementations in infrastructure/ layer.
Domain depends on interfaces (ABC) only.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import StrategyApproval
from .value_objects import DailyBudgetTracker, TradeReviewItem


class IApprovalRepository(ABC):
    """Strategy approval persistence interface."""

    @abstractmethod
    def save(self, approval: StrategyApproval) -> None:
        """Persist approval. Deactivates previous active approvals."""
        ...

    @abstractmethod
    def get_active(self) -> Optional[StrategyApproval]:
        """Return the currently active approval, or None."""
        ...

    @abstractmethod
    def find_by_id(self, approval_id: str) -> Optional[StrategyApproval]:
        """Find approval by ID."""
        ...


class IBudgetRepository(ABC):
    """Daily budget tracking persistence interface."""

    @abstractmethod
    def get_or_create_today(self, budget_cap: float) -> DailyBudgetTracker:
        """Return today's budget tracker, creating with spent=0 if not exists."""
        ...

    @abstractmethod
    def save(self, tracker: DailyBudgetTracker) -> None:
        """Update the daily budget tracker."""
        ...


class IReviewQueueRepository(ABC):
    """Trade review queue persistence interface."""

    @abstractmethod
    def add(self, item: TradeReviewItem) -> int:
        """Insert a review item. Returns assigned ID."""
        ...

    @abstractmethod
    def list_pending(self) -> List[TradeReviewItem]:
        """Return non-reviewed, non-expired items."""
        ...

    @abstractmethod
    def mark_reviewed(self, item_id: int, approved: bool) -> None:
        """Mark item as reviewed."""
        ...

    @abstractmethod
    def expire_old(self, hours: int = 24) -> int:
        """Mark items older than hours as expired. Returns count expired."""
        ...
