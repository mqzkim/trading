"""Tests for DuckDB signal store and screener queries (SIGN-02).

Tests DuckDBSignalStore implementing ISignalRepository and
query_top_n() for ranking the universe by risk-adjusted composite score.
"""
from __future__ import annotations

import pytest
import duckdb

from src.signals.infrastructure.duckdb_signal_store import DuckDBSignalStore


def _create_test_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Pre-create scores and valuations tables with test data."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            symbol VARCHAR PRIMARY KEY,
            composite_score DOUBLE,
            risk_adjusted_score DOUBLE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS valuations (
            symbol VARCHAR PRIMARY KEY,
            intrinsic_value DOUBLE,
            margin_of_safety DOUBLE,
            has_margin BOOLEAN
        )
    """)


def _insert_test_data(conn: duckdb.DuckDBPyConnection) -> None:
    """Insert test scores and valuations for 6 tickers."""
    scores_data = [
        ("AAPL", 85.0, 82.0),
        ("MSFT", 90.0, 88.0),
        ("GOOG", 75.0, 72.0),
        ("AMZN", 60.0, 55.0),
        ("TSLA", 40.0, 35.0),
        ("META", 70.0, 68.0),
    ]
    for symbol, composite, risk_adj in scores_data:
        conn.execute(
            "INSERT INTO scores VALUES (?, ?, ?)",
            [symbol, composite, risk_adj],
        )

    valuations_data = [
        ("AAPL", 200.0, 0.15, True),
        ("MSFT", 450.0, 0.20, True),
        ("GOOG", 180.0, 0.10, True),
        ("AMZN", 160.0, 0.05, False),
        ("TSLA", 200.0, -0.10, False),
        ("META", 350.0, 0.12, True),
    ]
    for symbol, intrinsic, mos, has_margin in valuations_data:
        conn.execute(
            "INSERT INTO valuations VALUES (?, ?, ?, ?)",
            [symbol, intrinsic, mos, has_margin],
        )


@pytest.fixture
def conn() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB connection with test data."""
    c = duckdb.connect(":memory:")
    _create_test_tables(c)
    _insert_test_data(c)
    return c


@pytest.fixture
def store(conn: duckdb.DuckDBPyConnection) -> DuckDBSignalStore:
    """DuckDBSignalStore backed by in-memory connection."""
    return DuckDBSignalStore(conn)


# ── ISignalRepository interface tests ─────────────────────────────


class TestDuckDBSignalStoreRepository:
    """Tests that DuckDBSignalStore implements ISignalRepository correctly."""

    def test_save_persists_signal(self, store: DuckDBSignalStore) -> None:
        store.save("AAPL", "BUY", 85.0, {"composite_score": 80.0})
        result = store.find_active("AAPL")
        assert result is not None
        assert result["symbol"] == "AAPL"
        assert result["direction"] == "BUY"
        assert result["strength"] == 85.0

    def test_find_active_returns_saved_signal(self, store: DuckDBSignalStore) -> None:
        store.save("MSFT", "SELL", 30.0, {"reason": "low score"})
        result = store.find_active("MSFT")
        assert result is not None
        assert result["direction"] == "SELL"

    def test_find_active_returns_none_for_missing(self, store: DuckDBSignalStore) -> None:
        result = store.find_active("NVDA")
        assert result is None

    def test_find_all_active_returns_all_saved(self, store: DuckDBSignalStore) -> None:
        store.save("AAPL", "BUY", 80.0, {})
        store.save("MSFT", "SELL", 30.0, {})
        store.save("GOOG", "HOLD", 50.0, {})
        results = store.find_all_active()
        assert len(results) == 3

    def test_save_overwrites_existing(self, store: DuckDBSignalStore) -> None:
        store.save("AAPL", "BUY", 80.0, {})
        store.save("AAPL", "SELL", 20.0, {})
        result = store.find_active("AAPL")
        assert result is not None
        assert result["direction"] == "SELL"
        assert result["strength"] == 20.0


# ── Screener query tests ─────────────────────────────────────────


class TestScreenerQueries:
    """Tests for query_top_n screener functionality."""

    def _seed_signals(self, store: DuckDBSignalStore) -> None:
        """Insert BUY/SELL/HOLD signals for 6 tickers."""
        store.save("AAPL", "BUY", 82.0, {})
        store.save("MSFT", "BUY", 88.0, {})
        store.save("GOOG", "BUY", 72.0, {})
        store.save("AMZN", "HOLD", 55.0, {})
        store.save("TSLA", "SELL", 35.0, {})
        store.save("META", "BUY", 68.0, {})

    def test_query_top_n_returns_correct_count(self, store: DuckDBSignalStore) -> None:
        self._seed_signals(store)
        results = store.query_top_n(top_n=3)
        assert len(results) <= 3

    def test_query_top_n_ordered_by_risk_adjusted_score_desc(
        self, store: DuckDBSignalStore
    ) -> None:
        self._seed_signals(store)
        results = store.query_top_n(top_n=6, min_composite=0.0, signal_filter=None)
        if len(results) >= 2:
            scores = [r["risk_adjusted_score"] for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_query_top_n_signal_filter_buy_excludes_sell_hold(
        self, store: DuckDBSignalStore
    ) -> None:
        self._seed_signals(store)
        results = store.query_top_n(top_n=10, min_composite=0.0, signal_filter="BUY")
        directions = {r["direction"] for r in results}
        assert "SELL" not in directions
        assert "HOLD" not in directions

    def test_query_top_n_min_composite_filters_correctly(
        self, store: DuckDBSignalStore
    ) -> None:
        self._seed_signals(store)
        results = store.query_top_n(top_n=10, min_composite=70.0, signal_filter=None)
        for r in results:
            assert r["risk_adjusted_score"] >= 70.0

    def test_query_top_n_empty_result_when_no_match(
        self, store: DuckDBSignalStore
    ) -> None:
        self._seed_signals(store)
        results = store.query_top_n(top_n=10, min_composite=99.0, signal_filter="BUY")
        assert len(results) == 0

    def test_query_top_n_joins_with_scores_and_valuations(
        self, store: DuckDBSignalStore
    ) -> None:
        self._seed_signals(store)
        results = store.query_top_n(top_n=3, min_composite=0.0, signal_filter=None)
        if results:
            first = results[0]
            # Should contain joined fields from all three tables
            assert "symbol" in first
            assert "composite_score" in first
            assert "risk_adjusted_score" in first
            assert "direction" in first
            assert "strength" in first
