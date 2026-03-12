"""RegimeRadar response schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .common import DISCLAIMER


class RegimeCurrentResponse(BaseModel):
    """Response for GET /api/v1/regime/current."""

    regime_type: str
    confidence: float = Field(ge=0, le=1)
    is_confirmed: bool
    confirmed_days: int
    vix: Optional[float] = None
    adx: Optional[float] = None
    yield_spread: Optional[float] = None
    detected_at: Optional[str] = None
    disclaimer: str = DISCLAIMER


class RegimeHistoryEntry(BaseModel):
    """Single entry in regime history."""

    regime_type: str
    confidence: float
    is_confirmed: bool
    detected_at: str


class RegimeHistoryResponse(BaseModel):
    """Response for GET /api/v1/regime/history."""

    entries: list[RegimeHistoryEntry]
    total: int
    period_days: int
    disclaimer: str = DISCLAIMER
