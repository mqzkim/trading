"""Integration tests for approval application layer and pipeline gate.

Tests ApprovalHandler CRUD, regime/drawdown suspension, pipeline _run_execute
with mocked approval gate, and budget tracking.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.approval.application.commands import (
    CreateApprovalCommand,
    RevokeApprovalCommand,
    ResumeApprovalCommand,
    ReviewTradeCommand,
)
from src.approval.application.handlers import ApprovalHandler
from src.approval.domain.entities import StrategyApproval
from src.approval.domain.services import ApprovalGateService
from src.approval.domain.value_objects import (
    DailyBudgetTracker,
    GateResult,
    TradeReviewItem,
)
from src.approval.infrastructure import (
    SqliteApprovalRepository,
    SqliteBudgetRepository,
    SqliteReviewQueueRepository,
)


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def approval_repo():
    return SqliteApprovalRepository(db_path=":memory:")


@pytest.fixture
def budget_repo():
    return SqliteBudgetRepository(db_path=":memory:")


@pytest.fixture
def review_queue_repo():
    return SqliteReviewQueueRepository(db_path=":memory:")


@pytest.fixture
def handler(approval_repo, budget_repo, review_queue_repo):
    return ApprovalHandler(
        approval_repo=approval_repo,
        budget_repo=budget_repo,
        review_queue_repo=review_queue_repo,
    )


@pytest.fixture
def create_cmd():
    return CreateApprovalCommand(
        score_threshold=60.0,
        allowed_regimes=["Bull", "Sideways"],
        max_per_trade_pct=8.0,
        daily_budget_cap=50000.0,
        expires_in_days=30,
    )


# ── ApprovalHandler.create ────────────────────────────────────────

class TestApprovalHandlerCreate:
    def test_create_saves_and_returns_approval(self, handler, create_cmd, approval_repo):
        approval = handler.create(create_cmd)

        assert approval is not None
        assert approval.id != ""
        assert approval.score_threshold == 60.0
        assert approval.allowed_regimes == ["Bull", "Sideways"]
        assert approval.max_per_trade_pct == 8.0
        assert approval.daily_budget_cap == 50000.0
        assert approval.is_active is True

        # Verify persisted
        stored = approval_repo.get_active()
        assert stored is not None
        assert stored.id == approval.id

    def test_create_deactivates_previous_approval(self, handler, create_cmd, approval_repo):
        first = handler.create(create_cmd)
        second = handler.create(create_cmd)

        assert second.id != first.id
        assert second.is_active is True

        # First should be deactivated
        old = approval_repo.find_by_id(first.id)
        assert old is not None
        assert old.is_active is False

    def test_create_sets_expiration(self, handler, create_cmd):
        approval = handler.create(create_cmd)
        expected_min = datetime.now(timezone.utc) + timedelta(days=29)
        assert approval.expires_at > expected_min


# ── ApprovalHandler.get_status ────────────────────────────────────

class TestApprovalHandlerGetStatus:
    def test_get_status_no_active(self, handler):
        status = handler.get_status()
        assert status["approval"] is None

    def test_get_status_with_active(self, handler, create_cmd):
        handler.create(create_cmd)
        status = handler.get_status()
        assert status["approval"] is not None
        assert "budget" in status
        assert "pending_review_count" in status


# ── ApprovalHandler.revoke ────────────────────────────────────────

class TestApprovalHandlerRevoke:
    def test_revoke_deactivates(self, handler, create_cmd, approval_repo):
        approval = handler.create(create_cmd)
        handler.revoke(RevokeApprovalCommand(approval_id=approval.id))

        stored = approval_repo.find_by_id(approval.id)
        assert stored is not None
        assert stored.is_active is False


# ── ApprovalHandler.resume ────────────────────────────────────────

class TestApprovalHandlerResume:
    def test_resume_removes_drawdown_suspension(self, handler, create_cmd, approval_repo):
        approval = handler.create(create_cmd)
        handler.suspend_for_drawdown()

        stored = approval_repo.get_active()
        assert stored is not None
        assert stored.is_suspended is True

        handler.resume(ResumeApprovalCommand())

        stored = approval_repo.get_active()
        assert stored is not None
        assert stored.is_suspended is False


# ── Regime suspension ─────────────────────────────────────────────

class TestRegimeSuspension:
    def test_suspend_if_regime_not_allowed(self, handler, create_cmd, approval_repo):
        handler.create(create_cmd)
        # "Crisis" is not in allowed_regimes ["Bull", "Sideways"]
        handler.suspend_if_regime_invalid("Crisis")

        stored = approval_repo.get_active()
        assert stored is not None
        assert "regime_change" in stored.suspended_reasons

    def test_unsuspend_when_regime_returns_to_allowed(self, handler, create_cmd, approval_repo):
        handler.create(create_cmd)
        handler.suspend_if_regime_invalid("Crisis")
        handler.suspend_if_regime_invalid("Bull")

        stored = approval_repo.get_active()
        assert stored is not None
        assert "regime_change" not in stored.suspended_reasons

    def test_no_change_if_regime_already_allowed(self, handler, create_cmd, approval_repo):
        handler.create(create_cmd)
        handler.suspend_if_regime_invalid("Bull")

        stored = approval_repo.get_active()
        assert stored is not None
        assert stored.is_suspended is False

    def test_no_active_approval_is_noop(self, handler):
        # Should not raise
        handler.suspend_if_regime_invalid("Crisis")


# ── Drawdown suspension ──────────────────────────────────────────

class TestDrawdownSuspension:
    def test_suspend_for_drawdown(self, handler, create_cmd, approval_repo):
        handler.create(create_cmd)
        handler.suspend_for_drawdown()

        stored = approval_repo.get_active()
        assert stored is not None
        assert "drawdown_tier2" in stored.suspended_reasons

    def test_drawdown_does_not_auto_clear(self, handler, create_cmd, approval_repo):
        handler.create(create_cmd)
        handler.suspend_for_drawdown()

        # Regime change should NOT clear drawdown
        handler.suspend_if_regime_invalid("Bull")

        stored = approval_repo.get_active()
        assert stored is not None
        assert "drawdown_tier2" in stored.suspended_reasons


# ── Pipeline _run_execute with approval gate ──────────────────────

class TestPipelineApprovalGate:
    def _make_mock_plan(self, symbol="AAPL", score=75.0, position_pct=5.0, position_value=5000.0):
        plan = MagicMock()
        plan.symbol = symbol
        plan.composite_score = score
        plan.position_pct = position_pct
        plan.position_value = position_value
        return plan

    def _make_handlers(
        self,
        approval_gate=None,
        approval_handler=None,
        budget_repo=None,
        review_queue_repo=None,
    ):
        handlers = {
            "trade_plan_handler": MagicMock(),
            "capital": 100000.0,
            "notifier": MagicMock(),
        }
        if approval_gate is not None:
            handlers["approval_gate"] = approval_gate
        if approval_handler is not None:
            handlers["approval_handler"] = approval_handler
        if budget_repo is not None:
            handlers["budget_repo"] = budget_repo
        if review_queue_repo is not None:
            handlers["review_queue_repo"] = review_queue_repo
        return handlers

    def test_no_approval_gate_skips_execution(self):
        from src.pipeline.domain.services import PipelineOrchestrator

        orch = PipelineOrchestrator()
        handlers = self._make_handlers()  # no approval_gate
        plans = [self._make_mock_plan()]

        result = orch._run_execute(handlers, plans)

        assert result.status == "skipped"
        assert result.symbols_processed == 0

    def test_no_active_approval_skips_execution(self):
        from src.pipeline.domain.services import PipelineOrchestrator

        orch = PipelineOrchestrator()
        approval_handler = MagicMock()
        approval_handler.get_status.return_value = {"approval": None, "budget": None, "pending_review_count": 0}

        handlers = self._make_handlers(
            approval_gate=ApprovalGateService(),
            approval_handler=approval_handler,
            budget_repo=MagicMock(),
            review_queue_repo=MagicMock(),
        )
        plans = [self._make_mock_plan()]

        result = orch._run_execute(handlers, plans)

        assert result.status == "skipped"

    def test_approved_trades_execute(self):
        from src.pipeline.domain.services import PipelineOrchestrator

        orch = PipelineOrchestrator()
        approval = StrategyApproval(
            _id="test-id",
            score_threshold=60.0,
            allowed_regimes=["Bull"],
            max_per_trade_pct=10.0,
            daily_budget_cap=50000.0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        approval_handler = MagicMock()
        approval_handler.get_status.return_value = {
            "approval": approval,
            "budget": DailyBudgetTracker(budget_cap=50000.0, date="2026-01-01"),
            "pending_review_count": 0,
        }

        budget_repo = MagicMock()
        budget_repo.get_or_create_today.return_value = DailyBudgetTracker(
            budget_cap=50000.0, date="2026-01-01"
        )

        gate = MagicMock()
        gate.check.return_value = GateResult(approved=True)

        handlers = self._make_handlers(
            approval_gate=gate,
            approval_handler=approval_handler,
            budget_repo=budget_repo,
            review_queue_repo=MagicMock(),
        )
        plans = [self._make_mock_plan()]

        result = orch._run_execute(handlers, plans)

        assert result.symbols_succeeded >= 1
        handlers["trade_plan_handler"].approve.assert_called_once()
        handlers["trade_plan_handler"].execute.assert_called_once()

    def test_rejected_trades_queued_for_review(self):
        from src.pipeline.domain.services import PipelineOrchestrator

        orch = PipelineOrchestrator()
        approval = StrategyApproval(
            _id="test-id",
            score_threshold=60.0,
            allowed_regimes=["Bull"],
            max_per_trade_pct=10.0,
            daily_budget_cap=50000.0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        approval_handler = MagicMock()
        approval_handler.get_status.return_value = {
            "approval": approval,
            "budget": DailyBudgetTracker(budget_cap=50000.0, date="2026-01-01"),
            "pending_review_count": 0,
        }

        budget_repo = MagicMock()
        budget_repo.get_or_create_today.return_value = DailyBudgetTracker(
            budget_cap=50000.0, date="2026-01-01"
        )

        gate = MagicMock()
        gate.check.return_value = GateResult(approved=False, reason="Score too low")

        review_queue_repo = MagicMock()

        handlers = self._make_handlers(
            approval_gate=gate,
            approval_handler=approval_handler,
            budget_repo=budget_repo,
            review_queue_repo=review_queue_repo,
        )
        plans = [self._make_mock_plan()]

        result = orch._run_execute(handlers, plans)

        review_queue_repo.add.assert_called_once()
        handlers["trade_plan_handler"].approve.assert_not_called()

    def test_budget_80_percent_warning(self):
        from src.pipeline.domain.services import PipelineOrchestrator

        orch = PipelineOrchestrator()
        approval = StrategyApproval(
            _id="test-id",
            score_threshold=60.0,
            allowed_regimes=["Bull"],
            max_per_trade_pct=10.0,
            daily_budget_cap=10000.0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Budget already at 75% spent
        budget = DailyBudgetTracker(budget_cap=10000.0, date="2026-01-01", spent=7500.0)

        approval_handler = MagicMock()
        approval_handler.get_status.return_value = {
            "approval": approval,
            "budget": budget,
            "pending_review_count": 0,
        }

        budget_repo = MagicMock()
        budget_repo.get_or_create_today.return_value = budget

        gate = MagicMock()
        gate.check.return_value = GateResult(approved=True)

        notifier = MagicMock()

        handlers = self._make_handlers(
            approval_gate=gate,
            approval_handler=approval_handler,
            budget_repo=budget_repo,
            review_queue_repo=MagicMock(),
        )
        handlers["notifier"] = notifier

        plan = self._make_mock_plan(position_value=1000.0)
        result = orch._run_execute(handlers, [plan])

        # After spending 1000 on top of 7500 = 8500/10000 = 85% >= 80%
        # Notifier should be called with budget warning
        notifier.notify.assert_called()
        warning_call = notifier.notify.call_args
        assert "budget" in str(warning_call).lower() or "80%" in str(warning_call).lower()
