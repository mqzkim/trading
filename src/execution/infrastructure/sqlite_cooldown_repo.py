"""Execution Infrastructure -- SQLite Cooldown Repository.

Persists CooldownState to SQLite. Follows SqliteTradePlanRepository pattern.
Same DB file (data/portfolio.db) by default for consistency.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from src.execution.domain.repositories import ICooldownRepository
from src.execution.domain.value_objects import CooldownState


class SqliteCooldownRepository(ICooldownRepository):
    """SQLite-based cooldown state persistence.

    Stores drawdown cooldown state with UTC timestamps.
    Uses WAL journal mode for concurrent safety.
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS cooldown_state (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            triggered_at    TEXT NOT NULL,
            expires_at      TEXT NOT NULL,
            current_tier    INTEGER NOT NULL,
            re_entry_pct    INTEGER NOT NULL DEFAULT 0,
            reason          TEXT NOT NULL DEFAULT 'drawdown',
            is_active       INTEGER NOT NULL DEFAULT 1,
            force_overridden INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """

    def __init__(self, db_path: str = "data/portfolio.db") -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        dir_part = os.path.dirname(self._db_path)
        if dir_part:
            os.makedirs(dir_part, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(self._CREATE_TABLE)

    def save(self, state: CooldownState) -> int:
        """Persist cooldown state. Returns assigned id."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO cooldown_state
                    (triggered_at, expires_at, current_tier, re_entry_pct,
                     reason, is_active, force_overridden)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.triggered_at.isoformat(),
                    state.expires_at.isoformat(),
                    state.current_tier,
                    state.re_entry_pct,
                    state.reason,
                    1 if state.is_active else 0,
                    1 if state.force_overridden else 0,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_active(self) -> Optional[CooldownState]:
        """Return active, non-expired cooldown or None.

        Checks expiry in Python (not SQL) for timezone safety.
        Returns the most recently triggered active cooldown.
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM cooldown_state
                WHERE is_active = 1
                ORDER BY triggered_at DESC
                """,
            ).fetchall()

        for row in rows:
            state = self._row_to_state(row)
            if not state.is_expired():
                return state

        return None

    def deactivate(self, cooldown_id: int) -> None:
        """Mark cooldown as inactive."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "UPDATE cooldown_state SET is_active = 0 WHERE id = ?",
                (cooldown_id,),
            )

    def get_history(self) -> list[CooldownState]:
        """Return all cooldown records ordered by triggered_at desc."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM cooldown_state ORDER BY triggered_at DESC",
            ).fetchall()

        return [self._row_to_state(row) for row in rows]

    @staticmethod
    def _row_to_state(row: sqlite3.Row) -> CooldownState:
        """Convert SQLite row to CooldownState."""
        return CooldownState(
            triggered_at=datetime.fromisoformat(row["triggered_at"]).replace(
                tzinfo=timezone.utc
            ),
            expires_at=datetime.fromisoformat(row["expires_at"]).replace(
                tzinfo=timezone.utc
            ),
            current_tier=row["current_tier"],
            re_entry_pct=row["re_entry_pct"],
            reason=row["reason"],
            is_active=bool(row["is_active"]),
            force_overridden=bool(row["force_overridden"]),
            id=row["id"],
        )
