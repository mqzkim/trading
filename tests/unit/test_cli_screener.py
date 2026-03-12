"""Tests for CLI screener command (INTF-02).

Tests screener rendering with mocked DuckDB signal store:
  - Screener renders top-N table with mock data
  - Screener shows empty message when no results
  - Screener JSON output mode
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from cli.main import app


runner = CliRunner()


_DUCKDB_CONNECT = "duckdb.connect"


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


class TestScreenerCommand:
    """Screener CLI command tests."""

    @patch(_SIGNAL_STORE)
    @patch(_DUCKDB_CONNECT)
    def test_screener_renders_table(self, mock_connect, mock_store_cls) -> None:
        """Screener renders a table with top-N results."""
        mock_store_inst = MagicMock()
        mock_store_inst.query_top_n.return_value = _mock_query_top_n_results()
        mock_store_cls.return_value = mock_store_inst

        result = runner.invoke(app, ["screener"])
        assert result.exit_code == 0
        assert "MSFT" in result.output
        assert "AAPL" in result.output

    @patch(_SIGNAL_STORE)
    @patch(_DUCKDB_CONNECT)
    def test_screener_no_results(self, mock_connect, mock_store_cls) -> None:
        """Screener shows empty message when no stocks match."""
        mock_store_inst = MagicMock()
        mock_store_inst.query_top_n.return_value = []
        mock_store_cls.return_value = mock_store_inst

        result = runner.invoke(app, ["screener"])
        assert result.exit_code == 0
        assert "No stocks match" in result.output

    @patch(_SIGNAL_STORE)
    @patch(_DUCKDB_CONNECT)
    def test_screener_json_output(self, mock_connect, mock_store_cls) -> None:
        """Screener --output json prints valid JSON."""
        import json

        mock_store_inst = MagicMock()
        mock_store_inst.query_top_n.return_value = _mock_query_top_n_results()
        mock_store_cls.return_value = mock_store_inst

        result = runner.invoke(app, ["screener", "--output", "json"])
        assert result.exit_code == 0
        # Should contain JSON array with results
        assert "MSFT" in result.output
        assert "AAPL" in result.output

    @patch(_SIGNAL_STORE)
    @patch(_DUCKDB_CONNECT)
    def test_screener_passes_options(self, mock_connect, mock_store_cls) -> None:
        """Screener passes --top-n, --min-score, --signal options correctly."""
        mock_store_inst = MagicMock()
        mock_store_inst.query_top_n.return_value = []
        mock_store_cls.return_value = mock_store_inst

        result = runner.invoke(app, [
            "screener", "--top-n", "5", "--min-score", "70", "--signal", "SELL"
        ])
        assert result.exit_code == 0
        mock_store_inst.query_top_n.assert_called_once_with(
            top_n=5, min_composite=70.0, signal_filter="SELL"
        )
