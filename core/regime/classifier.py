"""Rule-based market regime classifier.

Uses 4 indicators:
  - VIX level
  - S&P 500 vs 200-day MA ratio
  - ADX (trend strength)
  - Yield curve slope (bps)
"""
import math

REGIMES = ["Low-Vol Bull", "High-Vol Bull", "Low-Vol Range", "High-Vol Bear", "Transition"]

def classify(
    vix: float,
    sp500_vs_200ma: float,  # ratio: close / MA200
    adx: float,
    yield_curve_bps: float,
) -> dict:
    """
    Returns dict with 'regime', 'confidence', 'probabilities', 'warning'.
    Rules are deterministic (rule-based, no ML).
    """
    above_200ma = sp500_vs_200ma > 1.0
    strong_trend = adx > 25
    high_vol = vix > 20
    extreme_vol = vix > 30
    inverted_curve = yield_curve_bps < 0

    # --- Hard classification ---
    if extreme_vol and not above_200ma and strong_trend:
        regime = "High-Vol Bear"
        confidence = 0.85
    elif high_vol and not above_200ma:
        regime = "High-Vol Bear"
        confidence = 0.70
    elif high_vol and above_200ma and strong_trend:
        regime = "High-Vol Bull"
        confidence = 0.72
    elif not high_vol and above_200ma and strong_trend:
        regime = "Low-Vol Bull"
        confidence = 0.80
    elif not high_vol and not strong_trend:
        regime = "Low-Vol Range"
        confidence = 0.65
    else:
        regime = "Transition"
        confidence = 0.50

    # Reduce confidence if yield curve is inverted (recessionary signal)
    if inverted_curve and regime in ("Low-Vol Bull", "High-Vol Bull"):
        confidence = max(confidence - 0.15, 0.40)
        if confidence < 0.55:
            regime = "Transition"

    # Build probability distribution (rough approximation)
    probs = {r: 0.0 for r in REGIMES}
    probs[regime] = confidence
    remaining = 1.0 - confidence
    others = [r for r in REGIMES if r != regime]
    for r in others:
        probs[r] = round(remaining / len(others), 3)
    probs[regime] = round(confidence, 3)

    warning = None
    if regime == "High-Vol Bear":
        warning = "HIGH_VOL_BEAR: 신규 진입 중단 권고, 방어적 전환"
    elif regime == "Transition":
        warning = "TRANSITION: 포지션 축소, 높은 불확실성"
    elif vix > 30:
        warning = "EXTREME_FEAR: VIX > 30 극단적 공포"

    return {
        "regime": regime,
        "confidence": confidence,
        "probabilities": probs,
        "indicators": {
            "vix": vix,
            "sp500_vs_200ma": sp500_vs_200ma,
            "adx": adx,
            "yield_curve_bps": yield_curve_bps,
        },
        "warning": warning,
    }
