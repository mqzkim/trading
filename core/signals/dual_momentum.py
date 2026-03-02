"""Dual Momentum signal -- Antonacci's absolute + relative momentum."""

def evaluate(
    return_12m: float | None,      # 12-month return of asset
    return_12m_benchmark: float | None,  # 12-month return of benchmark (S&P 500)
    tbill_rate: float = 0.04,      # risk-free rate (annualized)
) -> dict:
    """
    Dual Momentum:
      Relative: asset 12m return > benchmark 12m return -> positive relative momentum
      Absolute: asset 12m return > T-bill rate -> positive absolute momentum
      BUY only if BOTH pass.
    """
    ret = return_12m or 0.0
    bench = return_12m_benchmark or 0.0

    relative_pass = ret > bench
    absolute_pass = ret > tbill_rate

    if relative_pass and absolute_pass:
        signal = "BUY"
        confidence = 0.80
    elif not absolute_pass:
        signal = "SELL"   # absolute momentum fail = go to safety
        confidence = 0.75
    else:
        signal = "HOLD"
        confidence = 0.50

    return {
        "methodology": "Dual Momentum",
        "signal": signal,
        "score": int(relative_pass) + int(absolute_pass),
        "score_max": 2,
        "confidence": confidence,
        "relative_pass": relative_pass,
        "absolute_pass": absolute_pass,
        "return_12m": ret,
    }
