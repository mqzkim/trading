"""SignalFusion response schemas.

LEGAL BOUNDARY: This schema intentionally EXCLUDES:
  - Any "recommendation" or "action" field
  - Position size or capital allocation
  - Stop-loss or take-profit prices
  - margin_of_safety

Only exposes: direction (informational), strength, consensus_count,
methodology_scores, methodology_votes, regime_type.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .common import DISCLAIMER


class MethodologyVote(BaseModel):
    """Individual methodology vote."""

    name: str
    direction: str
    score: Optional[float] = None


class SignalResponse(BaseModel):
    """Response for GET /api/v1/signals/{ticker}.

    Does NOT include position sizing or buy/sell recommendations.
    """

    symbol: str
    direction: str  # BULLISH / BEARISH / NEUTRAL
    strength: float = Field(ge=0, le=1)
    consensus_count: int
    methodology_count: int
    methodology_scores: Optional[dict] = None
    methodology_votes: Optional[list[MethodologyVote]] = None
    regime_type: Optional[str] = None
    disclaimer: str = DISCLAIMER
