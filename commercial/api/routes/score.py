"""Score endpoint -- QuantScore API."""
from fastapi import APIRouter, HTTPException
from ..models import ScoreResponse

router = APIRouter()


@router.get("/score/{symbol}", response_model=ScoreResponse)
async def get_score(symbol: str):
    """Return composite score (0-100) for a symbol."""
    symbol = symbol.upper()
    try:
        from core.data.client import DataClient
        from core.scoring.composite import score_symbol
        from core.scoring.safety import check_safety
        from core.regime.classifier import classify
        from core.data.market import get_vix, get_sp500_vs_200ma, get_yield_curve_slope

        client = DataClient()
        data = client.get_full(symbol)

        # Regime detection
        vix = get_vix()
        sp500 = get_sp500_vs_200ma()
        slope = get_yield_curve_slope()
        adx = data.get("indicators", {}).get("adx14", 20.0)
        regime_result = classify(vix, sp500, adx, slope)
        regime = regime_result.get("regime", "Transition")

        # Safety check (z_score, m_score)
        fund = data.get("fundamentals", {}).get("highlights", {})
        z_score = fund.get("z_score", 2.5) if fund.get("z_score") is not None else 2.5
        m_score = fund.get("m_score", -2.0) if fund.get("m_score") is not None else -2.0
        safety = check_safety(z_score, m_score)
        safety_passed = safety.get("safety_passed", False)

        # Build sub-results matching score_symbol signature
        fund_result = {
            "fundamental_score": 50.0,
            "safety_passed": safety_passed,
            "f_score": 5,
            "z_score": z_score,
            "m_score": m_score,
        }
        tech_result = {"technical_score": 50.0, "trend": "neutral", "momentum_pct": 50}
        sent_result = {"sentiment_score": 50.0}

        result = score_symbol(symbol, fund_result, tech_result, sent_result)

        return ScoreResponse(
            symbol=symbol,
            composite_score=round(result.get("composite_score", 50.0), 2),
            safety_passed=safety_passed,
            fundamental_score=fund_result.get("fundamental_score"),
            technical_score=tech_result.get("technical_score"),
            sentiment_score=sent_result.get("sentiment_score"),
            regime=regime,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"데이터 수집 실패: {str(e)}")
