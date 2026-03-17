"""QuantScore response schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .common import DISCLAIMER


class SubScoreEntry(BaseModel):
    """Individual sub-score entry for technical/sentiment breakdown."""

    name: str
    value: Optional[float] = None  # 0-100 normalized, null if unavailable
    raw_value: Optional[float] = None


class QuantScoreResponse(BaseModel):
    """Response for GET /api/v1/quantscore/{ticker}."""

    symbol: str
    composite_score: float = Field(ge=0, le=100)
    risk_adjusted_score: float = Field(ge=0, le=100)
    safety_passed: bool
    fundamental_score: Optional[float] = None
    technical_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    sentiment_confidence: Optional[str] = None  # "NONE"/"LOW"/"MEDIUM"/"HIGH"
    sub_scores: Optional[dict] = None  # Keep for backward compat
    technical_sub_scores: Optional[list[SubScoreEntry]] = None
    sentiment_sub_scores: Optional[list[SubScoreEntry]] = None
    disclaimer: str = DISCLAIMER
