"""QuantScore router -- composite scoring via DDD handler.

GET /api/v1/quantscore/{ticker} -- returns score breakdown with disclaimer.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter

from commercial.api.dependencies import get_current_user, get_score_handler
from commercial.api.middleware.rate_limit import get_tier_limit, limiter
from commercial.api.schemas.common import DISCLAIMER
from commercial.api.schemas.score import QuantScoreResponse
from src.scoring.application.commands import ScoreSymbolCommand
from src.shared.domain import Err

router = APIRouter(prefix="/quantscore", tags=["QuantScore"])


@router.get("/{ticker}", response_model=QuantScoreResponse)
@limiter.limit(get_tier_limit)
def get_quantscore(
    request: Request,
    ticker: str,
    strategy: str = "swing",
    user: dict = Depends(get_current_user),
    handler=Depends(get_score_handler),
):
    """Return composite quantitative score for a ticker."""
    result = handler.handle(ScoreSymbolCommand(symbol=ticker, strategy=strategy))

    if isinstance(result, Err):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(result.error),
        )

    data = result.value

    # Build sub_scores from technical_sub_scores if present
    sub_scores = None
    if data.get("technical_sub_scores"):
        sub_scores = {
            s["name"]: {"value": s["value"], "explanation": s["explanation"], "raw_value": s["raw_value"]}
            for s in data["technical_sub_scores"]
        }

    return QuantScoreResponse(
        symbol=data["symbol"],
        composite_score=data["composite_score"],
        risk_adjusted_score=data.get("risk_adjusted_score", data["composite_score"]),
        safety_passed=data["safety_passed"],
        fundamental_score=data.get("fundamental_score"),
        technical_score=data.get("technical_score"),
        sentiment_score=data.get("sentiment_score"),
        sub_scores=sub_scores,
        disclaimer=DISCLAIMER,
    )
