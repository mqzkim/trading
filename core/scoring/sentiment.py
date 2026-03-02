"""Sentiment scoring: analyst estimates, short interest proxies."""
import math


def compute_sentiment_score(
    pe_ratio: float | None = None,
    forward_pe: float | None = None,
    analyst_target: float | None = None,
    current_price: float | None = None,
    short_ratio: float | None = None,
) -> dict:
    """
    Compute sentiment score (0-100) from available proxy data.
    Uses analyst price target vs current price as primary signal.
    """
    score_components = []

    # Analyst target upside (primary signal, 60 pts weight)
    if analyst_target and current_price and current_price > 0:
        upside = (analyst_target - current_price) / current_price
        target_score = _norm(upside, -0.20, 0.40)
        score_components.append((target_score, 0.60))

    # Forward PE vs Trailing PE (earnings revision proxy, 20 pts weight)
    if pe_ratio and forward_pe and pe_ratio > 0:
        # Lower forward PE = improving earnings = bullish
        pe_ratio_val = forward_pe / pe_ratio
        pe_score = _norm(1 - (pe_ratio_val - 0.5), 0, 1)  # < 1 = improving
        score_components.append((pe_score, 0.20))

    # Short ratio (20 pts weight) -- lower = less bearish sentiment
    if short_ratio is not None and not math.isnan(short_ratio):
        short_score = _norm(short_ratio, 15, 0)  # inverted: lower ratio = better
        score_components.append((short_score, 0.20))

    if not score_components:
        return {"sentiment_score": 50.0, "note": "insufficient data, using neutral"}

    # Weighted average
    total_weight = sum(w for _, w in score_components)
    sentiment_score = sum(s * w for s, w in score_components) / total_weight
    sentiment_score = max(0, min(100, sentiment_score))

    return {
        "sentiment_score": round(sentiment_score, 1),
        "analyst_upside": round((analyst_target - current_price) / current_price * 100, 1)
            if analyst_target and current_price else None,
    }


def _norm(v: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 50.0
    return max(0.0, min(100.0, (v - lo) / (hi - lo) * 100))
