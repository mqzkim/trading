"""Tests for CLI approve, execute, and monitor commands."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

import cli.main
from cli.main import app

runner = CliRunner()

# Watchlist repo still imported inline in CLI (not via bootstrap)
_WL_REPO = "src.portfolio.infrastructure.sqlite_watchlist_repo.SqliteWatchlistRepository"


def _mock_plan_dict(**overrides) -> dict:
    """Return a mock trade plan dict from repository."""
    defaults = dict(
        symbol="AAPL",
        direction="BUY",
        entry_price=150.0,
        stop_loss_price=140.0,
        take_profit_price=170.0,
        quantity=10,
        position_value=1500.0,
        reasoning_trace="Strong fundamentals",
        composite_score=75.0,
        margin_of_safety=0.15,
        signal_direction="BUY",
        status="PENDING",
    )
    defaults.update(overrides)
    return defaults


def _setup_bootstrap_ctx(handler=None, portfolio_handler=None):
    """Create a mock bootstrap context dict and inject it into cli.main._ctx_cache."""
    ctx = {
        "trade_plan_handler": handler or MagicMock(),
        "portfolio_handler": portfolio_handler or MagicMock(),
        "bus": MagicMock(),
        "db_factory": MagicMock(),
        "score_handler": MagicMock(),
        "signal_handler": MagicMock(),
        "regime_handler": MagicMock(),
        "capital": 100_000.0,
        "market": "us",
    }
    cli.main._ctx_cache["us"] = ctx
    return ctx


def _teardown_ctx():
    """Reset cli.main._ctx_cache after test."""
    cli.main._ctx_cache.clear()


class TestApproveCommand:
    """Test CLI approve command."""

    def test_approve_no_pending_plan(self):
        """approve AAPL with no pending plan shows error."""
        mock_handler = MagicMock()
        mock_handler._repo.find_by_symbol.return_value = None
        _setup_bootstrap_ctx(handler=mock_handler)
        try:
            result = runner.invoke(app, ["approve", "AAPL"])
            assert result.exit_code != 0 or "No pending plan" in result.output
        finally:
            _teardown_ctx()

    def test_approve_displays_plan_and_rejects(self):
        """approve AAPL with 'n' input rejects the plan."""
        mock_handler = MagicMock()
        mock_handler._repo.find_by_symbol.return_value = _mock_plan_dict()
        mock_handler.approve.return_value = {"status": "REJECTED", "symbol": "AAPL"}
        _setup_bootstrap_ctx(handler=mock_handler)
        try:
            result = runner.invoke(app, ["approve", "AAPL"], input="n\n")
            assert result.exit_code == 0
            assert "AAPL" in result.output
            assert "150" in result.output  # entry price displayed
            assert "rejected" in result.output.lower()
        finally:
            _teardown_ctx()

    def test_approve_and_execute_mock(self):
        """approve AAPL with 'y' then 'n' (no modify) submits order."""
        from src.execution.domain.value_objects import OrderResult

        mock_handler = MagicMock()
        mock_handler._repo.find_by_symbol.return_value = _mock_plan_dict()
        mock_handler.approve.return_value = {"status": "APPROVED", "symbol": "AAPL"}
        mock_handler.execute.return_value = OrderResult(
            order_id="MOCK-AAPL-abc123",
            status="filled",
            symbol="AAPL",
            quantity=10,
            filled_price=150.0,
        )
        _setup_bootstrap_ctx(handler=mock_handler)
        try:
            result = runner.invoke(app, ["approve", "AAPL"], input="y\nn\n")
            assert result.exit_code == 0
            assert "Order submitted" in result.output or "MOCK-AAPL" in result.output
        finally:
            _teardown_ctx()


class TestExecuteCommand:
    """Test CLI execute command."""

    def test_execute_not_approved(self):
        """execute AAPL --force with non-approved plan shows error."""
        mock_handler = MagicMock()
        mock_handler._repo.find_by_symbol.return_value = _mock_plan_dict(status="PENDING")
        _setup_bootstrap_ctx(handler=mock_handler)
        try:
            result = runner.invoke(app, ["execute", "AAPL", "--force"])
            assert result.exit_code != 0 or "not approved" in result.output.lower()
        finally:
            _teardown_ctx()

    def test_execute_approved_plan(self):
        """execute AAPL --force with approved plan submits order."""
        from src.execution.domain.value_objects import OrderResult

        mock_handler = MagicMock()
        mock_handler._repo.find_by_symbol.return_value = _mock_plan_dict(status="APPROVED")
        mock_handler.execute.return_value = OrderResult(
            order_id="MOCK-AAPL-xyz789",
            status="filled",
            symbol="AAPL",
            quantity=10,
            filled_price=150.0,
        )
        _setup_bootstrap_ctx(handler=mock_handler)
        try:
            result = runner.invoke(app, ["execute", "AAPL", "--force"])
            assert result.exit_code == 0
            assert "Order submitted" in result.output
        finally:
            _teardown_ctx()


class TestMonitorCommand:
    """Test CLI monitor command."""

    @patch(_WL_REPO)
    def test_monitor_no_positions(self, mock_wl_cls):
        """monitor with empty repos shows 0 positions summary."""
        mock_portfolio_handler = MagicMock()
        mock_portfolio_handler._position_repo.find_all_open.return_value = []
        mock_portfolio_handler._portfolio_repo.find_by_id.return_value = None

        mock_wl = MagicMock()
        mock_wl.find_all.return_value = []
        mock_wl_cls.return_value = mock_wl

        _setup_bootstrap_ctx(portfolio_handler=mock_portfolio_handler)
        try:
            result = runner.invoke(app, ["monitor"])
            assert result.exit_code == 0
            assert "0" in result.output  # 0 positions
            assert "Monitoring Summary" in result.output or "monitored" in result.output
        finally:
            _teardown_ctx()

    @patch(_WL_REPO)
    def test_monitor_with_drawdown_alert(self, mock_wl_cls):
        """monitor with drawdown shows alert."""
        from src.portfolio.domain.aggregates import Portfolio

        mock_portfolio_handler = MagicMock()
        mock_portfolio_handler._position_repo.find_all_open.return_value = []

        # Create a portfolio with drawdown
        portfolio = Portfolio(portfolio_id="default", initial_value=100000.0)
        portfolio.peak_value = 120000.0  # peak was 120k, now 100k = 16.7% dd (WARNING)

        mock_portfolio_handler._portfolio_repo.find_by_id.return_value = portfolio

        mock_wl = MagicMock()
        mock_wl.find_all.return_value = []
        mock_wl_cls.return_value = mock_wl

        _setup_bootstrap_ctx(portfolio_handler=mock_portfolio_handler)
        try:
            result = runner.invoke(app, ["monitor"])
            assert result.exit_code == 0
            assert "DRAWDOWN ALERT" in result.output or "WARNING" in result.output
        finally:
            _teardown_ctx()
