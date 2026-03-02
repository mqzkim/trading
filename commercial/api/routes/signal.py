"""Signal endpoint -- SignalFusion API."""
from fastapi import APIRouter, HTTPException
from ..models import SignalResponse

router = APIRouter()


@router.get("/signal/{symbol}", response_model=SignalResponse)
async def get_signal(symbol: str):
    """Return 4-strategy consensus signal for a symbol."""
    symbol = symbol.upper()
    try:
        from core.data.client import DataClient
        from core.signals.consensus import generate_signals
        from core.data.market import get_vix, get_sp500_vs_200ma, get_yield_curve_slope
        from core.regime.classifier import classify

        client = DataClient()
        data = client.get_full(symbol)

        vix = get_vix()
        sp500 = get_sp500_vs_200ma()
        slope = get_yield_curve_slope()
        adx = data.get("indicators", {}).get("adx14", 20.0)
        regime_result = classify(vix, sp500, adx, slope)
        regime = regime_result.get("regime", "Transition")

        result = generate_signals(symbol, data, regime)

        return SignalResponse(
            symbol=symbol,
            consensus=result.get("consensus", "NEUTRAL"),
            agreement=result.get("agreement", 0),
            methods=result.get("methods", {}),
            regime=regime,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"시그널 생성 실패: {str(e)}")
