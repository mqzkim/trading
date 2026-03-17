"""DuckDB implementation of IProposalRepository."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import duckdb

from src.performance.domain.repositories import IProposalRepository


class DuckDBProposalRepository(IProposalRepository):
    """DuckDB-backed proposal persistence."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id VARCHAR PRIMARY KEY,
                regime VARCHAR,
                axis VARCHAR,
                current_weight DOUBLE,
                proposed_weight DOUBLE,
                walk_forward_sharpe DOUBLE,
                status VARCHAR DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                decided_at TIMESTAMP
            )
        """)

    def save(self, proposal: dict) -> None:
        self._conn.execute(
            """INSERT INTO proposals (id, regime, axis, current_weight,
                proposed_weight, walk_forward_sharpe, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                proposal["id"],
                proposal.get("regime"),
                proposal.get("axis"),
                proposal.get("current_weight"),
                proposal.get("proposed_weight"),
                proposal.get("walk_forward_sharpe"),
                proposal.get("status", "pending"),
            ],
        )

    def find_pending(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, regime, axis, current_weight, proposed_weight, "
            "walk_forward_sharpe, status, created_at FROM proposals "
            "WHERE status = 'pending' ORDER BY created_at DESC"
        ).fetchall()
        return [self._to_dict(r) for r in rows]

    def find_by_id(self, proposal_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT id, regime, axis, current_weight, proposed_weight, "
            "walk_forward_sharpe, status, created_at, decided_at FROM proposals "
            "WHERE id = ?",
            [proposal_id],
        ).fetchone()
        if row is None:
            return None
        return self._to_dict(row)

    def approve(self, proposal_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "UPDATE proposals SET status = 'approved', decided_at = ? WHERE id = ?",
            [now, proposal_id],
        )

    def reject(self, proposal_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "UPDATE proposals SET status = 'rejected', decided_at = ? WHERE id = ?",
            [now, proposal_id],
        )

    def list_history(self, limit: int = 5) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, regime, axis, current_weight, proposed_weight, "
            "walk_forward_sharpe, status, created_at, decided_at FROM proposals "
            "WHERE status IN ('approved', 'rejected') "
            "ORDER BY decided_at DESC LIMIT ?",
            [limit],
        ).fetchall()
        return [self._to_dict(r) for r in rows]

    @staticmethod
    def _to_dict(row: tuple) -> dict:
        keys = [
            "id", "regime", "axis", "current_weight", "proposed_weight",
            "walk_forward_sharpe", "status", "created_at",
        ]
        if len(row) > 8:
            keys.append("decided_at")
        return dict(zip(keys, row))
