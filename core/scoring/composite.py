"""Composite score: weighted sum of fundamental, technical, sentiment."""

# Strategy regime weights
WEIGHTS = {
    "swing": {"fundamental": 0.35, "technical": 0.40, "sentiment": 0.25},
    "position": {"fundamental": 0.50, "technical": 0.30, "sentiment": 0.20},
}
DEFAULT_STRATEGY = "swing"


def compute_composite(
    fundamental_score: float,
    technical_score: float,
    sentiment_score: float,
    strategy: str = DEFAULT_STRATEGY,
    tail_risk_penalty: float = 0.0,
) -> dict:
    """
    Compute composite score (0-100).
    tail_risk_penalty: additional deduction for tail risk (0-100 scale).
    """
    w = WEIGHTS.get(strategy, WEIGHTS[DEFAULT_STRATEGY])

    raw = (
        w["fundamental"] * fundamental_score
        + w["technical"] * technical_score
        + w["sentiment"] * sentiment_score
    )
    raw = max(0.0, min(100.0, raw))

    risk_adjusted = raw - 0.3 * tail_risk_penalty
    risk_adjusted = max(0.0, min(100.0, risk_adjusted))

    return {
        "composite_score": round(raw, 1),
        "risk_adjusted_score": round(risk_adjusted, 1),
        "weights": w,
        "strategy": strategy,
    }


def score_symbol(
    symbol: str,
    fundamental_result: dict,
    technical_result: dict,
    sentiment_result: dict,
    strategy: str = DEFAULT_STRATEGY,
) -> dict:
    """
    Full scoring pipeline for a single symbol.
    Applies safety gate: if not passed, returns zero scores.
    """
    if not fundamental_result.get("safety_passed", False):
        return {
            "symbol": symbol,
            "safety_passed": False,
            "composite_score": 0,
            "risk_adjusted_score": 0,
            "z_score": fundamental_result.get("z_score"),
            "m_score": fundamental_result.get("m_score"),
            "fundamental_score": 0,
            "technical_score": technical_result.get("technical_score", 0),
            "sentiment_score": sentiment_result.get("sentiment_score", 50),
        }

    composite = compute_composite(
        fundamental_result["fundamental_score"],
        technical_result["technical_score"],
        sentiment_result["sentiment_score"],
        strategy=strategy,
    )

    return {
        "symbol": symbol,
        "safety_passed": True,
        **composite,
        "fundamental_score": fundamental_result["fundamental_score"],
        "technical_score": technical_result["technical_score"],
        "sentiment_score": sentiment_result["sentiment_score"],
        "f_score": fundamental_result.get("f_score"),
        "z_score": fundamental_result.get("z_score"),
        "m_score": fundamental_result.get("m_score"),
    }
