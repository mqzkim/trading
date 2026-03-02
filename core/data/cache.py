"""SQLite-based data cache with TTL support."""
import sqlite3
import json
import time
import threading
from pathlib import Path
from typing import Any


_local = threading.local()
DB_PATH = Path("./data/trading.db")


def _get_conn() -> sqlite3.Connection:
    """Get thread-local connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
        """)
        conn.commit()
        _local.conn = conn
    return _local.conn


def get(key: str) -> Any | None:
    """Return cached value if not expired, else None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
    ).fetchone()
    if row is None:
        return None
    value, expires_at = row
    if time.time() > expires_at:
        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()
        return None
    return json.loads(value)


def set(key: str, value: Any, ttl: int) -> None:
    """Store value with TTL in seconds."""
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
        (key, json.dumps(value, default=str), time.time() + ttl),
    )
    conn.commit()


def delete(key: str) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
    conn.commit()


def purge_expired() -> int:
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),))
    conn.commit()
    return cursor.rowcount


PRICE_TTL = 86_400      # 24 hours
FUNDAMENTALS_TTL = 604_800  # 7 days
MARKET_TTL = 3_600      # 1 hour
