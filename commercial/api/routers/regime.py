"""RegimeRadar router -- market regime detection via DDD handler.

GET /api/v1/regime/current  -- current regime with confidence
GET /api/v1/regime/history  -- regime transitions over a period
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from commercial.api.dependencies import get_context, get_current_user, get_regime_handler
from commercial.api.middleware.rate_limit import get_tier_limit, limiter
from commercial.api.schemas.common import DISCLAIMER
from commercial.api.schemas.regime import (
    RegimeCurrentResponse,
    RegimeHistoryEntry,
    RegimeHistoryResponse,
)
from src.regime.application.commands import DetectRegimeCommand
from src.shared.domain import Err

router = APIRouter(prefix="/regime", tags=["RegimeRadar"])


def _compute_regime_probabilities(regime_type: str, confidence: float) -> dict[str, float]:
    """Compute approximate probability distribution from dominant regime + confidence."""
    regimes = ["Bull", "Bear", "Sideways", "Crisis"]
    remaining = 1.0 - confidence
    per_other = remaining / (len(regimes) - 1) if len(regimes) > 1 else 0.0
    probs = {r: round(per_other, 4) for r in regimes}
    probs[regime_type] = round(confidence, 4)
    return probs


@router.get("/current", response_model=RegimeCurrentResponse)
@limiter.limit(get_tier_limit)
def get_current_regime(
    request: Request,
    user: dict = Depends(get_current_user),
    handler=Depends(get_regime_handler),
):
    """Return current market regime with confidence and data points."""
    # Use sentinel zeros to trigger handler auto-fetch (same pattern as CLI)
    result = handler.handle(
        DetectRegimeCommand(vix=0, sp500_price=0, sp500_ma200=0, adx=0, yield_spread=0)
    )

    if isinstance(result, Err):
        # Fallback: try reading latest from repo
        latest = handler._regime_repo.find_latest()
        if latest is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No regime data available",
            )
        return RegimeCurrentResponse(
            regime_type=latest.regime_type.value,
            confidence=latest.confidence,
            is_confirmed=latest.is_confirmed,
            confirmed_days=latest.confirmed_days,
            vix=latest.vix.value,
            adx=latest.trend.adx,
            yield_spread=latest.yield_curve.spread,
            detected_at=latest.detected_at.isoformat(),
            regime_probabilities=_compute_regime_probabilities(
                latest.regime_type.value, latest.confidence
            ),
            disclaimer=DISCLAIMER,
        )

    data = result.value
    return RegimeCurrentResponse(
        regime_type=data["regime_type"],
        confidence=data["confidence"],
        is_confirmed=data["is_confirmed"],
        confirmed_days=data["confirmed_days"],
        vix=data.get("vix"),
        adx=data.get("adx"),
        yield_spread=data.get("yield_spread"),
        detected_at=data.get("detected_at"),
        regime_probabilities=_compute_regime_probabilities(
            data["regime_type"], data["confidence"]
        ),
        disclaimer=DISCLAIMER,
    )


@router.get("/history", response_model=RegimeHistoryResponse)
@limiter.limit(get_tier_limit)
def get_regime_history(
    request: Request,
    days: int = Query(default=90, ge=1, le=365),
    user: dict = Depends(get_current_user),
    context: dict = Depends(get_context),
):
    """Return regime transitions for a given period."""
    regime_handler = context["regime_handler"]
    repo = regime_handler._regime_repo

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    regimes = repo.find_by_date_range(start, end)

    entries = [
        RegimeHistoryEntry(
            regime_type=r.regime_type.value,
            confidence=r.confidence,
            is_confirmed=r.is_confirmed,
            detected_at=r.detected_at.isoformat(),
        )
        for r in regimes
    ]

    return RegimeHistoryResponse(
        entries=entries,
        total=len(entries),
        period_days=days,
        disclaimer=DISCLAIMER,
    )
