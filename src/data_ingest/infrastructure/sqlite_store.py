"""SQLite operational store -- thin adapter wrapping core/data/cache.py.

Handles operational state: cache lookups, ingestion logging.
Delegates cache operations to existing core.data.cache module.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

from core.data.cache import (
    delete as cache_delete,
    get as cache_get,
    set as cache_set,
)


_LOG_DB_PATH = Path("./data/ingestion_log.db")


class SQLiteStore:
    """Operational state store wrapping core/data/cache.py."""

    def __init__(self, log_db_path: Path | None = None) -> None:
        self._log_db_path = log_db_path or _LOG_DB_PATH
        self._log_conn: sqlite3.Connection | None = None

    def _ensure_log_db(self) -> sqlite3.Connection:
        if self._log_conn is None:
            self._log_db_path.parent.mkdir(parents=True, exist_ok=True)
            self._log_conn = sqlite3.connect(str(self._log_db_path))
            self._log_conn.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    created_at REAL NOT NULL
                )
            """)
            self._log_conn.commit()
        return self._log_conn

    # ── Cache delegation ─────────────────────────────────────────────

    def get_cached(self, key: str) -> Any | None:
        """Get a cached value (delegates to core.data.cache)."""
        return cache_get(key)

    def set_cached(self, key: str, value: Any, ttl: int) -> None:
        """Set a cached value with TTL (delegates to core.data.cache)."""
        cache_set(key, value, ttl)

    def delete_cached(self, key: str) -> None:
        """Delete a cached value (delegates to core.data.cache)."""
        cache_delete(key)

    # ── Ingestion log ────────────────────────────────────────────────

    def log_ingestion(self, ticker: str, status: str, details: str = "") -> None:
        """Log a data ingestion event."""
        conn = self._ensure_log_db()
        conn.execute(
            "INSERT INTO ingestion_log (ticker, status, details, created_at) "
            "VALUES (?, ?, ?, ?)",
            (ticker, status, details, time.time()),
        )
        conn.commit()

    def close(self) -> None:
        """Close the log database connection."""
        if self._log_conn is not None:
            self._log_conn.close()
            self._log_conn = None
