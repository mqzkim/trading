"""Execution Infrastructure — SQLite Trade Plan Repository.

SqlitePositionRepository 패턴을 따름.
같은 DB 파일(data/portfolio.db)을 공유하여 일관성 유지.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from src.execution.domain.repositories import ITradePlanRepository
from src.execution.domain.value_objects import TradePlan, TradePlanStatus


class SqliteTradePlanRepository(ITradePlanRepository):
    """SQLite 기반 trade plan 저장소.

    저장 경로: db_path (기본값 data/portfolio.db -- 포지션 DB와 공유)
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS trade_plans (
            symbol          TEXT PRIMARY KEY,
            direction       TEXT NOT NULL,
            entry_price     REAL NOT NULL,
            stop_loss_price REAL NOT NULL,
            take_profit_price REAL NOT NULL,
            quantity        INTEGER NOT NULL,
            position_value  REAL NOT NULL,
            reasoning_trace TEXT,
            composite_score REAL,
            margin_of_safety REAL,
            signal_direction TEXT,
            status          TEXT NOT NULL DEFAULT 'PENDING',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    def _now_utc(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── ITradePlanRepository 구현 ─────────────────────────────────────

    def save(self, plan: TradePlan, status: TradePlanStatus) -> None:
        now = self._now_utc()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO trade_plans
                    (symbol, direction, entry_price, stop_loss_price, take_profit_price,
                     quantity, position_value, reasoning_trace, composite_score,
                     margin_of_safety, signal_direction, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan.symbol,
                    plan.direction,
                    plan.entry_price,
                    plan.stop_loss_price,
                    plan.take_profit_price,
                    plan.quantity,
                    plan.position_value,
                    plan.reasoning_trace,
                    plan.composite_score,
                    plan.margin_of_safety,
                    plan.signal_direction,
                    status.value,
                    now,
                    now,
                ),
            )

    def find_pending(self) -> List[dict]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM trade_plans WHERE status = ? ORDER BY created_at DESC",
                ("PENDING",),
            ).fetchall()
        return [dict(row) for row in rows]

    def find_by_symbol(self, symbol: str) -> Optional[dict]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM trade_plans WHERE symbol = ?", (symbol,)
            ).fetchone()
        return dict(row) if row else None

    def update_status(self, symbol: str, new_status: TradePlanStatus) -> None:
        now = self._now_utc()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "UPDATE trade_plans SET status = ?, updated_at = ? WHERE symbol = ?",
                (new_status.value, now, symbol),
            )
