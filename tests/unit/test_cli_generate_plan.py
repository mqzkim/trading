"""Unit tests for CLI generate-plan command."""
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

import cli.main
from cli.main import app

runner = CliRunner()


def _setup_ctx(handler=None):
    """Inject mock bootstrap context into cli.main._ctx_cache."""
    ctx = {
        "trade_plan_handler": handler or MagicMock(),
        "portfolio_handler": MagicMock(),
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
    cli.main._ctx_cache.clear()


def _mock_data_client():
    """Create a mock DataClient that returns realistic data."""
    mock_client = MagicMock()
    mock_client.get_full.return_value = {
        "price": {"open": 149.0, "high": 151.0, "low": 148.0, "close": 150.0, "volume": 1_000_000},
        "indicators": {"atr21": 3.5, "rsi14": 55.0, "ma50": 148.0, "ma200": 140.0},
        "fundamentals": {},
    }
    return mock_client


def _mock_score_result(composite=72.5, margin=0.15):
    """Create a mock Result for score_handler.handle()."""
    result = MagicMock()
    result.is_ok.return_value = True
    result.unwrap.return_value = {"composite_score": composite, "margin_of_safety": margin}
    return result


def _mock_signal_result(direction="BUY"):
    """Create a mock Result for signal_handler.handle()."""
    result = MagicMock()
    result.is_ok.return_value = True
    result.unwrap.return_value = {"direction": direction, "reasoning_trace": "Test reasoning"}
    return result


class TestGeneratePlanCommand:
    """Tests for the 'trading generate-plan' CLI command."""

    @patch("core.data.client.DataClient")
    def test_generate_plan_displays_plan(self, mock_dc_cls):
        """'trading generate-plan AAPL' displays plan details."""
        mock_dc_cls.return_value = _mock_data_client()

        mock_plan = MagicMock()
        mock_plan.symbol = "AAPL"
        mock_plan.direction = "BUY"
        mock_plan.entry_price = 150.0
        mock_plan.stop_loss_price = 139.5
        mock_plan.take_profit_price = 165.0
        mock_plan.quantity = 22
        mock_plan.position_value = 3300.0
        mock_plan.reasoning_trace = "Strong fundamentals"
        mock_plan.composite_score = 72.5
        mock_plan.margin_of_safety = 0.15

        mock_handler = MagicMock()
        mock_handler.generate.return_value = mock_plan
        ctx = _setup_ctx(handler=mock_handler)
        ctx["score_handler"].handle.return_value = _mock_score_result()
        ctx["signal_handler"].handle.return_value = _mock_signal_result()
        try:
            result = runner.invoke(app, ["generate-plan", "AAPL"])
            assert result.exit_code == 0
            assert "AAPL" in result.output
            assert "150" in result.output
        finally:
            _teardown_ctx()

    @patch("core.data.client.DataClient")
    def test_generate_plan_rejected(self, mock_dc_cls):
        """Rejected plan shows rejection message."""
        mock_dc_cls.return_value = _mock_data_client()

        mock_handler = MagicMock()
        mock_handler.generate.return_value = None
        ctx = _setup_ctx(handler=mock_handler)
        ctx["score_handler"].handle.return_value = _mock_score_result()
        ctx["signal_handler"].handle.return_value = _mock_signal_result()
        try:
            result = runner.invoke(app, ["generate-plan", "AAPL"])
            assert result.exit_code == 0
            assert "reject" in result.output.lower() or "denied" in result.output.lower()
        finally:
            _teardown_ctx()
