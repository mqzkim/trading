"""9-layer trading pipeline orchestrator.

Combines all core and personal modules into a single analysis pipeline:
  1. Data fetch (DataClient)
  2. Technical indicators (compute_all)
  3. Market indicators (VIX, SP500 vs 200MA, yield curve)
  4. Regime classification
  5. Signal generation (4-strategy consensus)
  6. Composite scoring
  7. Entry permission check
  8. Position sizing (ATR-based)
  9. Entry plan generation
"""
from dataclasses import dataclass, field
from typing import Optional

from core.data.client import DataClient
from core.data.market import get_vix, get_sp500_vs_200ma, get_yield_curve_slope
from core.regime.classifier import classify
from core.regime.weights import get_weights, get_risk_adjustment
from core.signals.consensus import generate_signals
from core.scoring.composite import score_symbol
from personal.sizer.kelly import atr_position_size, validate_position
from personal.risk.manager import full_risk_check, check_entry_allowed
from personal.execution.planner import plan_entry


@dataclass
class PipelineResult:
    symbol: str
    regime: str
    regime_confidence: float
    consensus: str          # BULLISH / BEARISH / NEUTRAL
    agreement: int          # 0~4
    composite_score: float
    safety_passed: bool
    position_shares: int
    position_value: float
    risk_level: int         # 0~3 (drawdown defense level)
    entry_plan: dict
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None


def run_full_pipeline(
    symbol: str,
    capital: float = 100_000.0,
    strategy: str = "swing",
    peak_value: float | None = None,
    current_value: float | None = None,
) -> PipelineResult:
    """
    Execute the full 9-layer analysis pipeline for a single symbol.

    Args:
        symbol: Ticker symbol (e.g. "AAPL")
        capital: Total portfolio capital
        strategy: "swing" or "position"
        peak_value: Portfolio peak value for drawdown calc (defaults to capital)
        current_value: Portfolio current value (defaults to capital)

    Returns:
        PipelineResult with all analysis results
    """
    if peak_value is None:
        peak_value = capital
    if current_value is None:
        current_value = capital

    warnings: list[str] = []

    # --- Layer 1: Data Fetch ---
    try:
        client = DataClient()
        data = client.get_full(symbol)
    except Exception as e:
        return PipelineResult(
            symbol=symbol, regime="Unknown", regime_confidence=0.0,
            consensus="NEUTRAL", agreement=0, composite_score=0.0,
            safety_passed=False, position_shares=0, position_value=0.0,
            risk_level=0, entry_plan={},
            error=f"Data fetch failed: {e}",
        )

    price = data.get("price", {})
    indicators = data.get("indicators", {})
    close = price.get("close", 0.0)
    atr_val = indicators.get("atr21", 0.0) or 0.0
    adx_val = indicators.get("adx14", 15.0) or 15.0

    # --- Layer 2-3: Market Indicators + Regime ---
    try:
        vix = get_vix()
        sp500_ratio = get_sp500_vs_200ma()
        yield_curve = get_yield_curve_slope()
    except Exception as e:
        warnings.append(f"Market indicators failed: {e}")
        vix, sp500_ratio, yield_curve = 18.0, 1.02, 50.0

    try:
        regime_result = classify(vix, sp500_ratio, adx_val, yield_curve)
    except Exception as e:
        warnings.append(f"Regime classification failed: {e}")
        regime_result = {"regime": "Transition", "confidence": 0.5, "warning": None}

    regime = regime_result["regime"]
    regime_confidence = regime_result["confidence"]
    if regime_result.get("warning"):
        warnings.append(regime_result["warning"])

    # --- Layer 4: Signal Generation (4-strategy consensus) ---
    try:
        signal_result = generate_signals(symbol, data, regime)
        consensus = signal_result.get("consensus", "NEUTRAL")
        agreement = signal_result.get("agreement", 0)
    except Exception as e:
        warnings.append(f"Signal generation failed: {e}")
        consensus = "NEUTRAL"
        agreement = 0
        signal_result = {}

    # --- Layer 5: Composite Scoring ---
    # Build minimal sub-results for score_symbol
    # score_symbol expects fundamental_result, technical_result, sentiment_result
    try:
        fund = data.get("fundamentals", {}).get("highlights", {})
        fundamental_result = {
            "safety_passed": True,  # placeholder — full safety requires Z/M scores
            "fundamental_score": _estimate_fundamental_score(fund),
            "z_score": None,
            "m_score": None,
            "f_score": None,
        }
        technical_result = {
            "technical_score": _estimate_technical_score(indicators, close),
        }
        sentiment_result = {
            "sentiment_score": 50.0,  # neutral default
        }
        score_result = score_symbol(
            symbol, fundamental_result, technical_result, sentiment_result, strategy
        )
        composite_score = score_result.get("composite_score", 0.0)
        safety_passed = score_result.get("safety_passed", False)
    except Exception as e:
        warnings.append(f"Scoring failed: {e}")
        composite_score = 0.0
        safety_passed = False
        score_result = {}

    # --- Layer 6: Entry Permission ---
    try:
        entry_allowed = check_entry_allowed(peak_value, current_value)
        risk_level = entry_allowed.get("drawdown_level", 0)
        if not entry_allowed["allowed"]:
            warnings.append(f"Entry blocked: {entry_allowed['reason']}")
    except Exception as e:
        warnings.append(f"Entry check failed: {e}")
        risk_level = 0
        entry_allowed = {"allowed": True, "drawdown_level": 0}

    # --- Layer 7-8: Position Sizing + Entry Plan ---
    position_shares = 0
    position_value = 0.0
    entry_plan: dict = {}

    if entry_allowed["allowed"] and close > 0 and atr_val > 0:
        try:
            risk_adj = get_risk_adjustment(regime)
            adjusted_capital = capital * risk_adj

            sizing = atr_position_size(adjusted_capital, close, atr_val)
            position_shares = sizing.get("shares", 0)
            position_value = sizing.get("position_value", 0.0)

            # Validate position
            pos_check = validate_position(position_value, capital)
            if not pos_check["passed"]:
                warnings.extend(pos_check["violations"])

            # Generate entry plan
            entry_plan = plan_entry(
                symbol=symbol,
                entry_price=close,
                atr=atr_val,
                capital=adjusted_capital,
                peak_value=peak_value,
                current_value=current_value,
            )
            if entry_plan.get("status") == "REJECTED":
                warnings.append(f"Entry plan rejected: {entry_plan.get('violations', [])}")
        except Exception as e:
            warnings.append(f"Position sizing failed: {e}")
    elif close <= 0 or atr_val <= 0:
        warnings.append("Cannot size position: missing price or ATR data")

    return PipelineResult(
        symbol=symbol,
        regime=regime,
        regime_confidence=regime_confidence,
        consensus=consensus,
        agreement=agreement,
        composite_score=composite_score,
        safety_passed=safety_passed,
        position_shares=position_shares,
        position_value=position_value,
        risk_level=risk_level,
        entry_plan=entry_plan,
        warnings=warnings,
    )


def run_quick_scan(
    symbols: list[str],
    capital: float = 100_000.0,
    strategy: str = "swing",
) -> dict[str, dict]:
    """
    Quick scan: data fetch + scoring only (no position sizing or risk checks).
    Much faster than full pipeline.

    Returns:
        dict mapping symbol -> {score, safety_passed, regime}
    """
    results: dict[str, dict] = {}
    client = DataClient()

    # Get regime once for all symbols
    try:
        vix = get_vix()
        sp500_ratio = get_sp500_vs_200ma()
        yield_curve = get_yield_curve_slope()
    except Exception:
        vix, sp500_ratio, yield_curve = 18.0, 1.02, 50.0

    for sym in symbols:
        try:
            data = client.get_full(sym)
            indicators = data.get("indicators", {})
            price = data.get("price", {})
            close = price.get("close", 0.0)
            adx_val = indicators.get("adx14", 15.0) or 15.0

            regime_result = classify(vix, sp500_ratio, adx_val, yield_curve)
            regime = regime_result["regime"]

            fund = data.get("fundamentals", {}).get("highlights", {})
            fundamental_result = {
                "safety_passed": True,
                "fundamental_score": _estimate_fundamental_score(fund),
            }
            technical_result = {
                "technical_score": _estimate_technical_score(indicators, close),
            }
            sentiment_result = {"sentiment_score": 50.0}

            score_result = score_symbol(
                sym, fundamental_result, technical_result, sentiment_result, strategy
            )

            results[sym] = {
                "score": score_result.get("composite_score", 0.0),
                "risk_adjusted_score": score_result.get("risk_adjusted_score", 0.0),
                "safety_passed": score_result.get("safety_passed", False),
                "regime": regime,
            }
        except Exception as e:
            results[sym] = {
                "score": 0.0,
                "risk_adjusted_score": 0.0,
                "safety_passed": False,
                "regime": "Unknown",
                "error": str(e),
            }

    return results


# --- Internal helpers ---

def _estimate_fundamental_score(highlights: dict) -> float:
    """Rough fundamental score (0-100) from available highlights data."""
    score = 50.0  # neutral baseline
    roe = highlights.get("roe")
    pe = highlights.get("pe_ratio")
    current_ratio = highlights.get("current_ratio")

    if roe is not None:
        if roe > 0.15:
            score += 15
        elif roe > 0.10:
            score += 8
        elif roe < 0:
            score -= 15

    if pe is not None:
        if 0 < pe < 15:
            score += 10
        elif 15 <= pe < 25:
            score += 5
        elif pe > 40:
            score -= 10

    if current_ratio is not None:
        if current_ratio > 1.5:
            score += 5
        elif current_ratio < 1.0:
            score -= 10

    return max(0.0, min(100.0, score))


def _estimate_technical_score(indicators: dict, close: float) -> float:
    """Rough technical score (0-100) from indicator values."""
    score = 50.0  # neutral baseline
    ma50 = indicators.get("ma50", 0) or 0
    ma200 = indicators.get("ma200", 0) or 0
    rsi = indicators.get("rsi14", 50) or 50
    macd_hist = indicators.get("macd_histogram", 0) or 0

    if close > 0:
        if ma50 > 0 and close > ma50:
            score += 10
        if ma200 > 0 and close > ma200:
            score += 10
        if ma50 > 0 and close < ma50:
            score -= 10
        if ma200 > 0 and close < ma200:
            score -= 10

    if rsi > 70:
        score -= 5   # overbought
    elif rsi < 30:
        score += 10  # oversold bounce potential
    elif 50 <= rsi <= 70:
        score += 5

    if macd_hist > 0:
        score += 5
    elif macd_hist < 0:
        score -= 5

    return max(0.0, min(100.0, score))
