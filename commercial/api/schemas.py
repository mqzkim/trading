"""API Schemas -- Pydantic 모델."""
from pydantic import BaseModel, Field
from typing import Optional

DISCLAIMER = "이 정보는 투자 참고용 데이터입니다. 투자 권고나 자문이 아닙니다. 투자 결정은 본인 책임입니다."


class ScoreResponse(BaseModel):
    symbol: str
    safety_passed: bool
    composite_score: float = Field(ge=0, le=100)
    risk_adjusted_score: float = Field(ge=0, le=100)
    strategy: str
    fundamental_score: Optional[float] = None
    technical_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    f_score: Optional[int] = None
    z_score: Optional[float] = None
    m_score: Optional[float] = None
    disclaimer: str = DISCLAIMER


class RegimeResponse(BaseModel):
    regime_type: str
    vix: Optional[float] = None
    adx: Optional[float] = None
    yield_spread: Optional[float] = None
    detected_at: Optional[str] = None
    disclaimer: str = DISCLAIMER


class BatchScoreRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=20)
    strategy: str = "swing"


class BatchScoreResponse(BaseModel):
    results: list[ScoreResponse]
    total: int
    disclaimer: str = DISCLAIMER
