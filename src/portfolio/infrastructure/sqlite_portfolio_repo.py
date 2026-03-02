"""Portfolio Infrastructure — SQLite Portfolio Repository."""
from __future__ import annotations

import os
import sqlite3
from typing import Optional

from src.portfolio.domain import IPortfolioRepository, Portfolio


class SqlitePortfolioRepository(IPortfolioRepository):
    """SQLite 기반 포트폴리오 저장소.

    저장 경로: db_path (기본값 data/portfolio.db)
    positions 필드는 포지션 저장소(SqlitePositionRepository)가 별도 관리하므로
    여기서는 portfolio 메타데이터(initial_value, peak_value)만 영속화.
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS portfolios (
            portfolio_id  TEXT PRIMARY KEY,
            initial_value REAL NOT NULL,
            peak_value    REAL NOT NULL,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    # ── IPortfolioRepository 구현 ────────────────────────────────────

    def save(self, portfolio: Portfolio) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO portfolios (portfolio_id, initial_value, peak_value)
                VALUES (?, ?, ?)
                """,
                (portfolio.portfolio_id, portfolio.initial_value, portfolio.peak_value),
            )

    def find_by_id(self, portfolio_id: str) -> Optional[Portfolio]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM portfolios WHERE portfolio_id = ?", (portfolio_id,)
            ).fetchone()
        if not row:
            return None
        p = Portfolio(
            portfolio_id=row["portfolio_id"],
            initial_value=row["initial_value"],
        )
        p.peak_value = row["peak_value"]
        return p
