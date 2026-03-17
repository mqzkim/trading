"""DuckDB implementation of ITradeHistoryRepository."""
from __future__ import annotations

from datetime import date

import duckdb

from src.performance.domain.entities import ClosedTrade
from src.performance.domain.repositories import ITradeHistoryRepository


class DuckDBTradeHistoryRepository(ITradeHistoryRepository):
    """DuckDB-backed trade history persistence.

    Uses in-constructor table creation (consistent with DuckDBSignalStore pattern).
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS trades_id_seq START 1;
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER DEFAULT nextval('trades_id_seq') PRIMARY KEY,
                symbol VARCHAR NOT NULL,
                entry_date DATE NOT NULL,
                exit_date DATE NOT NULL,
                entry_price DOUBLE NOT NULL,
                exit_price DOUBLE NOT NULL,
                quantity INTEGER NOT NULL,
                pnl DOUBLE NOT NULL,
                pnl_pct DOUBLE NOT NULL,
                strategy VARCHAR,
                sector VARCHAR,
                composite_score DOUBLE,
                technical_score DOUBLE,
                fundamental_score DOUBLE,
                sentiment_score DOUBLE,
                regime VARCHAR,
                weights_json VARCHAR,
                signal_direction VARCHAR
            )
        """)

    def save(self, trade: ClosedTrade) -> None:
        self._conn.execute(
            """INSERT INTO trades (
                symbol, entry_date, exit_date, entry_price, exit_price,
                quantity, pnl, pnl_pct, strategy, sector,
                composite_score, technical_score, fundamental_score,
                sentiment_score, regime, weights_json, signal_direction
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                trade.symbol,
                trade.entry_date,
                trade.exit_date,
                trade.entry_price,
                trade.exit_price,
                trade.quantity,
                trade.pnl,
                trade.pnl_pct,
                trade.strategy,
                trade.sector,
                trade.composite_score,
                trade.technical_score,
                trade.fundamental_score,
                trade.sentiment_score,
                trade.regime,
                trade.weights_json,
                trade.signal_direction,
            ],
        )

    def find_all(self) -> list[ClosedTrade]:
        rows = self._conn.execute(
            "SELECT id, symbol, entry_date, exit_date, entry_price, exit_price, "
            "quantity, pnl, pnl_pct, strategy, sector, composite_score, "
            "technical_score, fundamental_score, sentiment_score, regime, "
            "weights_json, signal_direction FROM trades ORDER BY exit_date"
        ).fetchall()
        return [self._to_entity(row) for row in rows]

    def count(self) -> int:
        result = self._conn.execute("SELECT COUNT(*) FROM trades").fetchone()
        return int(result[0]) if result else 0

    @staticmethod
    def _to_entity(row: tuple) -> ClosedTrade:
        entry_date = row[2]
        exit_date = row[3]
        if isinstance(entry_date, str):
            entry_date = date.fromisoformat(entry_date)
        if isinstance(exit_date, str):
            exit_date = date.fromisoformat(exit_date)
        return ClosedTrade(
            id=row[0],
            symbol=row[1],
            entry_date=entry_date,
            exit_date=exit_date,
            entry_price=row[4],
            exit_price=row[5],
            quantity=row[6],
            pnl=row[7],
            pnl_pct=row[8],
            strategy=row[9],
            sector=row[10],
            composite_score=row[11],
            technical_score=row[12],
            fundamental_score=row[13],
            sentiment_score=row[14],
            regime=row[15],
            weights_json=row[16],
            signal_direction=row[17],
        )
