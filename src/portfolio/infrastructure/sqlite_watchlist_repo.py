"""Portfolio Infrastructure -- SQLite Watchlist Repository."""
from __future__ import annotations

import os
import sqlite3
from datetime import date
from typing import List, Optional

from src.portfolio.domain import IWatchlistRepository, WatchlistEntry


class SqliteWatchlistRepository(IWatchlistRepository):
    """SQLite-backed watchlist persistence.

    Uses same DB as positions (data/portfolio.db) with a separate 'watchlists' table.
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS watchlists (
            symbol      TEXT PRIMARY KEY,
            added_date  TEXT NOT NULL,
            notes       TEXT,
            alert_above REAL,
            alert_below REAL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """

    def __init__(self, db_path: str = "data/portfolio.db"):
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        dir_part = os.path.dirname(self._db_path)
        if dir_part:
            os.makedirs(dir_part, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(self._CREATE_TABLE)

    def _row_to_entry(self, row: sqlite3.Row) -> WatchlistEntry:
        return WatchlistEntry(
            symbol=row["symbol"],
            added_date=date.fromisoformat(row["added_date"]),
            notes=row["notes"],
            alert_above=row["alert_above"],
            alert_below=row["alert_below"],
        )

    # -- IWatchlistRepository implementation ----------------------------------

    def add(self, entry: WatchlistEntry) -> None:
        """Persist a watchlist entry. Uses INSERT OR REPLACE for upsert."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO watchlists
                    (symbol, added_date, notes, alert_above, alert_below)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entry.symbol,
                    entry.added_date.isoformat(),
                    entry.notes,
                    entry.alert_above,
                    entry.alert_below,
                ),
            )

    def remove(self, symbol: str) -> None:
        """Remove a watchlist entry by symbol."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM watchlists WHERE symbol = ?", (symbol,))

    def find_all(self) -> List[WatchlistEntry]:
        """Return all watchlist entries, newest first."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM watchlists ORDER BY added_date DESC"
            ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def find_by_symbol(self, symbol: str) -> Optional[WatchlistEntry]:
        """Find a single watchlist entry by symbol."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM watchlists WHERE symbol = ?", (symbol,)
            ).fetchone()
        return self._row_to_entry(row) if row else None
