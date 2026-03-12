"""Tests for CLI screener command (INTF-02).

Tests screener rendering with mocked bootstrap context and DuckDB signal store:
  - Screener renders top-N table with mock data
  - Screener shows empty message when no results
  - Screener JSON output mode
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

import cli.main
from cli.main import app


runner = CliRunner()


def _mock_query_top_n_results() -> list[dict]:
    """Mock results from query_top_n."""
    return [
        {
            "symbol": "MSFT",
            "composite_score": 90.0,
            "risk_adjusted_score": 88.0,
            "intrinsic_value": 450.0,
            "margin_of_safety": 0.20,
            "has_margin": True,
            "direction": "BUY",
            "strength": 88.0,
        },
        {
            "symbol": "AAPL",
            "composite_score": 85.0,
            "risk_adjusted_score": 82.0,
            "intrinsic_value": 200.0,
            "margin_of_safety": 0.15,
            "has_margin": True,
            "direction": "BUY",
            "strength": 82.0,
        },
    ]


_SIGNAL_STORE = "src.signals.infrastructure.duckdb_signal_store.DuckDBSignalStore"


def _setup_bootstrap_ctx():
    """Create a mock bootstrap context with db_factory and inject into cli.main._ctx."""
    mock_db_factory = MagicMock()
    mock_db_factory.duckdb_conn.return_value = MagicMock()

    ctx = {
        "trade_plan_handler": MagicMock(),
        "portfolio_handler": MagicMock(),
        "bus": MagicMock(),
        "db_factory": mock_db_factory,
        "score_handler": MagicMock(),
        "signal_handler": MagicMock(),
        "regime_handler": MagicMock(),
    }
    cli.main._ctx = ctx
    return ctx


def _teardown_ctx():
    """Reset cli.main._ctx to None after test."""
    cli.main._ctx = None


class TestScreenerCommand:
    """Screener CLI command tests."""

    @patch(_SIGNAL_STORE)
    def test_screener_renders_table(self, mock_store_cls) -> None:
        """Screener renders a table with top-N results."""
        mock_store_inst = MagicMock()
        mock_store_inst.query_top_n.return_value = _mock_query_top_n_results()
        mock_store_cls.return_value = mock_store_inst

        _setup_bootstrap_ctx()
        try:
            result = runner.invoke(app, ["screener"])
            assert result.exit_code == 0
            assert "MSFT" in result.output
            assert "AAPL" in result.output
        finally:
            _teardown_ctx()

    @patch(_SIGNAL_STORE)
    def test_screener_no_results(self, mock_store_cls) -> None:
        """Screener shows empty message when no stocks match."""
        mock_store_inst = MagicMock()
        mock_store_inst.query_top_n.return_value = []
        mock_store_cls.return_value = mock_store_inst

        _setup_bootstrap_ctx()
        try:
            result = runner.invoke(app, ["screener"])
            assert result.exit_code == 0
            assert "No stocks match" in result.output
        finally:
            _teardown_ctx()

    @patch(_SIGNAL_STORE)
    def test_screener_json_output(self, mock_store_cls) -> None:
        """Screener --output json prints valid JSON."""
        mock_store_inst = MagicMock()
        mock_store_inst.query_top_n.return_value = _mock_query_top_n_results()
        mock_store_cls.return_value = mock_store_inst

        _setup_bootstrap_ctx()
        try:
            result = runner.invoke(app, ["screener", "--output", "json"])
            assert result.exit_code == 0
            assert "MSFT" in result.output
            assert "AAPL" in result.output
        finally:
            _teardown_ctx()

    @patch(_SIGNAL_STORE)
    def test_screener_passes_options(self, mock_store_cls) -> None:
        """Screener passes --top-n, --min-score, --signal options correctly."""
        mock_store_inst = MagicMock()
        mock_store_inst.query_top_n.return_value = []
        mock_store_cls.return_value = mock_store_inst

        _setup_bootstrap_ctx()
        try:
            result = runner.invoke(app, [
                "screener", "--top-n", "5", "--min-score", "70", "--signal", "SELL"
            ])
            assert result.exit_code == 0
            mock_store_inst.query_top_n.assert_called_once_with(
                top_n=5, min_composite=70.0, signal_filter="SELL"
            )
        finally:
            _teardown_ctx()
