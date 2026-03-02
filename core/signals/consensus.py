"""Signal consensus: combine 4 strategies with regime-based weighting."""
from .canslim import evaluate as canslim_eval
from .magic_formula import evaluate as magic_eval
from .dual_momentum import evaluate as dual_eval
from .trend_following import evaluate as trend_eval
from core.regime.weights import get_weights


def compute_consensus(
    canslim_result: dict,
    magic_result: dict,
    dual_result: dict,
    trend_result: dict,
    regime: str = "Transition",
) -> dict:
    """
    Combine 4 strategy signals into consensus.
    3/4 BUY -> BULLISH, 3/4 SELL -> BEARISH, else NEUTRAL.
    Also compute regime-weighted score.
    """
    signals = [
        canslim_result["signal"],
        magic_result["signal"],
        dual_result["signal"],
        trend_result["signal"],
    ]
    buy_count = signals.count("BUY")
    sell_count = signals.count("SELL")

    if buy_count >= 3:
        consensus = "BULLISH"
    elif sell_count >= 3:
        consensus = "BEARISH"
    else:
        consensus = "NEUTRAL"

    # Regime-weighted score (normalize each signal score to 0-1, then weight)
    weights = get_weights(regime)

    def normalize(result: dict) -> float:
        s = result["score"]
        mx = result.get("score_max", 1)
        return s / mx if mx > 0 else 0.5

    weighted_score = (
        weights["canslim"] * normalize(canslim_result)
        + weights["magic"] * normalize(magic_result)
        + weights["momentum"] * normalize(dual_result)
        + weights["trend"] * normalize(trend_result)
    )

    return {
        "consensus": consensus,
        "agreement": buy_count if consensus == "BULLISH" else sell_count,
        "regime_context": regime,
        "methods": {
            "canslim": {"signal": canslim_result["signal"], "score": canslim_result["score"], "score_max": canslim_result["score_max"]},
            "magic_formula": {"signal": magic_result["signal"], "score": magic_result["score"], "score_max": magic_result["score_max"]},
            "dual_momentum": {"signal": dual_result["signal"], "score": dual_result["score"], "score_max": dual_result["score_max"]},
            "trend_following": {"signal": trend_result["signal"], "score": trend_result["score"], "score_max": trend_result["score_max"]},
        },
        "weighted_score": round(weighted_score, 3),
    }


def generate_signals(symbol: str, data: dict, regime: str = "Transition") -> dict:
    """
    Full signal pipeline for a symbol.
    data: dict with keys from DataClient.get_full() plus additional fields.
    """
    ind = data.get("indicators", {})
    price = data.get("price", {})
    fund = data.get("fundamentals", {}).get("highlights", {})

    close = price.get("close", 0)
    ma50 = ind.get("ma50", 0) or 0
    ma200 = ind.get("ma200", 0) or 0
    adx = ind.get("adx14", 15) or 15

    canslim = canslim_eval(
        eps_growth_qoq=None,
        eps_cagr_3y=None,
        near_52w_high=data.get("near_52w_high", False),
        volume_ratio=data.get("volume_ratio", 1.0),
        relative_strength=data.get("relative_strength", 50),
        institutional_increase=False,
        market_uptrend=(regime in ("Low-Vol Bull", "High-Vol Bull")),
    )

    magic = magic_eval(
        earnings_yield=data.get("earnings_yield"),
        return_on_capital=data.get("return_on_capital"),
        ey_percentile=data.get("ey_percentile", 50),
        roc_percentile=data.get("roc_percentile", 50),
    )

    dual = dual_eval(
        return_12m=data.get("return_12m"),
        return_12m_benchmark=data.get("return_12m_benchmark"),
    )

    trend = trend_eval(
        above_ma50=close > ma50 if ma50 else False,
        above_ma200=close > ma200 if ma200 else False,
        adx=adx,
        at_20d_high=data.get("at_20d_high", False),
    )

    consensus = compute_consensus(canslim, magic, dual, trend, regime)

    return {
        "skill": "signal-generate",
        "status": "success",
        "symbol": symbol,
        **consensus,
    }
