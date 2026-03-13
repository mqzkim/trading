"""CLI config and circuit breaker command tests."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


class TestConfigShow:
    def test_output_contains_settings(self):
        """config show displays EXECUTION_MODE and LIVE_CAPITAL_RATIO."""
        mock_settings = MagicMock()
        mock_settings.EXECUTION_MODE = "paper"
        mock_settings.US_CAPITAL = 100_000.0
        mock_settings.LIVE_CAPITAL_RATIO = 0.25
        mock_settings.ALPACA_PAPER_KEY = "fake"
        mock_settings.ALPACA_LIVE_KEY = None

        with patch("src.settings.Settings", return_value=mock_settings):
            result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        assert "EXECUTION_MODE" in result.output
        assert "LIVE_CAPITAL_RATIO" in result.output
        assert "paper" in result.output


class TestCircuitBreakerStatus:
    def test_shows_ok_when_not_tripped(self):
        """circuit-breaker status shows OK when not tripped."""
        mock_adapter = MagicMock()
        mock_adapter._circuit_tripped = False
        mock_adapter._consecutive_failures = 0
        mock_adapter._max_failures = 3

        mock_ctx = {"safe_adapter": mock_adapter}

        with patch("cli.main._get_ctx", return_value=mock_ctx):
            result = runner.invoke(app, ["circuit-breaker", "status"])

        assert result.exit_code == 0
        assert "OK" in result.output

    def test_shows_tripped_when_tripped(self):
        """circuit-breaker status shows TRIPPED when tripped."""
        mock_adapter = MagicMock()
        mock_adapter._circuit_tripped = True
        mock_adapter._consecutive_failures = 3
        mock_adapter._max_failures = 3

        mock_ctx = {"safe_adapter": mock_adapter}

        with patch("cli.main._get_ctx", return_value=mock_ctx):
            result = runner.invoke(app, ["circuit-breaker", "status"])

        assert result.exit_code == 0
        assert "TRIPPED" in result.output


class TestCircuitBreakerReset:
    def test_resets_circuit_breaker(self):
        """circuit-breaker reset calls reset_circuit_breaker()."""
        mock_adapter = MagicMock()
        mock_ctx = {"safe_adapter": mock_adapter}

        with patch("cli.main._get_ctx", return_value=mock_ctx):
            result = runner.invoke(app, ["circuit-breaker", "reset"])

        assert result.exit_code == 0
        mock_adapter.reset_circuit_breaker.assert_called_once()
        assert "reset successfully" in result.output
