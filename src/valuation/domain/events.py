"""Valuation domain events.

Events published when valuation completes for a ticker.
Used for cross-context communication via async event bus.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ValuationCompletedEvent(DomainEvent):
    """Raised when ensemble valuation completes for a ticker.

    Consumed by Signals context for buy/sell signal generation.
    """

    ticker: str
    intrinsic_value: float
    margin_of_safety: float
    confidence: float
    dcf_value: float
    epv_value: float
    relative_value: float
    sector: str
