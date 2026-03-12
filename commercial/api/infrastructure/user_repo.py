"""SQLite-backed user/tier store."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


class UserRepository:
    """Minimal user store for tier management."""

    def __init__(self, db_path: str = "data/api_keys.db") -> None:
        self._db_path = db_path
        self._ensure_table()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_table(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    tier TEXT NOT NULL DEFAULT 'free',
                    created_at TEXT NOT NULL
                )
                """
            )

    def create_user(self, user_id: str, tier: str = "free") -> None:
        """Insert or ignore a user record."""
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id, tier, created_at) VALUES (?, ?, ?)",
                (user_id, tier, now),
            )

    def get_by_id(self, user_id: str) -> dict | None:
        """Return user dict or None if not found."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT user_id, tier, created_at FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return {"user_id": row[0], "tier": row[1], "created_at": row[2]}

    def update_tier(self, user_id: str, tier: str) -> None:
        """Update user tier."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET tier = ? WHERE user_id = ?",
                (tier, user_id),
            )
