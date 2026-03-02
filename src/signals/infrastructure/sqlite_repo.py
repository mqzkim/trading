"""Signals Infrastructure — SQLite Repository."""
from __future__ import annotations

import json
import os
import sqlite3
from typing import Optional

from src.signals.domain import ISignalRepository


class SqliteSignalRepository(ISignalRepository):
    """SQLite 기반 시그널 저장소.

    저장 경로: db_path (기본값 data/signals.db)
    심볼별 최신 활성 시그널을 단 하나만 유지한다.
    새 시그널 저장 시 기존 활성 시그널은 자동 만료(is_active=0).
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS signals (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol     TEXT NOT NULL,
            direction  TEXT NOT NULL,
            strength   REAL NOT NULL DEFAULT 0.0,
            metadata   TEXT,
            is_active  INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """

    _CREATE_INDEX_SYMBOL = """
        CREATE INDEX IF NOT EXISTS idx_signal_symbol
            ON signals(symbol);
    """

    _CREATE_INDEX_ACTIVE = """
        CREATE INDEX IF NOT EXISTS idx_signal_active
            ON signals(is_active, direction);
    """

    def __init__(self, db_path: str = "data/signals.db"):
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        dir_part = os.path.dirname(self._db_path)
        if dir_part:
            os.makedirs(dir_part, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(self._CREATE_TABLE)
            conn.execute(self._CREATE_INDEX_SYMBOL)
            conn.execute(self._CREATE_INDEX_ACTIVE)

    # ── ISignalRepository 구현 ─────────────────────────────────────

    def save(self, symbol: str, direction: str, strength: float, metadata: dict) -> None:
        """심볼의 기존 활성 시그널을 만료시키고 새 시그널을 삽입한다."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "UPDATE signals SET is_active=0 WHERE symbol=? AND is_active=1",
                (symbol,),
            )
            conn.execute(
                "INSERT INTO signals (symbol, direction, strength, metadata) VALUES (?, ?, ?, ?)",
                (symbol, direction, strength, json.dumps(metadata)),
            )

    def find_active(self, symbol: str) -> Optional[dict]:
        """심볼의 가장 최근 활성 시그널을 반환. 없으면 None."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM signals WHERE symbol=? AND is_active=1"
                " ORDER BY created_at DESC LIMIT 1",
                (symbol,),
            ).fetchone()
        return dict(row) if row else None

    def find_all_active(self) -> list[dict]:
        """BUY 또는 SELL 방향의 모든 활성 시그널을 반환."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM signals"
                " WHERE is_active=1 AND direction IN ('BUY','SELL')"
                " ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]
