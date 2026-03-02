"""Regime endpoint -- RegimeRadar API."""
from fastapi import APIRouter, HTTPException
from ..models import RegimeResponse

router = APIRouter()


@router.get("/regime", response_model=RegimeResponse)
async def get_regime():
    """Return current market regime."""
    try:
        from core.data.market import get_vix, get_sp500_vs_200ma, get_yield_curve_slope
        from core.regime.classifier import classify
        from core.regime.weights import get_weights, get_risk_adjustment

        vix = get_vix()
        sp500 = get_sp500_vs_200ma()
        slope = get_yield_curve_slope()
        regime_result = classify(vix, sp500, 20.0, slope)
        regime = regime_result.get("regime", "Transition")
        weights = get_weights(regime)
        risk_adj = get_risk_adjustment(regime)

        return RegimeResponse(
            regime=regime,
            confidence=regime_result.get("confidence", 0.5),
            vix=vix,
            sp500_vs_200ma=sp500,
            adx=20.0,
            strategy_weights=weights,
            risk_adjustment=risk_adj,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"레짐 감지 실패: {str(e)}")
