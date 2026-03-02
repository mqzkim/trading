"""CAN SLIM signal -- 7-criteria evaluation."""

def evaluate(
    eps_growth_qoq: float | None,   # C: quarterly EPS growth %
    eps_cagr_3y: float | None,      # A: 3-year EPS CAGR %
    near_52w_high: bool = False,    # N: near 52-week high
    volume_ratio: float = 1.0,      # S: recent vol / avg vol
    relative_strength: float = 50,  # L: RS percentile 0-100
    institutional_increase: bool = False,  # I: institutions increasing
    market_uptrend: bool = True,    # M: market in uptrend (from regime)
) -> dict:
    """
    Returns signal dict with score 0-7 and BUY/HOLD/SELL.
    """
    criteria = {
        "C": (eps_growth_qoq or 0) > 25,
        "A": (eps_cagr_3y or 0) > 25,
        "N": near_52w_high,
        "S": volume_ratio > 1.4,
        "L": relative_strength >= 80,
        "I": institutional_increase,
        "M": market_uptrend,
    }
    score = sum(criteria.values())

    if score >= 6:
        signal = "BUY"
        confidence = 0.85
    elif score >= 4:
        signal = "HOLD"
        confidence = 0.55
    else:
        signal = "SELL"
        confidence = 0.70

    return {
        "methodology": "CAN SLIM",
        "signal": signal,
        "score": score,
        "score_max": 7,
        "confidence": confidence,
        "criteria": criteria,
    }
