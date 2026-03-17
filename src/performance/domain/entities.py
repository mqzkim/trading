"""Performance domain -- ClosedTrade entity."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ClosedTrade:
    """A completed trade with full decision context.

    Persisted to DuckDB trades table on every PositionClosedEvent.
    id is auto-assigned by DuckDB (None on creation).
    """

    id: Optional[int]
    symbol: str
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    pnl_pct: float
    strategy: str
    sector: str
    composite_score: Optional[float]
    technical_score: Optional[float]
    fundamental_score: Optional[float]
    sentiment_score: Optional[float]
    regime: Optional[str]
    weights_json: Optional[str]
    signal_direction: Optional[str]
