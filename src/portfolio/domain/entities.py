"""Portfolio 도메인 — Position Entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from src.shared.domain import Entity

from .value_objects import ATRStop, RiskTier


@dataclass(eq=False)
class Position(Entity[str]):
    """포지션 엔티티.

    id = symbol (종목 코드).
    청산 시 PositionClosedEvent 발행.
    """

    symbol: str = ""
    entry_price: float = 0.0
    quantity: int = 0
    entry_date: date = field(default_factory=date.today)
    strategy: str = "swing"       # "swing" | "position"
    atr_stop: Optional[ATRStop] = None
    sector: str = "unknown"
    risk_tier: RiskTier = RiskTier.MEDIUM

    @property
    def id(self) -> str:
        return self.symbol

    @property
    def market_value(self) -> float:
        return self.entry_price * self.quantity

    def close(self, exit_price: float) -> dict:
        """포지션 청산. 손익 정보 반환 및 PositionClosedEvent 발행."""
        from .events import PositionClosedEvent

        pnl = (exit_price - self.entry_price) * self.quantity
        pnl_pct = (exit_price - self.entry_price) / self.entry_price
        self.add_domain_event(
            PositionClosedEvent(symbol=self.symbol, pnl=pnl, pnl_pct=pnl_pct)
        )
        return {"symbol": self.symbol, "pnl": pnl, "pnl_pct": pnl_pct}
