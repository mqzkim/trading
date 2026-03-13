"""Approval Application -- Command dataclasses.

Immutable command objects for approval handler operations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CreateApprovalCommand:
    """Create a new strategy approval."""

    score_threshold: float
    allowed_regimes: list[str]
    max_per_trade_pct: float
    daily_budget_cap: float
    expires_in_days: int


@dataclass(frozen=True)
class RevokeApprovalCommand:
    """Revoke an approval (active or by ID)."""

    approval_id: Optional[str] = None


@dataclass(frozen=True)
class ResumeApprovalCommand:
    """Resume a suspended approval (remove drawdown_tier2 reason)."""

    approval_id: Optional[str] = None


@dataclass(frozen=True)
class ReviewTradeCommand:
    """Approve or reject a queued trade."""

    symbol: str = ""
    approved: bool = False
