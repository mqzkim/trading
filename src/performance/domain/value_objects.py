"""Performance domain -- value objects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AttributionLevel:
    """Single level in Brinson-Fachler decomposition."""

    name: str
    allocation_effect: float
    selection_effect: float
    interaction_effect: float
    total_effect: float


@dataclass(frozen=True)
class PerformanceReport:
    """Aggregated performance report with attribution and signal metrics."""

    sharpe: Optional[float]
    sortino: Optional[float]
    win_rate: Optional[float]
    max_drawdown: Optional[float]
    trade_count: int
    attribution: list[AttributionLevel]
    signal_ic_fundamental: Optional[float]
    signal_ic_technical: Optional[float]
    signal_ic_sentiment: Optional[float]
    kelly_efficiency: Optional[float]
