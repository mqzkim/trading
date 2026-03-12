"""Unit tests for CLI generate-plan command."""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()

# Patch at source module since cli/main.py uses lazy import inside function body
_BOOTSTRAP = "src.bootstrap.bootstrap"


class TestGeneratePlanCommand:
    """Tests for the 'trading generate-plan' CLI command."""

    @patch(_BOOTSTRAP)
    def test_generate_plan_displays_plan(self, mock_bootstrap):
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
        mock_bootstrap.return_value = {
            "trade_plan_handler": mock_handler,
            "bus": MagicMock(),
        }

        result = runner.invoke(app, ["generate-plan", "AAPL"])
        assert result.exit_code == 0
        assert "AAPL" in result.output
        assert "150" in result.output

    @patch(_BOOTSTRAP)
    def test_generate_plan_rejected(self, mock_bootstrap):
        """Rejected plan shows rejection message."""
        mock_handler = MagicMock()
        mock_handler.generate.return_value = None
        mock_bootstrap.return_value = {
            "trade_plan_handler": mock_handler,
            "bus": MagicMock(),
        }

        result = runner.invoke(app, ["generate-plan", "AAPL"])
        assert result.exit_code == 0
        assert "reject" in result.output.lower() or "denied" in result.output.lower()
