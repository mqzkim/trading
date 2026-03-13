"""Approval Domain -- StrategyApproval Entity.

Human-defined trading rules and daily budget cap that gate automated execution.
Expiry checked in Python (not SQL) for timezone safety, following CooldownState pattern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from src.shared.domain import Entity


@dataclass(eq=False)
class StrategyApproval(Entity[str]):
    """Strategy approval entity with suspension tracking.

    An approval defines what trades the automated pipeline can execute:
    - score_threshold: minimum composite score to auto-execute
    - allowed_regimes: market regimes where execution is permitted
    - max_per_trade_pct: max % of capital per trade
    - expires_at: mandatory expiration date
    - daily_budget_cap: daily capital limit

    Multiple suspension reasons can be active simultaneously.
    Only when ALL reasons are cleared does the approval become effective again.
    """

    _id: str = ""
    score_threshold: float = 70.0
    allowed_regimes: list[str] = field(default_factory=list)
    max_per_trade_pct: float = 8.0
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    daily_budget_cap: float = 10000.0
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    is_active: bool = True
    suspended_reasons: set[str] = field(default_factory=set)

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_expired(self) -> bool:
        """Check if approval has expired based on current UTC time."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_suspended(self) -> bool:
        """Check if approval is suspended (any reason present)."""
        return len(self.suspended_reasons) > 0

    @property
    def is_effective(self) -> bool:
        """Approval is active, not expired, and not suspended."""
        return self.is_active and not self.is_expired and not self.is_suspended

    def suspend(self, reason: str) -> None:
        """Add a suspension reason."""
        self.suspended_reasons.add(reason)

    def unsuspend(self, reason: str) -> None:
        """Remove a suspension reason. No-op if reason not present."""
        self.suspended_reasons.discard(reason)

    def revoke(self) -> None:
        """Permanently deactivate this approval."""
        self.is_active = False
