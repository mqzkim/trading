"""Trend Following signal -- MA cross, ADX, breakout."""

def evaluate(
    above_ma50: bool = False,
    above_ma200: bool = False,
    adx: float = 15.0,
    at_20d_high: bool = False,
) -> dict:
    """
    3 criteria:
      1. MA Cross: price > MA50 AND MA50 trend (proxy: above_ma50 and above_ma200)
      2. ADX > 25 (trend strength)
      3. 20-day high breakout
    BUY if 2+ criteria pass.
    """
    criteria = {
        "ma_cross": above_ma50 and above_ma200,
        "adx_strength": adx > 25,
        "breakout": at_20d_high,
    }
    score = sum(criteria.values())

    if score >= 2:
        signal = "BUY"
        confidence = 0.70 + (score - 2) * 0.10
    else:
        signal = "HOLD" if score == 1 else "SELL"
        confidence = 0.55

    return {
        "methodology": "Trend Following",
        "signal": signal,
        "score": score,
        "score_max": 3,
        "confidence": min(confidence, 0.90),
        "criteria": criteria,
    }
