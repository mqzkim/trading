"""Tests for scoring store unification: SQLite sub-score persistence and DuckDB sync.

Verifies:
1. SqliteScoreRepository.save() persists sub-scores (fundamental, technical, sentiment, f/z/m)
2. SqliteScoreRepository.find_all_latest_for_sync() returns sync-format dicts
3. DuckDB scores table gets consistent data via event-driven sync
4. DuckDBSignalStore.sync_scores() uses upsert semantics (no bulk delete)
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from typing import Optional

import duckdb
import pytest

from src.scoring.domain.value_objects import CompositeScore
from src.scoring.infrastructure.sqlite_repo import SqliteScoreRepository
from src.signals.infrastructure.duckdb_signal_store import DuckDBSignalStore


@pytest.fixture
def tmp_sqlite_repo(tmp_path):
    """Create SqliteScoreRepository with temp DB."""
    db_path = str(tmp_path / "scoring.db")
    return SqliteScoreRepository(db_path=db_path)


@pytest.fixture
def tmp_duckdb_store(tmp_path):
    """Create DuckDBSignalStore with temp DB."""
    db_path = str(tmp_path / "analytics.duckdb")
    conn = duckdb.connect(db_path)
    return DuckDBSignalStore(conn)


class TestSubScorePersistence:
    """SqliteScoreRepository should persist sub-scores when provided."""

    def test_save_persists_sub_scores(self, tmp_sqlite_repo) -> None:
        """save() with details should write sub-scores to the DB."""
        score = CompositeScore(value=75.0, risk_adjusted=72.0, strategy="swing")
        details = {
            "fundamental_score": 80.0,
            "technical_score": 70.0,
            "sentiment_score": 65.0,
            "f_score": 7.0,
            "z_score": 3.5,
            "m_score": -2.8,
        }
        tmp_sqlite_repo.save("AAPL", score, details=details)

        # Verify sub-scores are persisted in the DB
        with sqlite3.connect(tmp_sqlite_repo._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM scored_symbols WHERE symbol = ? ORDER BY id DESC LIMIT 1",
                ("AAPL",),
            ).fetchone()

        assert row is not None
        assert row["fundamental_score"] == 80.0
        assert row["technical_score"] == 70.0
        assert row["sentiment_score"] == 65.0
        assert row["f_score"] == 7.0
        assert row["z_score"] == 3.5
        assert row["m_score"] == -2.8

    def test_save_without_details_still_works(self, tmp_sqlite_repo) -> None:
        """save() without details should still work (backward compat)."""
        score = CompositeScore(value=60.0, risk_adjusted=58.0, strategy="swing")
        tmp_sqlite_repo.save("MSFT", score)

        result = tmp_sqlite_repo.find_latest("MSFT")
        assert result is not None
        assert result.value == 60.0


class TestFindAllLatestForSync:
    """SqliteScoreRepository should provide sync-format data."""

    def test_find_all_latest_for_sync_returns_correct_format(self, tmp_sqlite_repo) -> None:
        """find_all_latest_for_sync() returns list of dicts with sync keys."""
        score1 = CompositeScore(value=80.0, risk_adjusted=77.0, strategy="swing")
        score2 = CompositeScore(value=65.0, risk_adjusted=63.0, strategy="position")
        tmp_sqlite_repo.save("AAPL", score1)
        tmp_sqlite_repo.save("MSFT", score2)

        rows = tmp_sqlite_repo.find_all_latest_for_sync()
        assert len(rows) == 2

        symbols = {r["symbol"] for r in rows}
        assert "AAPL" in symbols
        assert "MSFT" in symbols

        aapl = next(r for r in rows if r["symbol"] == "AAPL")
        assert aapl["composite_score"] == 80.0
        assert aapl["risk_adjusted_score"] == 77.0
        assert aapl["strategy"] == "swing"


class TestDuckDBUpsertSync:
    """DuckDBSignalStore.sync_scores() should use upsert semantics."""

    def test_sync_scores_upserts_not_deletes(self, tmp_duckdb_store) -> None:
        """sync_scores() should insert/replace individual rows, not delete all."""
        # First: insert two rows
        tmp_duckdb_store.sync_scores([
            {"symbol": "AAPL", "composite_score": 80.0, "risk_adjusted_score": 77.0, "strategy": "swing"},
            {"symbol": "MSFT", "composite_score": 65.0, "risk_adjusted_score": 63.0, "strategy": "position"},
        ])

        # Second: update just AAPL
        tmp_duckdb_store.sync_scores([
            {"symbol": "AAPL", "composite_score": 85.0, "risk_adjusted_score": 82.0, "strategy": "swing"},
        ])

        # MSFT should still be there (not deleted by bulk delete)
        rows = tmp_duckdb_store._conn.execute(
            "SELECT symbol, composite_score FROM scores ORDER BY symbol"
        ).fetchall()
        assert len(rows) == 2, f"Both rows should exist, got {rows}"
        symbols = {r[0] for r in rows}
        assert "AAPL" in symbols
        assert "MSFT" in symbols

        # AAPL should have updated score
        aapl_row = next(r for r in rows if r[0] == "AAPL")
        assert aapl_row[1] == 85.0

    def test_query_top_n_returns_consistent_scores(self, tmp_duckdb_store) -> None:
        """query_top_n() should return scores that match what was synced."""
        tmp_duckdb_store.sync_scores([
            {"symbol": "AAPL", "composite_score": 80.0, "risk_adjusted_score": 77.0, "strategy": "swing"},
        ])

        results = tmp_duckdb_store.query_top_n(top_n=10, min_composite=50.0, signal_filter=None)
        assert len(results) == 1
        assert results[0]["symbol"] == "AAPL"
        assert results[0]["composite_score"] == 80.0
        assert results[0]["risk_adjusted_score"] == 77.0
