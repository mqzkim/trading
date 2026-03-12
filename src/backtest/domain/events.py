"""Backtest domain -- Domain Events."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.shared.domain import DomainEvent


@dataclass(frozen=True, kw_only=True)
class BacktestCompletedEvent(DomainEvent):
    """Emitted when a backtest or walk-forward validation completes.

    Subscribers: portfolio context (position sizing), signals context (feedback loop).
    """

    symbol: str = field(default="")
    sharpe_ratio: float = field(default=0.0)
    profit_factor: float = field(default=0.0)
    max_drawdown: float = field(default=0.0)
