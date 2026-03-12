"""SignalFusion router -- consensus signal via DDD handler.

GET /api/v1/signals/{ticker} -- returns signal with per-strategy votes.

LEGAL BOUNDARY: Response deliberately EXCLUDES:
  - margin_of_safety (investment advice indicator)
  - reasoning_trace (contains "BUY"/"SELL" recommendation language)
  - Any position sizing, stop-loss, or take-profit references

Direction uses informational language: "Bullish"/"Bearish"/"Neutral"
(not action language: "BUY"/"SELL"/"HOLD").
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from commercial.api.dependencies import get_current_user, get_signal_handler
from commercial.api.middleware.rate_limit import get_tier_limit, limiter
from commercial.api.schemas.common import DISCLAIMER
from commercial.api.schemas.signal import MethodologyVote, SignalResponse
from src.shared.domain import Err
from src.signals.application.commands import GenerateSignalCommand

router = APIRouter(prefix="/signals", tags=["SignalFusion"])

# Map handler action language to API informational language
_DIRECTION_MAP: dict[str, str] = {
    "BUY": "Bullish",
    "SELL": "Bearish",
    "HOLD": "Neutral",
}


@router.get("/{ticker}", response_model=SignalResponse)
@limiter.limit(get_tier_limit)
def get_signal(
    request: Request,
    ticker: str,
    user: dict = Depends(get_current_user),
    handler=Depends(get_signal_handler),
):
    """Return consensus signal for a ticker with per-methodology votes."""
    result = handler.handle(GenerateSignalCommand(symbol=ticker))

    if isinstance(result, Err):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(result.error),
        )

    data = result.value

    # Map direction: BUY -> Bullish, SELL -> Bearish, HOLD -> Neutral
    direction = _DIRECTION_MAP.get(data["direction"], "Neutral")

    # Build methodology_votes from handler's methodology_scores and methodology_directions
    methodology_votes = []
    scores = data.get("methodology_scores", {})
    directions = data.get("methodology_directions", {})
    for method_name in scores:
        raw_dir = directions.get(method_name, "HOLD")
        vote_direction = _DIRECTION_MAP.get(raw_dir, "Neutral")
        methodology_votes.append(
            MethodologyVote(
                name=method_name,
                direction=vote_direction,
                score=scores[method_name],
            )
        )

    # Map strength: handler returns 0-100 float or "STRONG"/"MODERATE"/"WEAK" string
    # SignalResponse.strength expects float 0-1
    strength_raw = data.get("strength", "MODERATE")
    if isinstance(strength_raw, (int, float)):
        strength_val = min(1.0, max(0.0, float(strength_raw) / 100.0))
    else:
        strength_map = {"STRONG": 0.9, "MODERATE": 0.5, "WEAK": 0.2}
        strength_val = strength_map.get(str(strength_raw).upper(), 0.5)

    return SignalResponse(
        symbol=data["symbol"],
        direction=direction,
        strength=strength_val,
        consensus_count=data["consensus_count"],
        methodology_count=data["methodology_count"],
        methodology_scores=scores,
        methodology_votes=methodology_votes,
        regime_type=data.get("regime_type"),
        disclaimer=DISCLAIMER,
    )
