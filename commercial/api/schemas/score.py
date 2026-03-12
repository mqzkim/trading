"""QuantScore response schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .common import DISCLAIMER


class QuantScoreResponse(BaseModel):
    """Response for GET /api/v1/quantscore/{ticker}."""

    symbol: str
    composite_score: float = Field(ge=0, le=100)
    risk_adjusted_score: float = Field(ge=0, le=100)
    safety_passed: bool
    fundamental_score: Optional[float] = None
    technical_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    sub_scores: Optional[dict] = None
    disclaimer: str = DISCLAIMER
