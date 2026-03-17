"""Performance API schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class KPIs(BaseModel):
    sharpe: Optional[float] = None
    sortino: Optional[float] = None
    win_rate: Optional[float] = None
    max_drawdown: Optional[float] = None


class BrinsonRow(BaseModel):
    name: str
    allocation_effect: float
    selection_effect: float
    interaction_effect: float
    total_effect: float


class SignalICPerAxis(BaseModel):
    fundamental: Optional[float] = None
    technical: Optional[float] = None
    sentiment: Optional[float] = None


class AttributionResponse(BaseModel):
    kpis: KPIs
    brinson_table: list[BrinsonRow]
    equity_curve: Optional[list] = None
    signal_ic: Optional[float] = None
    signal_ic_per_axis: SignalICPerAxis
    kelly_efficiency: Optional[float] = None
    trade_count: int
    disclaimer: str


class ProposalResponse(BaseModel):
    id: str
    regime: Optional[str] = None
    axis: Optional[str] = None
    current_weight: Optional[float] = None
    proposed_weight: Optional[float] = None
    walk_forward_sharpe: Optional[float] = None
    status: str = "pending"
    created_at: Optional[str] = None
    decided_at: Optional[str] = None


class ProposalActionResponse(BaseModel):
    status: str
    proposal_id: str
