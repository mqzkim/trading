"""Technical scoring: trend, momentum, volume (0-100)."""
import math
import pandas as pd


def _safe_last(s: "pd.Series") -> float:
    v = s.dropna()
    return float(v.iloc[-1]) if len(v) > 0 else float("nan")


def _norm(v: float, lo: float, hi: float) -> float:
    """Normalize v to [0, 100] between lo and hi."""
    if hi == lo:
        return 50.0
    return max(0.0, min(100.0, (v - lo) / (hi - lo) * 100))


def compute_technical_score(df: pd.DataFrame, indicators: dict) -> dict:
    """
    Compute technical sub-scores from OHLCV DataFrame and pre-computed indicators.
    indicators: output of core.data.indicators.compute_all(df)
    Returns dict with trend_score, momentum_score, volume_score, technical_score.
    """
    close = df["close"]
    current_close = float(close.iloc[-1])

    # --- Trend score (0-100) ---
    ma50 = _safe_last(indicators["ma50"])
    ma200 = _safe_last(indicators["ma200"])
    adx14 = _safe_last(indicators["adx14"])
    macd_hist = _safe_last(indicators["macd_histogram"])

    trend_points = 0
    # Price vs MA200 (40 pts)
    if not math.isnan(ma200) and current_close > ma200:
        trend_points += 40
    # Price vs MA50 (20 pts)
    if not math.isnan(ma50) and current_close > ma50:
        trend_points += 20
    # ADX strength (20 pts)
    if not math.isnan(adx14):
        trend_points += _norm(adx14, 10, 50) * 0.20
    # MACD direction (20 pts)
    if not math.isnan(macd_hist) and macd_hist > 0:
        trend_points += 20

    trend_score = min(100, trend_points)

    # --- Momentum score (0-100) ---
    rsi14 = _safe_last(indicators["rsi14"])
    if math.isnan(rsi14):
        momentum_score = 50.0
    else:
        # RSI 40-60 = neutral (50), >60 = bullish, <40 = bearish
        # RSI 70+ = overbought penalty
        if rsi14 > 70:
            momentum_score = 60 - (rsi14 - 70) * 2  # penalty for overbought
        elif rsi14 < 30:
            momentum_score = 40 + (30 - rsi14) * 1  # slight boost for oversold
        else:
            momentum_score = _norm(rsi14, 20, 80)

    # 12-1 month return (price momentum)
    n = len(close)
    if n >= 252:
        ret_12_1 = (float(close.iloc[-21]) - float(close.iloc[-252])) / float(close.iloc[-252])
        momentum_ret_score = _norm(ret_12_1, -0.30, 0.50)
        momentum_score = 0.5 * momentum_score + 0.5 * momentum_ret_score

    momentum_score = max(0, min(100, momentum_score))

    # --- Volume score (0-100) ---
    obv = indicators["obv"]
    # OBV trend: compare last 20 vs last 60 days
    if len(obv.dropna()) >= 60:
        obv_recent = float(obv.dropna().iloc[-1])
        obv_past = float(obv.dropna().iloc[-60])
        if obv_past != 0:
            obv_change = (obv_recent - obv_past) / abs(obv_past)
            volume_score = _norm(obv_change, -0.20, 0.20)
        else:
            volume_score = 50.0
    else:
        volume_score = 50.0

    # --- Composite (40% trend + 40% momentum + 20% volume) ---
    technical_score = 0.40 * trend_score + 0.40 * momentum_score + 0.20 * volume_score
    technical_score = max(0, min(100, technical_score))

    return {
        "trend_score": round(trend_score, 1),
        "momentum_score": round(momentum_score, 1),
        "volume_score": round(volume_score, 1),
        "technical_score": round(technical_score, 1),
        "rsi14": round(rsi14, 1) if not math.isnan(rsi14) else None,
        "adx14": round(adx14, 1) if not math.isnan(adx14) else None,
        "above_ma200": not math.isnan(ma200) and current_close > ma200,
    }
