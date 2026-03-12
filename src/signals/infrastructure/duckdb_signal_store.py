"""DuckDB persistence for signals and screener queries.

Implements ISignalRepository with DuckDB backend.
Provides query_top_n() for screening/ranking the universe.
Accepts DuckDB connection via dependency injection.
"""
from __future__ import annotations

import json
from typing import Optional

import duckdb

from src.signals.domain.repositories import ISignalRepository


class DuckDBSignalStore(ISignalRepository):
    """DuckDB-backed signal store with screener query capability.

    Usage:
        conn = duckdb.connect("data/analytics.duckdb")
        store = DuckDBSignalStore(conn)
        store.save("AAPL", "BUY", 85.0, {"composite_score": 80})
        top = store.query_top_n(top_n=20, signal_filter="BUY")
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._ensure_table()
        self._ensure_scores_table()
        self._ensure_valuation_results_table()

    def _ensure_table(self) -> None:
        """Create signals table if not exists."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                symbol VARCHAR PRIMARY KEY,
                direction VARCHAR,
                strength DOUBLE,
                metadata JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _ensure_scores_table(self) -> None:
        """Create scores table if not exists."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                symbol VARCHAR PRIMARY KEY,
                composite_score DOUBLE,
                risk_adjusted_score DOUBLE,
                strategy VARCHAR
            )
        """)

    def _ensure_valuation_results_table(self) -> None:
        """Create valuation_results table if not exists."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS valuation_results (
                ticker VARCHAR PRIMARY KEY,
                intrinsic_value DOUBLE,
                margin_of_safety DOUBLE,
                has_margin BOOLEAN
            )
        """)

    def sync_scores(self, rows: list[dict]) -> None:
        """Populate scores table from external data.

        Used by bootstrap or CLI to sync SQLite scores to DuckDB
        before screening. Each dict has keys: symbol, composite_score,
        risk_adjusted_score, strategy.
        """
        self._conn.execute("DELETE FROM scores")
        for row in rows:
            self._conn.execute(
                "INSERT INTO scores (symbol, composite_score, risk_adjusted_score, strategy) "
                "VALUES (?, ?, ?, ?)",
                [row["symbol"], row["composite_score"], row["risk_adjusted_score"], row["strategy"]],
            )

    # -- ISignalRepository implementation ------------------------------------

    def save(self, symbol: str, direction: str, strength: float, metadata: dict) -> None:
        """Persist signal. Uses INSERT OR REPLACE for upsert semantics."""
        self._conn.execute(
            """
            INSERT OR REPLACE INTO signals (symbol, direction, strength, metadata, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [symbol, direction, strength, json.dumps(metadata)],
        )

    def find_active(self, symbol: str) -> Optional[dict]:
        """Retrieve the active signal for a symbol."""
        result = self._conn.execute(
            "SELECT symbol, direction, strength, metadata FROM signals WHERE symbol = ?",
            [symbol],
        ).fetchone()
        if result is None:
            return None
        return {
            "symbol": result[0],
            "direction": result[1],
            "strength": result[2],
            "metadata": json.loads(result[3]) if result[3] else {},
        }

    def find_all_active(self) -> list[dict]:
        """Retrieve all active signals."""
        rows = self._conn.execute(
            "SELECT symbol, direction, strength, metadata FROM signals"
        ).fetchall()
        return [
            {
                "symbol": row[0],
                "direction": row[1],
                "strength": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
            }
            for row in rows
        ]

    # -- Screener queries ---------------------------------------------------

    def query_top_n(
        self,
        top_n: int = 20,
        min_composite: float = 60.0,
        signal_filter: str | None = "BUY",
    ) -> list[dict]:
        """Rank universe by risk-adjusted composite score, filter by signal.

        Joins signals with scores and valuations tables (created by
        Phase 1-2 DuckDB stores) to produce screener results.

        Args:
            top_n: Maximum results to return.
            min_composite: Minimum risk_adjusted_score threshold.
            signal_filter: Filter by signal direction (e.g. "BUY"). None = no filter.

        Returns:
            List of dicts sorted by risk_adjusted_score DESC.
        """
        sql = """
            SELECT s.symbol,
                   s.composite_score,
                   s.risk_adjusted_score,
                   v.intrinsic_value,
                   v.margin_of_safety,
                   v.has_margin,
                   sig.direction,
                   sig.strength
            FROM scores s
            LEFT JOIN valuation_results v ON s.symbol = v.ticker
            LEFT JOIN signals sig ON s.symbol = sig.symbol
            WHERE s.risk_adjusted_score >= ?
        """
        params: list = [min_composite]

        if signal_filter is not None:
            sql += " AND sig.direction = ?"
            params.append(signal_filter)

        sql += " ORDER BY s.risk_adjusted_score DESC LIMIT ?"
        params.append(top_n)

        rows = self._conn.execute(sql, params).fetchall()
        columns = [
            "symbol", "composite_score", "risk_adjusted_score",
            "intrinsic_value", "margin_of_safety", "has_margin",
            "direction", "strength",
        ]
        return [dict(zip(columns, row)) for row in rows]
