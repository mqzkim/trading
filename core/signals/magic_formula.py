"""Magic Formula signal -- Earnings Yield + Return on Capital."""

def evaluate(
    earnings_yield: float | None,   # EBIT / Enterprise Value
    return_on_capital: float | None, # EBIT / (NWC + Net Fixed Assets)
    ey_percentile: float = 50.0,    # percentile rank within universe (0-100)
    roc_percentile: float = 50.0,   # percentile rank within universe (0-100)
) -> dict:
    """
    Magic Formula: rank on EY + ROC combined.
    Higher percentile = better rank.
    """
    # Combined rank: average of two percentile ranks
    combined_rank = (ey_percentile + roc_percentile) / 2

    if combined_rank >= 70:
        signal = "BUY"
        confidence = 0.75
    elif combined_rank >= 40:
        signal = "HOLD"
        confidence = 0.50
    else:
        signal = "SELL"
        confidence = 0.65

    return {
        "methodology": "Magic Formula",
        "signal": signal,
        "score": round(combined_rank, 1),
        "score_max": 100,
        "confidence": confidence,
        "earnings_yield": earnings_yield,
        "return_on_capital": return_on_capital,
        "combined_rank": round(combined_rank, 1),
    }
