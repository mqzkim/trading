"""Request/response models for Commercial API."""
from pydantic import BaseModel, Field
from typing import Optional

DISCLAIMER = "정보 제공 목적이며 투자 권유가 아닙니다. 투자 결정의 책임은 투자자에게 있습니다."


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"


class ScoreResponse(BaseModel):
    symbol: str
    composite_score: float = Field(ge=0, le=100)
    safety_passed: bool
    fundamental_score: Optional[float] = None
    technical_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    regime: str
    disclaimer: str = DISCLAIMER


class RegimeResponse(BaseModel):
    regime: str
    confidence: float = Field(ge=0, le=1)
    vix: Optional[float] = None
    sp500_vs_200ma: Optional[float] = None
    adx: Optional[float] = None
    strategy_weights: dict
    risk_adjustment: float
    disclaimer: str = DISCLAIMER


class SignalResponse(BaseModel):
    symbol: str
    consensus: str  # BULLISH / BEARISH / NEUTRAL
    agreement: int  # 0~4
    methods: dict  # canslim/magic_formula/dual_momentum/trend_following
    regime: str
    disclaimer: str = DISCLAIMER


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
