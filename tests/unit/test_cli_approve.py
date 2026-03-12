"""Tests for CLI approve, execute, and monitor commands."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()

# Patch paths matching lazy imports inside CLI function bodies
_TRADE_PLAN_REPO = "src.execution.infrastructure.sqlite_trade_plan_repo.SqliteTradePlanRepository"
_TRADE_PLAN_SERVICE = "src.execution.domain.services.TradePlanService"
_ALPACA_ADAPTER = "src.execution.infrastructure.alpaca_adapter.AlpacaExecutionAdapter"
_TRADE_PLAN_HANDLER = "src.execution.application.handlers.TradePlanHandler"
_POS_REPO = "src.portfolio.infrastructure.sqlite_position_repo.SqlitePositionRepository"
_PORT_REPO = "src.portfolio.infrastructure.sqlite_portfolio_repo.SqlitePortfolioRepository"
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


class TestApproveCommand:
    """Test CLI approve command."""

    @patch(_TRADE_PLAN_REPO)
    def test_approve_no_pending_plan(self, mock_repo_cls):
        """approve AAPL with empty repo shows error."""
        mock_repo = MagicMock()
        mock_repo.find_by_symbol.return_value = None
        mock_repo_cls.return_value = mock_repo

        result = runner.invoke(app, ["approve", "AAPL"])

        assert result.exit_code != 0 or "No pending plan" in result.output

    @patch(_ALPACA_ADAPTER)
    @patch(_TRADE_PLAN_SERVICE)
    @patch(_TRADE_PLAN_HANDLER)
    @patch(_TRADE_PLAN_REPO)
    def test_approve_displays_plan_and_rejects(
        self, mock_repo_cls, mock_handler_cls, mock_service_cls, mock_adapter_cls
    ):
        """approve AAPL with 'n' input rejects the plan."""
        mock_repo = MagicMock()
        mock_repo.find_by_symbol.return_value = _mock_plan_dict()
        mock_repo_cls.return_value = mock_repo

        mock_handler = MagicMock()
        mock_handler.approve.return_value = {"status": "REJECTED", "symbol": "AAPL"}
        mock_handler_cls.return_value = mock_handler

        result = runner.invoke(app, ["approve", "AAPL"], input="n\n")

        assert result.exit_code == 0
        assert "AAPL" in result.output
        assert "150" in result.output  # entry price displayed
        assert "rejected" in result.output.lower()

    @patch(_ALPACA_ADAPTER)
    @patch(_TRADE_PLAN_SERVICE)
    @patch(_TRADE_PLAN_HANDLER)
    @patch(_TRADE_PLAN_REPO)
    def test_approve_and_execute_mock(
        self, mock_repo_cls, mock_handler_cls, mock_service_cls, mock_adapter_cls
    ):
        """approve AAPL with 'y' then 'n' (no modify) submits order."""
        from src.execution.domain.value_objects import OrderResult

        mock_repo = MagicMock()
        mock_repo.find_by_symbol.return_value = _mock_plan_dict()
        mock_repo_cls.return_value = mock_repo

        mock_handler = MagicMock()
        mock_handler.approve.return_value = {"status": "APPROVED", "symbol": "AAPL"}
        mock_handler.execute.return_value = OrderResult(
            order_id="MOCK-AAPL-abc123",
            status="filled",
            symbol="AAPL",
            quantity=10,
            filled_price=150.0,
        )
        mock_handler_cls.return_value = mock_handler

        result = runner.invoke(app, ["approve", "AAPL"], input="y\nn\n")

        assert result.exit_code == 0
        assert "Order submitted" in result.output or "MOCK-AAPL" in result.output


class TestExecuteCommand:
    """Test CLI execute command."""

    @patch(_TRADE_PLAN_REPO)
    def test_execute_not_approved(self, mock_repo_cls):
        """execute AAPL --force with non-approved plan shows error."""
        mock_repo = MagicMock()
        mock_repo.find_by_symbol.return_value = _mock_plan_dict(status="PENDING")
        mock_repo_cls.return_value = mock_repo

        result = runner.invoke(app, ["execute", "AAPL", "--force"])

        assert result.exit_code != 0 or "not approved" in result.output.lower()

    @patch(_ALPACA_ADAPTER)
    @patch(_TRADE_PLAN_SERVICE)
    @patch(_TRADE_PLAN_HANDLER)
    @patch(_TRADE_PLAN_REPO)
    def test_execute_approved_plan(
        self, mock_repo_cls, mock_handler_cls, mock_service_cls, mock_adapter_cls
    ):
        """execute AAPL --force with approved plan submits order."""
        from src.execution.domain.value_objects import OrderResult

        mock_repo = MagicMock()
        mock_repo.find_by_symbol.return_value = _mock_plan_dict(status="APPROVED")
        mock_repo_cls.return_value = mock_repo

        mock_handler = MagicMock()
        mock_handler.execute.return_value = OrderResult(
            order_id="MOCK-AAPL-xyz789",
            status="filled",
            symbol="AAPL",
            quantity=10,
            filled_price=150.0,
        )
        mock_handler_cls.return_value = mock_handler

        result = runner.invoke(app, ["execute", "AAPL", "--force"])

        assert result.exit_code == 0
        assert "Order submitted" in result.output


class TestMonitorCommand:
    """Test CLI monitor command."""

    @patch(_WL_REPO)
    @patch(_PORT_REPO)
    @patch(_POS_REPO)
    def test_monitor_no_positions(self, mock_pos_cls, mock_port_cls, mock_wl_cls):
        """monitor with empty repos shows 0 positions summary."""
        mock_pos = MagicMock()
        mock_pos.find_all_open.return_value = []
        mock_pos_cls.return_value = mock_pos

        mock_port = MagicMock()
        mock_port.find_by_id.return_value = None
        mock_port_cls.return_value = mock_port

        mock_wl = MagicMock()
        mock_wl.find_all.return_value = []
        mock_wl_cls.return_value = mock_wl

        result = runner.invoke(app, ["monitor"])

        assert result.exit_code == 0
        assert "0" in result.output  # 0 positions
        assert "Monitoring Summary" in result.output or "monitored" in result.output

    @patch(_WL_REPO)
    @patch(_PORT_REPO)
    @patch(_POS_REPO)
    def test_monitor_with_drawdown_alert(self, mock_pos_cls, mock_port_cls, mock_wl_cls):
        """monitor with drawdown shows alert."""
        from src.portfolio.domain.aggregates import Portfolio

        mock_pos = MagicMock()
        mock_pos.find_all_open.return_value = []
        mock_pos_cls.return_value = mock_pos

        # Create a portfolio with drawdown
        portfolio = Portfolio(portfolio_id="default", initial_value=100000.0)
        portfolio.peak_value = 120000.0  # peak was 120k, now 100k = 16.7% dd (WARNING)

        mock_port = MagicMock()
        mock_port.find_by_id.return_value = portfolio
        mock_port_cls.return_value = mock_port

        mock_wl = MagicMock()
        mock_wl.find_all.return_value = []
        mock_wl_cls.return_value = mock_wl

        result = runner.invoke(app, ["monitor"])

        assert result.exit_code == 0
        assert "DRAWDOWN ALERT" in result.output or "WARNING" in result.output
