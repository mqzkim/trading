"""Approval Domain -- ApprovalGateService.

Pure domain logic. Checks a trade plan against the active strategy approval
and daily budget. No external imports beyond domain types.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .value_objects import GateResult

if TYPE_CHECKING:
    from .entities import StrategyApproval


class ApprovalGateService:
    """Check a trade plan against active strategy approval + budget.

    Returns GateResult indicating whether the trade is approved or rejected.
    Checks are ordered by cheapest first: existence, effectiveness, score,
    regime, position %, budget.
    """

    def check(
        self,
        plan_symbol: str,
        plan_score: float,
        plan_position_pct: float,
        current_regime: str,
        daily_remaining: float,
        plan_position_value: float,
        approval: Optional[StrategyApproval],
    ) -> GateResult:
        """Run all gate checks against the given approval."""
        if approval is None:
            return GateResult(approved=False, reason="No active approval")

        if not approval.is_effective:
            return GateResult(approved=False, reason="Approval not effective")

        if plan_score < approval.score_threshold:
            return GateResult(
                approved=False,
                reason=f"Score {plan_score} below threshold {approval.score_threshold}",
            )

        if current_regime not in approval.allowed_regimes:
            return GateResult(
                approved=False,
                reason=f"Regime {current_regime} not allowed",
            )

        if plan_position_pct > approval.max_per_trade_pct:
            return GateResult(
                approved=False,
                reason=(
                    f"Position {plan_position_pct}% exceeds "
                    f"max {approval.max_per_trade_pct}%"
                ),
            )

        if plan_position_value > daily_remaining:
            return GateResult(
                approved=False,
                reason=(
                    f"Position ${plan_position_value} exceeds "
                    f"remaining budget ${daily_remaining}"
                ),
            )

        return GateResult(approved=True)
