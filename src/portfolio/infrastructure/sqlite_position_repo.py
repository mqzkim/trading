"""Portfolio Infrastructure — SQLite Position Repository."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import date
from typing import List, Optional

from src.portfolio.domain import ATRStop, IPositionRepository, Position, RiskTier


class SqlitePositionRepository(IPositionRepository):
    """SQLite 기반 포지션 저장소.

    저장 경로: db_path (기본값 data/portfolio.db)
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS positions (
            symbol        TEXT PRIMARY KEY,
            entry_price   REAL NOT NULL,
            quantity      INTEGER NOT NULL,
            entry_date    TEXT NOT NULL,
            strategy      TEXT NOT NULL DEFAULT 'swing',
            sector        TEXT NOT NULL DEFAULT 'unknown',
            risk_tier     TEXT NOT NULL DEFAULT 'medium',
            atr_stop_json TEXT,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    def _row_to_position(self, row: sqlite3.Row) -> Position:
        atr_stop = None
        if row["atr_stop_json"]:
            d = json.loads(row["atr_stop_json"])
            atr_stop = ATRStop(**d)
        return Position(
            symbol=row["symbol"],
            entry_price=row["entry_price"],
            quantity=row["quantity"],
            entry_date=date.fromisoformat(row["entry_date"]),
            strategy=row["strategy"],
            sector=row["sector"],
            risk_tier=RiskTier(row["risk_tier"]),
            atr_stop=atr_stop,
        )

    # ── IPositionRepository 구현 ─────────────────────────────────────

    def save(self, position: Position) -> None:
        atr_json = None
        if position.atr_stop:
            atr_json = json.dumps({
                "entry_price": position.atr_stop.entry_price,
                "atr": position.atr_stop.atr,
                "multiplier": position.atr_stop.multiplier,
            })
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO positions
                    (symbol, entry_price, quantity, entry_date, strategy, sector, risk_tier, atr_stop_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    position.symbol,
                    position.entry_price,
                    position.quantity,
                    position.entry_date.isoformat(),
                    position.strategy,
                    position.sector,
                    position.risk_tier.value,
                    atr_json,
                ),
            )

    def find_by_symbol(self, symbol: str) -> Optional[Position]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM positions WHERE symbol = ?", (symbol,)
            ).fetchone()
        return self._row_to_position(row) if row else None

    def find_all_open(self) -> List[Position]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM positions ORDER BY created_at DESC"
            ).fetchall()
        return [self._row_to_position(r) for r in rows]

    def delete(self, symbol: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
