"""Tests for CLI approval and review commands.

Uses typer.testing.CliRunner with mocked bootstrap context.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.main import app
from src.approval.domain.entities import StrategyApproval
from src.approval.domain.value_objects import DailyBudgetTracker, TradeReviewItem


runner = CliRunner()


def _make_mock_ctx():
    """Create a mock bootstrap context with approval components."""
    approval = StrategyApproval(
        _id="test-approval-id",
        score_threshold=60.0,
        allowed_regimes=["Bull", "Sideways"],
        max_per_trade_pct=8.0,
        daily_budget_cap=50000.0,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )

    approval_handler = MagicMock()
    approval_handler.create.return_value = approval
    approval_handler.get_status.return_value = {
        "approval": approval,
        "budget": DailyBudgetTracker(budget_cap=50000.0, date="2026-01-01", spent=5000.0),
        "pending_review_count": 2,
    }

    review_queue_repo = MagicMock()
    review_queue_repo.list_pending.return_value = [
        TradeReviewItem(
            symbol="AAPL",
            plan_json='{"symbol": "AAPL"}',
            rejection_reason="Score too low",
            id=1,
        ),
    ]
    review_queue_repo.expire_old.return_value = 0

    ctx = {
        "approval_handler": approval_handler,
        "review_queue_repo": review_queue_repo,
        "trade_plan_handler": MagicMock(),
    }
    return ctx


@pytest.fixture
def mock_ctx():
    ctx = _make_mock_ctx()
    with patch("cli.main._get_ctx", return_value=ctx):
        yield ctx


class TestApproveCreate:
    def test_create_with_valid_params(self, mock_ctx):
        result = runner.invoke(app, [
            "approval", "create",
            "--score", "60.0",
            "--regimes", "Bull,Sideways",
            "--max-pct", "8.0",
            "--budget", "50000",
            "--expires", "30",
        ])
        assert result.exit_code == 0
        assert "Approval Created" in result.output
        mock_ctx["approval_handler"].create.assert_called_once()


class TestApproveStatus:
    def test_status_shows_active_approval(self, mock_ctx):
        result = runner.invoke(app, ["approval", "status"])
        assert result.exit_code == 0
        assert "Strategy Approval" in result.output
        assert "60.0" in result.output  # score threshold
        assert "Bull" in result.output

    def test_status_shows_no_approval(self):
        ctx = _make_mock_ctx()
        ctx["approval_handler"].get_status.return_value = {
            "approval": None,
            "budget": None,
            "pending_review_count": 0,
        }
        with patch("cli.main._get_ctx", return_value=ctx):
            result = runner.invoke(app, ["approval", "status"])
            assert result.exit_code == 0
            assert "No active approval" in result.output


class TestApproveRevoke:
    def test_revoke(self, mock_ctx):
        result = runner.invoke(app, ["approval", "revoke"])
        assert result.exit_code == 0
        assert "revoked" in result.output.lower()
        mock_ctx["approval_handler"].revoke.assert_called_once()


class TestApproveResume:
    def test_resume(self, mock_ctx):
        result = runner.invoke(app, ["approval", "resume"])
        assert result.exit_code == 0
        assert "resumed" in result.output.lower()
        mock_ctx["approval_handler"].resume.assert_called_once()


class TestReviewList:
    def test_list_pending_items(self, mock_ctx):
        result = runner.invoke(app, ["review", "list"])
        assert result.exit_code == 0
        assert "AAPL" in result.output
        assert "Score too low" in result.output

    def test_list_no_pending(self):
        ctx = _make_mock_ctx()
        ctx["review_queue_repo"].list_pending.return_value = []
        with patch("cli.main._get_ctx", return_value=ctx):
            result = runner.invoke(app, ["review", "list"])
            assert result.exit_code == 0
            assert "No pending reviews" in result.output


class TestReviewReject:
    def test_reject_trade(self, mock_ctx):
        result = runner.invoke(app, ["review", "reject", "AAPL"])
        assert result.exit_code == 0
        assert "rejected" in result.output.lower()
        mock_ctx["review_queue_repo"].mark_reviewed.assert_called_once_with(1, approved=False)
