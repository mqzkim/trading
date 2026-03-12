"""Integration tests for DuckDB screener (query_top_n).

Creates a temporary DuckDB database, populates scores/signals/valuation_results
tables, and verifies query_top_n returns correctly joined results.
"""
from __future__ import annotations

import duckdb
import pytest

from src.signals.infrastructure.duckdb_signal_store import DuckDBSignalStore


@pytest.fixture
def duckdb_conn():
    """Create an in-memory DuckDB connection with test data."""
    conn = duckdb.connect(":memory:")

    # Create valuation_results table (as created by DuckDBValuationStore)
    conn.execute("""
        CREATE TABLE valuation_results (
            ticker VARCHAR PRIMARY KEY,
            intrinsic_value DOUBLE,
            margin_of_safety DOUBLE,
            has_margin BOOLEAN
        )
    """)
    conn.execute("""
        INSERT INTO valuation_results VALUES
            ('AAPL', 200.0, 0.25, true),
            ('MSFT', 400.0, 0.15, true),
            ('TSLA', 150.0, -0.10, false)
    """)

    yield conn
    conn.close()


class TestScreenerQueryTopN:
    """Test query_top_n returns scored results when scores and signals exist."""

    def test_returns_results_with_correct_joins(self, duckdb_conn) -> None:
        store = DuckDBSignalStore(duckdb_conn)

        # Populate scores via sync_scores
        store.sync_scores([
            {"symbol": "AAPL", "composite_score": 85.0, "risk_adjusted_score": 80.0, "strategy": "swing"},
            {"symbol": "MSFT", "composite_score": 78.0, "risk_adjusted_score": 75.0, "strategy": "swing"},
            {"symbol": "TSLA", "composite_score": 65.0, "risk_adjusted_score": 62.0, "strategy": "swing"},
        ])

        # Save signals
        store.save("AAPL", "BUY", 0.9, {"source": "test"})
        store.save("MSFT", "BUY", 0.7, {"source": "test"})
        store.save("TSLA", "SELL", 0.6, {"source": "test"})

        results = store.query_top_n(top_n=10, min_composite=60.0, signal_filter="BUY")

        assert len(results) == 2
        # Ordered by risk_adjusted_score DESC
        assert results[0]["symbol"] == "AAPL"
        assert results[1]["symbol"] == "MSFT"

        # Verify valuation data joined correctly (from valuation_results, not valuations)
        assert results[0]["intrinsic_value"] == 200.0
        assert results[0]["margin_of_safety"] == 0.25
        assert results[0]["has_margin"] is True

        assert results[1]["intrinsic_value"] == 400.0

    def test_returns_results_without_signal_filter(self, duckdb_conn) -> None:
        store = DuckDBSignalStore(duckdb_conn)

        store.sync_scores([
            {"symbol": "AAPL", "composite_score": 85.0, "risk_adjusted_score": 80.0, "strategy": "swing"},
            {"symbol": "TSLA", "composite_score": 65.0, "risk_adjusted_score": 62.0, "strategy": "swing"},
        ])

        store.save("AAPL", "BUY", 0.9, {})
        store.save("TSLA", "SELL", 0.6, {})

        results = store.query_top_n(top_n=10, min_composite=60.0, signal_filter=None)

        assert len(results) == 2
        # Both returned regardless of direction
        symbols = {r["symbol"] for r in results}
        assert symbols == {"AAPL", "TSLA"}

    def test_min_composite_filter(self, duckdb_conn) -> None:
        store = DuckDBSignalStore(duckdb_conn)

        store.sync_scores([
            {"symbol": "AAPL", "composite_score": 85.0, "risk_adjusted_score": 80.0, "strategy": "swing"},
            {"symbol": "TSLA", "composite_score": 55.0, "risk_adjusted_score": 50.0, "strategy": "swing"},
        ])

        store.save("AAPL", "BUY", 0.9, {})
        store.save("TSLA", "BUY", 0.6, {})

        results = store.query_top_n(top_n=10, min_composite=60.0, signal_filter="BUY")

        assert len(results) == 1
        assert results[0]["symbol"] == "AAPL"

    def test_top_n_limit(self, duckdb_conn) -> None:
        store = DuckDBSignalStore(duckdb_conn)

        store.sync_scores([
            {"symbol": "AAPL", "composite_score": 85.0, "risk_adjusted_score": 80.0, "strategy": "swing"},
            {"symbol": "MSFT", "composite_score": 78.0, "risk_adjusted_score": 75.0, "strategy": "swing"},
        ])

        store.save("AAPL", "BUY", 0.9, {})
        store.save("MSFT", "BUY", 0.7, {})

        results = store.query_top_n(top_n=1, min_composite=60.0, signal_filter="BUY")

        assert len(results) == 1
        assert results[0]["symbol"] == "AAPL"

    def test_scores_table_created_automatically(self, duckdb_conn) -> None:
        """scores table should exist after DuckDBSignalStore init."""
        store = DuckDBSignalStore(duckdb_conn)
        # Table should exist even without sync_scores
        tables = duckdb_conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'scores'"
        ).fetchall()
        assert len(tables) == 1, "scores table should be created in __init__"
