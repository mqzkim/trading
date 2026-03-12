"""DuckDB persistence for backtest results.

Implements IBacktestResultRepository with DuckDB backend.
Accepts DuckDB connection via dependency injection.
"""
from __future__ import annotations

import json
from typing import Optional

import duckdb

from src.backtest.domain.repositories import IBacktestResultRepository


class DuckDBBacktestStore(IBacktestResultRepository):
    """DuckDB-backed store for backtest results.

    Usage:
        conn = duckdb.connect("data/analytics.duckdb")
        store = DuckDBBacktestStore(conn)
        store.save("AAPL", {"capital": 100000}, {"sharpe": 1.5})
        latest = store.find_latest("AAPL")
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create backtest_results table and sequence if not exists."""
        self._conn.execute(
            "CREATE SEQUENCE IF NOT EXISTS backtest_id_seq START 1"
        )
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER DEFAULT nextval('backtest_id_seq'),
                symbol VARCHAR,
                config JSON,
                report JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def save(self, symbol: str, config: dict, report: dict) -> None:
        """Persist a backtest result."""
        self._conn.execute(
            """
            INSERT INTO backtest_results (symbol, config, report, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [symbol, json.dumps(config), json.dumps(report)],
        )

    def find_latest(self, symbol: str) -> Optional[dict]:
        """Retrieve the most recent backtest result for a symbol."""
        result = self._conn.execute(
            """
            SELECT symbol, config, report, created_at
            FROM backtest_results
            WHERE symbol = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            [symbol],
        ).fetchone()
        if result is None:
            return None
        return {
            "symbol": result[0],
            "config": json.loads(result[1]) if result[1] else {},
            "report": json.loads(result[2]) if result[2] else {},
            "created_at": str(result[3]),
        }

    def find_all(self) -> list[dict]:
        """Retrieve all backtest results, most recent first."""
        rows = self._conn.execute(
            """
            SELECT symbol, config, report, created_at
            FROM backtest_results
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
        return [
            {
                "symbol": row[0],
                "config": json.loads(row[1]) if row[1] else {},
                "report": json.loads(row[2]) if row[2] else {},
                "created_at": str(row[3]),
            }
            for row in rows
        ]
