"""Unit tests for CLI generate-plan command."""
import pytest
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


class TestGeneratePlanCommand:
    """Tests for the 'trading generate-plan' CLI command."""

    def test_generate_plan_displays_plan(self):
        """'trading generate-plan AAPL' displays plan details."""
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
        _setup_ctx(handler=mock_handler)
        try:
            result = runner.invoke(app, ["generate-plan", "AAPL"])
            assert result.exit_code == 0
            assert "AAPL" in result.output
            assert "150" in result.output
        finally:
            _teardown_ctx()

    def test_generate_plan_rejected(self):
        """Rejected plan shows rejection message."""
        mock_handler = MagicMock()
        mock_handler.generate.return_value = None
        _setup_ctx(handler=mock_handler)
        try:
            result = runner.invoke(app, ["generate-plan", "AAPL"])
            assert result.exit_code == 0
            assert "reject" in result.output.lower() or "denied" in result.output.lower()
        finally:
            _teardown_ctx()
