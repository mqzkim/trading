"""Regime 라우터."""
from fastapi import APIRouter, Depends, HTTPException
from ..schemas import RegimeResponse
from ..dependencies import verify_api_key, get_regime_repo

router = APIRouter(prefix="/v1/regime", tags=["Regime"])


@router.get("/current", response_model=RegimeResponse)
async def get_current_regime(
    _=Depends(verify_api_key),
    repo=Depends(get_regime_repo),
):
    latest = repo.find_latest()
    if latest is None:
        raise HTTPException(status_code=404, detail="No regime data available")
    return RegimeResponse(
        regime_type=latest.regime_type.value,
        vix=latest.vix.value,
        adx=latest.trend.adx,
        yield_spread=latest.yield_curve.spread,
        detected_at=latest.detected_at.isoformat(),
    )
