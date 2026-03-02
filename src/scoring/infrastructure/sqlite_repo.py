"""Scoring Infrastructure — SQLite Repository."""
from __future__ import annotations

import os
import sqlite3
from typing import Optional

from src.scoring.domain import IScoreRepository
from src.scoring.domain.value_objects import CompositeScore


class SqliteScoreRepository(IScoreRepository):
    """SQLite 기반 스코어 저장소.

    저장 경로: db_path (기본값 data/scoring.db)
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS scored_symbols (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol      TEXT    NOT NULL,
            composite_score  REAL NOT NULL,
            risk_adjusted    REAL NOT NULL DEFAULT 0.0,
            strategy         TEXT NOT NULL DEFAULT 'swing',
            fundamental_score REAL,
            technical_score   REAL,
            sentiment_score   REAL,
            f_score     REAL,
            z_score     REAL,
            m_score     REAL,
            scored_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """

    _CREATE_INDEX_SYMBOL = """
        CREATE INDEX IF NOT EXISTS idx_score_symbol
            ON scored_symbols(symbol);
    """

    _CREATE_INDEX_COMPOSITE = """
        CREATE INDEX IF NOT EXISTS idx_score_composite
            ON scored_symbols(composite_score DESC);
    """

    def __init__(self, db_path: str = "data/scoring.db"):
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        dir_part = os.path.dirname(self._db_path)
        if dir_part:
            os.makedirs(dir_part, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(self._CREATE_TABLE)
            conn.execute(self._CREATE_INDEX_SYMBOL)
            conn.execute(self._CREATE_INDEX_COMPOSITE)

    # ── IScoreRepository 구현 ─────────────────────────────────────

    def save(self, symbol: str, score: CompositeScore) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO scored_symbols
                    (symbol, composite_score, risk_adjusted, strategy)
                VALUES (?, ?, ?, ?)
                """,
                (
                    symbol,
                    score.value,
                    score.risk_adjusted,
                    score.strategy,
                ),
            )

    def find_latest(self, symbol: str) -> Optional[CompositeScore]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT composite_score, risk_adjusted, strategy
                FROM scored_symbols
                WHERE symbol = ?
                ORDER BY scored_at DESC
                LIMIT 1
                """,
                (symbol,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_vo(dict(row))

    def find_all_latest(self, limit: int = 100) -> dict[str, CompositeScore]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT symbol, composite_score, risk_adjusted, strategy
                FROM scored_symbols
                WHERE id IN (
                    SELECT MAX(id) FROM scored_symbols GROUP BY symbol
                )
                ORDER BY composite_score DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return {row["symbol"]: self._row_to_vo(dict(row)) for row in rows}

    # ── 내부 헬퍼 ─────────────────────────────────────────────────

    @staticmethod
    def _row_to_vo(row: dict) -> CompositeScore:
        return CompositeScore(
            value=row["composite_score"],
            risk_adjusted=row["risk_adjusted"],
            strategy=row["strategy"],
        )
