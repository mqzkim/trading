"""Regime Infrastructure — SQLite Repository."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Optional

from src.regime.domain import (
    IRegimeRepository,
    MarketRegime,
    RegimeType,
    VIXLevel,
    TrendStrength,
    YieldCurve,
    SP500Position,
)


class SqliteRegimeRepository(IRegimeRepository):
    """SQLite 기반 레짐 저장소.

    저장 경로: db_path (기본값 data/regime.db)
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS market_regimes (
            id TEXT PRIMARY KEY,
            regime_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            vix REAL NOT NULL,
            adx REAL NOT NULL,
            yield_spread REAL NOT NULL,
            sp500_price REAL NOT NULL,
            sp500_ma200 REAL NOT NULL,
            confirmed_days INTEGER NOT NULL DEFAULT 0,
            metadata TEXT,
            detected_at TIMESTAMP NOT NULL
        );
    """

    _CREATE_INDEX = """
        CREATE INDEX IF NOT EXISTS idx_regime_detected_at
            ON market_regimes(detected_at DESC);
    """

    def __init__(self, db_path: str = "data/regime.db"):
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        dir_part = os.path.dirname(self._db_path)
        if dir_part:
            os.makedirs(dir_part, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(self._CREATE_TABLE)
            conn.execute(self._CREATE_INDEX)

    # ── IRegimeRepository 구현 ─────────────────────────────────────

    def save(self, regime: MarketRegime) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO market_regimes
                    (id, regime_type, confidence, vix, adx, yield_spread,
                     sp500_price, sp500_ma200, confirmed_days, metadata, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    regime.id,
                    regime.regime_type.value,
                    regime.confidence,
                    regime.vix.value,
                    regime.trend.adx,
                    regime.yield_curve.spread,
                    regime.sp500.current_price,
                    regime.sp500.ma_200,
                    regime.confirmed_days,
                    json.dumps({"regime_type": regime.regime_type.value}),
                    regime.detected_at.isoformat(),
                ),
            )

    def find_latest(self) -> Optional[MarketRegime]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM market_regimes ORDER BY detected_at DESC LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return self._row_to_entity(dict(row))

    def find_by_date_range(
        self,
        start: datetime,
        end: datetime,
    ) -> list[MarketRegime]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM market_regimes
                WHERE detected_at >= ? AND detected_at <= ?
                ORDER BY detected_at DESC
                """,
                (start.isoformat(), end.isoformat()),
            ).fetchall()
        return [self._row_to_entity(dict(r)) for r in rows]

    # ── 내부 헬퍼 ─────────────────────────────────────────────────

    def _row_to_entity(self, row: dict) -> MarketRegime:
        return MarketRegime(
            _id=row["id"],
            regime_type=RegimeType(row["regime_type"]),
            confidence=row["confidence"],
            vix=VIXLevel(value=row["vix"]),
            trend=TrendStrength(adx=row["adx"]),
            yield_curve=YieldCurve(spread=row["yield_spread"]),
            sp500=SP500Position(
                current_price=row["sp500_price"],
                ma_200=row["sp500_ma200"],
            ),
            confirmed_days=row["confirmed_days"],
            detected_at=datetime.fromisoformat(row["detected_at"]),
        )
