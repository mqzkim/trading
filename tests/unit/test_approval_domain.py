"""Unit tests for approval domain entities and value objects."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.approval.domain.entities import StrategyApproval
from src.approval.domain.value_objects import (
    ApprovalStatus,
    DailyBudgetTracker,
    GateResult,
    TradeReviewItem,
)


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


class TestStrategyApproval:
    def test_creation_with_all_fields(self) -> None:
        approval = _make_approval()
        assert approval.id == "appr-001"
        assert approval.score_threshold == 70.0
        assert approval.allowed_regimes == ["Bull", "Sideways"]
        assert approval.max_per_trade_pct == 8.0
        assert approval.daily_budget_cap == 10000.0
        assert approval.is_active is True
        assert approval.suspended_reasons == set()

    def test_is_expired_false_for_future_expiry(self) -> None:
        approval = _make_approval(
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        assert approval.is_expired is False

    def test_is_expired_true_for_past_expiry(self) -> None:
        approval = _make_approval(
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        assert approval.is_expired is True

    def test_is_suspended_false_when_no_reasons(self) -> None:
        approval = _make_approval()
        assert approval.is_suspended is False

    def test_is_suspended_true_when_reasons_exist(self) -> None:
        approval = _make_approval(suspended_reasons={"regime_change"})
        assert approval.is_suspended is True

    def test_is_effective_true_when_active_not_expired_not_suspended(self) -> None:
        approval = _make_approval()
        assert approval.is_effective is True

    def test_is_effective_false_when_inactive(self) -> None:
        approval = _make_approval(is_active=False)
        assert approval.is_effective is False

    def test_is_effective_false_when_expired(self) -> None:
        approval = _make_approval(
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        assert approval.is_effective is False

    def test_is_effective_false_when_suspended(self) -> None:
        approval = _make_approval(suspended_reasons={"drawdown_tier2"})
        assert approval.is_effective is False

    def test_suspend_adds_reason(self) -> None:
        approval = _make_approval()
        approval.suspend("regime_change")
        assert "regime_change" in approval.suspended_reasons
        assert approval.is_suspended is True

    def test_unsuspend_removes_reason(self) -> None:
        approval = _make_approval(suspended_reasons={"regime_change"})
        approval.unsuspend("regime_change")
        assert "regime_change" not in approval.suspended_reasons
        assert approval.is_suspended is False

    def test_multiple_suspend_reasons(self) -> None:
        approval = _make_approval()
        approval.suspend("regime_change")
        approval.suspend("drawdown_tier2")
        assert approval.suspended_reasons == {"regime_change", "drawdown_tier2"}
        assert approval.is_suspended is True

    def test_unsuspend_one_leaves_other(self) -> None:
        approval = _make_approval()
        approval.suspend("regime_change")
        approval.suspend("drawdown_tier2")
        approval.unsuspend("regime_change")
        assert "regime_change" not in approval.suspended_reasons
        assert "drawdown_tier2" in approval.suspended_reasons
        assert approval.is_suspended is True

    def test_revoke_sets_inactive(self) -> None:
        approval = _make_approval()
        approval.revoke()
        assert approval.is_active is False
        assert approval.is_effective is False

    def test_unsuspend_nonexistent_reason_is_noop(self) -> None:
        approval = _make_approval()
        approval.unsuspend("nonexistent")
        assert approval.is_suspended is False


class TestGateResult:
    def test_approved_result(self) -> None:
        result = GateResult(approved=True)
        assert result.approved is True
        assert result.reason == ""

    def test_rejected_result_with_reason(self) -> None:
        result = GateResult(approved=False, reason="Score too low")
        assert result.approved is False
        assert result.reason == "Score too low"


class TestDailyBudgetTracker:
    def test_remaining_calculation(self) -> None:
        tracker = DailyBudgetTracker(
            budget_cap=10000.0,
            date="2026-03-13",
            spent=3000.0,
            trade_count=2,
        )
        assert tracker.remaining == 7000.0

    def test_remaining_never_negative(self) -> None:
        tracker = DailyBudgetTracker(
            budget_cap=10000.0,
            date="2026-03-13",
            spent=12000.0,
            trade_count=5,
        )
        assert tracker.remaining == 0.0

    def test_can_spend_true_when_within_budget(self) -> None:
        tracker = DailyBudgetTracker(
            budget_cap=10000.0,
            date="2026-03-13",
            spent=3000.0,
            trade_count=2,
        )
        assert tracker.can_spend(5000.0) is True

    def test_can_spend_false_when_exceeds_budget(self) -> None:
        tracker = DailyBudgetTracker(
            budget_cap=10000.0,
            date="2026-03-13",
            spent=8000.0,
            trade_count=3,
        )
        assert tracker.can_spend(3000.0) is False

    def test_can_spend_true_for_exact_remaining(self) -> None:
        tracker = DailyBudgetTracker(
            budget_cap=10000.0,
            date="2026-03-13",
            spent=7000.0,
            trade_count=2,
        )
        assert tracker.can_spend(3000.0) is True

    def test_record_spend(self) -> None:
        tracker = DailyBudgetTracker(
            budget_cap=10000.0,
            date="2026-03-13",
            spent=0.0,
            trade_count=0,
        )
        tracker.record_spend(2500.0)
        assert tracker.spent == 2500.0
        assert tracker.trade_count == 1


class TestApprovalStatus:
    def test_status_values(self) -> None:
        assert ApprovalStatus.ACTIVE.value == "ACTIVE"
        assert ApprovalStatus.SUSPENDED.value == "SUSPENDED"
        assert ApprovalStatus.EXPIRED.value == "EXPIRED"
        assert ApprovalStatus.REVOKED.value == "REVOKED"


class TestTradeReviewItem:
    def test_creation(self) -> None:
        item = TradeReviewItem(
            symbol="AAPL",
            plan_json='{"entry": 150}',
            rejection_reason="Score too low",
            pipeline_run_id="run-001",
            created_at=datetime.now(timezone.utc),
        )
        assert item.symbol == "AAPL"
        assert item.reviewed is False
        assert item.expired is False
        assert item.pipeline_run_id == "run-001"
