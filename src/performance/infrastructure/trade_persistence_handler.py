"""Event handler: persists closed trades to DuckDB."""
from __future__ import annotations

import json

from src.performance.domain.entities import ClosedTrade
from src.performance.domain.repositories import ITradeHistoryRepository
from src.portfolio.domain.events import PositionClosedEvent


class TradePersistenceHandler:
    """Subscribes to PositionClosedEvent, persists trade to DuckDB."""

    def __init__(self, trade_repo: ITradeHistoryRepository) -> None:
        self._trade_repo = trade_repo

    def on_position_closed(self, event: PositionClosedEvent) -> None:
        snap = event.score_snapshot or {}
        weights = snap.get("weights")
        trade = ClosedTrade(
            id=None,
            symbol=event.symbol,
            entry_date=event.entry_date,
            exit_date=event.exit_date,
            entry_price=event.entry_price,
            exit_price=event.exit_price,
            quantity=event.quantity,
            pnl=event.pnl,
            pnl_pct=event.pnl_pct,
            strategy=event.strategy,
            sector=event.sector,
            composite_score=snap.get("composite_score"),
            technical_score=snap.get("technical_score"),
            fundamental_score=snap.get("fundamental_score"),
            sentiment_score=snap.get("sentiment_score"),
            regime=snap.get("regime"),
            weights_json=json.dumps(weights) if weights else None,
            signal_direction=event.signal_direction or None,
        )
        self._trade_repo.save(trade)
