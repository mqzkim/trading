"""SQLite-backed API key CRUD."""
from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timezone

from passlib.context import CryptContext

from .user_repo import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ApiKeyRepository:
    """API key store with bcrypt-hashed storage."""

    def __init__(
        self,
        db_path: str = "data/api_keys.db",
        user_repo: UserRepository | None = None,
    ) -> None:
        self._db_path = db_path
        self._user_repo = user_repo or UserRepository(db_path=db_path)
        self._ensure_table()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_table(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    key_hash TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
                """
            )

    def create_key(self, user_id: str, name: str) -> tuple[str, str]:
        """Create a new API key.

        Returns (key_id, raw_key). raw_key is shown once, then only the hash is stored.
        """
        key_id = secrets.token_urlsafe(8)
        raw_key = f"iat_{secrets.token_urlsafe(32)}"
        hashed = pwd_context.hash(raw_key)
        now = datetime.now(timezone.utc).isoformat()

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO api_keys (key_id, key_hash, user_id, name, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (key_id, hashed, user_id, name, now),
            )

        return key_id, raw_key

    def verify_key(self, raw_key: str) -> dict | None:
        """Verify API key. Returns user info dict or None if invalid."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT key_id, key_hash, user_id FROM api_keys WHERE is_active = 1"
            ).fetchall()

        for key_id, key_hash, user_id in rows:
            if pwd_context.verify(raw_key, key_hash):
                # Look up user tier
                user = self._user_repo.get_by_id(user_id)
                tier = user["tier"] if user else "free"
                return {"user_id": user_id, "tier": tier, "key_id": key_id}

        return None

    def revoke_key(self, key_id: str, user_id: str) -> bool:
        """Soft-delete an API key. Returns True if key found and revoked."""
        with self._conn() as conn:
            cursor = conn.execute(
                "UPDATE api_keys SET is_active = 0 WHERE key_id = ? AND user_id = ?",
                (key_id, user_id),
            )
        return cursor.rowcount > 0

    def list_keys(self, user_id: str) -> list[dict]:
        """List API keys for a user (without raw key material)."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT key_id, name, created_at, is_active
                FROM api_keys WHERE user_id = ?
                """,
                (user_id,),
            ).fetchall()

        return [
            {
                "key_id": row[0],
                "name": row[1],
                "created_at": row[2],
                "is_active": bool(row[3]),
            }
            for row in rows
        ]
