"""Approval Domain -- Value Objects.

ApprovalStatus: lifecycle enum.
GateResult: approval check outcome.
DailyBudgetTracker: daily capital tracking.
TradeReviewItem: rejected trade awaiting manual review.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ApprovalStatus(Enum):
    """Approval lifecycle status."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class GateResult:
    """Result of an approval gate check."""

    approved: bool
    reason: str = ""


@dataclass
class DailyBudgetTracker:
    """Tracks daily capital spending against a budget cap.

    Resets daily by UTC date. Spent is recorded at order submission time.
    """

    budget_cap: float
    date: str  # YYYY-MM-DD
    spent: float = 0.0
    trade_count: int = 0

    @property
    def remaining(self) -> float:
        """Remaining budget for today. Never negative."""
        return max(0.0, self.budget_cap - self.spent)

    def can_spend(self, amount: float) -> bool:
        """Check if amount is within remaining budget."""
        return amount <= self.remaining

    def record_spend(self, amount: float) -> None:
        """Record a spend against today's budget."""
        self.spent += amount
        self.trade_count += 1


@dataclass
class TradeReviewItem:
    """A trade that was rejected by the gate and queued for manual review."""

    symbol: str
    plan_json: str
    rejection_reason: str
    pipeline_run_id: Optional[str] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    reviewed: bool = False
    expired: bool = False
    id: Optional[int] = None
