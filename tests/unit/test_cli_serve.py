"""Tests for CLI serve command (DASH-01).

Tests trade serve command that launches dashboard via uvicorn:
  - serve calls uvicorn.run with correct args
  - --host/--port override settings defaults
  - --no-browser suppresses webbrowser.open
  - browser opens by default via threading.Timer
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

import cli.main
from cli.main import app

runner = CliRunner()


def _mock_ctx() -> dict:
    """Return a minimal mock bootstrap context."""
    return {
        "bus": MagicMock(),
        "db_factory": MagicMock(),
        "score_handler": MagicMock(),
        "signal_handler": MagicMock(),
        "regime_handler": MagicMock(),
        "trade_plan_handler": MagicMock(),
        "portfolio_handler": MagicMock(),
        "capital": 100_000.0,
        "market": "us",
    }


class TestServeCommand:
    """Tests for the trade serve command."""

    @patch("cli.main.uvicorn")
    @patch("cli.main._get_ctx")
    def test_serve_calls_uvicorn_run(self, mock_get_ctx, mock_uvicorn) -> None:
        """serve command calls uvicorn.run with dashboard app, default host/port from settings."""
        mock_get_ctx.return_value = _mock_ctx()

        result = runner.invoke(app, ["serve", "--no-browser"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        mock_uvicorn.run.assert_called_once()
        call_kwargs = mock_uvicorn.run.call_args
        # Check host/port come from settings defaults
        assert call_kwargs.kwargs.get("host") == "0.0.0.0" or call_kwargs[1].get("host") == "0.0.0.0"
        assert call_kwargs.kwargs.get("port") == 8000 or call_kwargs[1].get("port") == 8000

    @patch("cli.main.uvicorn")
    @patch("cli.main._get_ctx")
    def test_serve_custom_host_port(self, mock_get_ctx, mock_uvicorn) -> None:
        """--host and --port options override settings defaults."""
        mock_get_ctx.return_value = _mock_ctx()

        result = runner.invoke(app, ["serve", "--host", "127.0.0.1", "--port", "9000", "--no-browser"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        mock_uvicorn.run.assert_called_once()
        call_kwargs = mock_uvicorn.run.call_args
        assert call_kwargs.kwargs.get("host") == "127.0.0.1" or call_kwargs[1].get("host") == "127.0.0.1"
        assert call_kwargs.kwargs.get("port") == 9000 or call_kwargs[1].get("port") == 9000

    @patch("cli.main.threading")
    @patch("cli.main.uvicorn")
    @patch("cli.main._get_ctx")
    def test_serve_no_browser_flag(self, mock_get_ctx, mock_uvicorn, mock_threading) -> None:
        """--no-browser flag prevents webbrowser.open call."""
        mock_get_ctx.return_value = _mock_ctx()

        result = runner.invoke(app, ["serve", "--no-browser"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        mock_threading.Timer.assert_not_called()

    @patch("cli.main.threading")
    @patch("cli.main.uvicorn")
    @patch("cli.main._get_ctx")
    def test_serve_opens_browser_by_default(self, mock_get_ctx, mock_uvicorn, mock_threading) -> None:
        """Without --no-browser, threading.Timer is used to schedule browser open."""
        mock_get_ctx.return_value = _mock_ctx()

        result = runner.invoke(app, ["serve"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        mock_threading.Timer.assert_called_once()
        # Timer should be started
        mock_threading.Timer.return_value.start.assert_called_once()
