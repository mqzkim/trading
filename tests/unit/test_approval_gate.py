"""Unit tests for ApprovalGateService."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.approval.domain.entities import StrategyApproval
from src.approval.domain.services import ApprovalGateService
from src.approval.domain.value_objects import GateResult


def _make_approval(
    *,
    score_threshold: float = 70.0,
    allowed_regimes: list[str] | None = None,
    max_per_trade_pct: float = 8.0,
    expires_at: datetime | None = None,
    daily_budget_cap: float = 10000.0,
    is_active: bool = True,
    suspended_reasons: set[str] | None = None,
) -> StrategyApproval:
    return StrategyApproval(
        _id="appr-001",
        score_threshold=score_threshold,
        allowed_regimes=allowed_regimes or ["Bull", "Sideways"],
        max_per_trade_pct=max_per_trade_pct,
        expires_at=expires_at or (datetime.now(timezone.utc) + timedelta(days=30)),
        daily_budget_cap=daily_budget_cap,
        is_active=is_active,
        suspended_reasons=suspended_reasons or set(),
    )


class TestApprovalGateService:
    def setup_method(self) -> None:
        self.gate = ApprovalGateService()

    def test_no_approval_returns_rejected(self) -> None:
        result = self.gate.check(
            plan_symbol="AAPL",
            plan_score=80.0,
            plan_position_pct=5.0,
            current_regime="Bull",
            daily_remaining=10000.0,
            plan_position_value=5000.0,
            approval=None,
        )
        assert result.approved is False
        assert "No active approval" in result.reason

    def test_approval_not_effective_returns_rejected(self) -> None:
        approval = _make_approval(
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        result = self.gate.check(
            plan_symbol="AAPL",
            plan_score=80.0,
            plan_position_pct=5.0,
            current_regime="Bull",
            daily_remaining=10000.0,
            plan_position_value=5000.0,
            approval=approval,
        )
        assert result.approved is False
        assert "not effective" in result.reason

    def test_score_below_threshold_returns_rejected(self) -> None:
        approval = _make_approval(score_threshold=70.0)
        result = self.gate.check(
            plan_symbol="AAPL",
            plan_score=60.0,
            plan_position_pct=5.0,
            current_regime="Bull",
            daily_remaining=10000.0,
            plan_position_value=5000.0,
            approval=approval,
        )
        assert result.approved is False
        assert "Score 60.0 below threshold 70.0" in result.reason

    def test_regime_not_allowed_returns_rejected(self) -> None:
        approval = _make_approval(allowed_regimes=["Bull", "Sideways"])
        result = self.gate.check(
            plan_symbol="AAPL",
            plan_score=80.0,
            plan_position_pct=5.0,
            current_regime="Crisis",
            daily_remaining=10000.0,
            plan_position_value=5000.0,
            approval=approval,
        )
        assert result.approved is False
        assert "Crisis" in result.reason
        assert "not allowed" in result.reason

    def test_position_pct_exceeds_max_returns_rejected(self) -> None:
        approval = _make_approval(max_per_trade_pct=8.0)
        result = self.gate.check(
            plan_symbol="AAPL",
            plan_score=80.0,
            plan_position_pct=10.0,
            current_regime="Bull",
            daily_remaining=10000.0,
            plan_position_value=5000.0,
            approval=approval,
        )
        assert result.approved is False
        assert "10.0%" in result.reason
        assert "8.0%" in result.reason

    def test_position_value_exceeds_daily_remaining_returns_rejected(self) -> None:
        approval = _make_approval()
        result = self.gate.check(
            plan_symbol="AAPL",
            plan_score=80.0,
            plan_position_pct=5.0,
            current_regime="Bull",
            daily_remaining=3000.0,
            plan_position_value=5000.0,
            approval=approval,
        )
        assert result.approved is False
        assert "5000.0" in result.reason
        assert "3000.0" in result.reason

    def test_all_checks_pass_returns_approved(self) -> None:
        approval = _make_approval()
        result = self.gate.check(
            plan_symbol="AAPL",
            plan_score=80.0,
            plan_position_pct=5.0,
            current_regime="Bull",
            daily_remaining=10000.0,
            plan_position_value=5000.0,
            approval=approval,
        )
        assert result.approved is True
        assert result.reason == ""

    def test_suspended_approval_returns_rejected(self) -> None:
        approval = _make_approval(suspended_reasons={"regime_change"})
        result = self.gate.check(
            plan_symbol="AAPL",
            plan_score=80.0,
            plan_position_pct=5.0,
            current_regime="Bull",
            daily_remaining=10000.0,
            plan_position_value=5000.0,
            approval=approval,
        )
        assert result.approved is False
        assert "not effective" in result.reason

    def test_exact_threshold_score_passes(self) -> None:
        approval = _make_approval(score_threshold=70.0)
        result = self.gate.check(
            plan_symbol="AAPL",
            plan_score=70.0,
            plan_position_pct=5.0,
            current_regime="Bull",
            daily_remaining=10000.0,
            plan_position_value=5000.0,
            approval=approval,
        )
        assert result.approved is True

    def test_exact_max_pct_passes(self) -> None:
        approval = _make_approval(max_per_trade_pct=8.0)
        result = self.gate.check(
            plan_symbol="AAPL",
            plan_score=80.0,
            plan_position_pct=8.0,
            current_regime="Bull",
            daily_remaining=10000.0,
            plan_position_value=5000.0,
            approval=approval,
        )
        assert result.approved is True
