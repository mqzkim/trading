"""Execution Application — Command Dataclasses.

Commands represent intentions to change state.
Each command carries the data needed for a single use case.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GenerateTradePlanCommand:
    """Request to generate a new trade plan via TradePlanService."""

    symbol: str
    entry_price: float
    atr: float
    capital: float
    peak_value: float
    current_value: float
    intrinsic_value: float
    composite_score: float
    margin_of_safety: float
    signal_direction: str
    reasoning_trace: str
    sector_exposure: float = 0.0
    atr_multiplier: float = 3.0


@dataclass
class ApproveTradePlanCommand:
    """Approve or reject a pending trade plan."""

    symbol: str
    approved: bool
    modified_quantity: Optional[int] = None
    modified_stop_loss: Optional[float] = None


@dataclass
class ExecuteOrderCommand:
    """Execute an approved trade plan as a bracket order."""

    symbol: str


@dataclass
class KillSwitchCommand:
    """Emergency kill switch -- cancel all orders, optionally liquidate."""

    liquidate: bool = False
    confirm: bool = False


@dataclass
class SyncPositionsCommand:
    """Sync local positions to match broker state."""

    market: str = "us"
