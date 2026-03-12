"""Scoring 도메인 — Domain Services.

CompositeScoringService: 3축 점수 -> 복합 점수 (G-Score 통합)
SafetyFilterService: 안전성 필터 판정
TechnicalScoringService: 5개 기술 지표 -> 개별 0-100 점수 + 설명 + 복합 기술 점수
RegimeWeightAdjuster: 레짐별 가중치 조정 프로토콜 (Phase 3 구현 대비)

참조: core/scoring/composite.py, core/scoring/safety.py (원본 로직)
"""
from __future__ import annotations

import math
from typing import Protocol

from .value_objects import (
    FundamentalScore,
    TechnicalScore,
    TechnicalIndicatorScore,
    SentimentScore,
    SafetyGate,
    CompositeScore,
    STRATEGY_WEIGHTS,
    DEFAULT_STRATEGY,
)


# 5개 기술 지표 가중치 (합계 = 1.0)
TECHNICAL_INDICATOR_WEIGHTS: dict[str, float] = {
    "rsi": 0.20,
    "macd": 0.20,
    "ma": 0.25,
    "adx": 0.15,
    "obv": 0.20,
}


class RegimeWeightAdjuster(Protocol):
    """레짐별 전략 가중치 조정 프로토콜.

    Phase 3에서 시장 레짐 감지와 함께 구체 구현 제공 예정.
    Phase 2에서는 NoOpRegimeAdjuster (기본값 그대로 반환)를 사용.
    """

    def adjust_weights(
        self, strategy: str, regime_type: str | None = None
    ) -> dict[str, float]: ...


class NoOpRegimeAdjuster:
    """레짐 조정 없이 기존 가중치 그대로 반환 (기본값)."""

    def adjust_weights(
        self, strategy: str, regime_type: str | None = None
    ) -> dict[str, float]:
        return STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS[DEFAULT_STRATEGY])


class SafetyFilterService:
    """안전성 필터 — 파산/회계조작 위험 종목 차단.

    불변 기준 (DOMAIN.md):
      Z-Score > 1.81  AND  M-Score < -1.78 통과 시에만 스코어링 진행
    """

    def check(self, z_score: float | None, m_score: float | None) -> SafetyGate:
        return SafetyGate(z_score=z_score, m_score=m_score)

    def is_safe(self, z_score: float | None, m_score: float | None) -> bool:
        return SafetyGate(z_score=z_score, m_score=m_score).passed


class CompositeScoringService:
    """3축 점수를 전략별 가중치로 합산하여 복합 점수 산출.

    성장주 (PBR > 3)의 경우 G-Score를 fundamental 점수에 블렌딩:
      G-Score 기여 = (g_score / 8) * 15 (최대 15점 추가)
      적용 후 fundamental.value + G-Score 기여, 100점 상한
    비성장주는 기존 동작과 동일 (하위 호환).
    """

    def __init__(self, regime_adjuster: RegimeWeightAdjuster | None = None) -> None:
        self._regime_adjuster: RegimeWeightAdjuster = regime_adjuster or NoOpRegimeAdjuster()

    def compute(
        self,
        fundamental: FundamentalScore,
        technical: TechnicalScore,
        sentiment: SentimentScore,
        strategy: str = DEFAULT_STRATEGY,
        tail_risk_penalty: float = 0.0,
        g_score: int | None = None,
        is_growth_stock: bool = False,
    ) -> CompositeScore:
        """복합 점수 계산.

        Safety Gate 탈락 종목은 호출하지 않는다.
        탈락 시 zero 처리는 Application Layer(ScoringHandler)에서 담당.

        Args:
            fundamental: 기본적 분석 점수 (0-100)
            technical: 기술적 분석 점수 (0-100)
            sentiment: 센티먼트 점수 (0-100)
            strategy: 전략 ("swing" or "position")
            tail_risk_penalty: 꼬리위험 패널티
            g_score: Mohanram G-Score (0-8), 성장주에만 적용
            is_growth_stock: PBR > 3 여부
        """
        # G-Score blending for growth stocks
        effective_fundamental_value = fundamental.value
        if is_growth_stock and g_score is not None:
            g_contribution = (g_score / 8) * 15.0
            effective_fundamental_value = min(100.0, fundamental.value + g_contribution)

        # Create an adjusted FundamentalScore for composite calculation
        adjusted_fundamental = FundamentalScore(
            value=effective_fundamental_value,
            f_score=fundamental.f_score,
            z_score=fundamental.z_score,
            m_score=fundamental.m_score,
            g_score=fundamental.g_score,
        )

        # Get weights (regime-adjusted or default)
        w = self._regime_adjuster.adjust_weights(strategy)

        raw = (
            w["fundamental"] * adjusted_fundamental.value
            + w["technical"] * technical.value
            + w["sentiment"] * sentiment.value
        )
        raw = max(0.0, min(100.0, raw))
        risk_adj = max(0.0, min(100.0, raw - 0.3 * tail_risk_penalty))

        return CompositeScore(
            value=round(raw, 1),
            risk_adjusted=round(risk_adj, 1),
            strategy=strategy,
            weights=w,
        )


def _norm(val: float, lo: float, hi: float) -> float:
    """Normalize val from [lo, hi] to [0, 100]. Clamps to boundaries."""
    if hi == lo:
        return 50.0
    return max(0.0, min(100.0, (val - lo) / (hi - lo) * 100))


def _is_missing(val: float | None) -> bool:
    """Check if value is None or NaN."""
    if val is None:
        return True
    try:
        return math.isnan(val)
    except (TypeError, ValueError):
        return True


class TechnicalScoringService:
    """5개 기술 지표를 개별 0-100 점수로 변환하고 복합 기술 점수를 산출.

    도메인 순수 서비스 -- pandas/numpy 의존 없음. float|None 입력만 받음.
    인프라스트럭처 어댑터가 pandas Series에서 float를 추출하여 전달.
    """

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self._weights = weights or TECHNICAL_INDICATOR_WEIGHTS

    def compute(
        self,
        rsi: float | None,
        macd_histogram: float | None,
        close: float | None,
        ma50: float | None,
        ma200: float | None,
        adx: float | None,
        obv_change_pct: float | None,
    ) -> TechnicalScore:
        """5개 지표에서 복합 기술 점수 산출.

        Args:
            rsi: RSI(14) 값 (0-100)
            macd_histogram: MACD 히스토그램 값
            close: 현재 종가
            ma50: 50일 이동평균
            ma200: 200일 이동평균
            adx: ADX(14) 값
            obv_change_pct: OBV 변화율 (%)

        Returns:
            TechnicalScore with 5 sub-scores and composite value.
        """
        rsi_sub = self._score_rsi(rsi)
        macd_sub = self._score_macd(macd_histogram)
        ma_sub = self._score_ma(close, ma50, ma200)
        adx_sub = self._score_adx(adx)
        obv_sub = self._score_obv(obv_change_pct)

        composite = (
            self._weights["rsi"] * rsi_sub.value
            + self._weights["macd"] * macd_sub.value
            + self._weights["ma"] * ma_sub.value
            + self._weights["adx"] * adx_sub.value
            + self._weights["obv"] * obv_sub.value
        )
        composite = max(0.0, min(100.0, composite))

        return TechnicalScore(
            value=round(composite, 1),
            rsi_score=rsi_sub,
            macd_score=macd_sub,
            ma_score=ma_sub,
            adx_score=adx_sub,
            obv_score=obv_sub,
            weights=self._weights,
        )

    def _score_rsi(self, rsi: float | None) -> TechnicalIndicatorScore:
        """RSI scoring: oversold = high score (buying opportunity), overbought = low score."""
        if _is_missing(rsi):
            return TechnicalIndicatorScore(
                name="RSI", value=50.0,
                explanation="RSI: insufficient data",
                raw_value=None,
            )
        assert isinstance(rsi, (int, float))

        # Inverted scoring: RSI 30 (oversold) = good entry = high score
        # RSI 70 (overbought) = risky = low score
        # RSI 0 -> score 100, RSI 100 -> score 0
        score = _norm(100.0 - rsi, 0.0, 100.0)

        if rsi > 70:
            explanation = f"RSI at {rsi:.0f}: overbought territory, momentum may reverse"
        elif rsi > 60:
            explanation = f"RSI at {rsi:.0f}: bullish momentum"
        elif rsi > 40:
            explanation = f"RSI at {rsi:.0f}: neutral momentum"
        elif rsi > 30:
            explanation = f"RSI at {rsi:.0f}: bearish momentum, approaching oversold"
        else:
            explanation = f"RSI at {rsi:.0f}: oversold territory, potential reversal"

        return TechnicalIndicatorScore(
            name="RSI", value=round(score, 1),
            explanation=explanation, raw_value=rsi,
        )

    def _score_macd(self, histogram: float | None) -> TechnicalIndicatorScore:
        """MACD histogram scoring: positive = bullish, negative = bearish."""
        if _is_missing(histogram):
            return TechnicalIndicatorScore(
                name="MACD", value=50.0,
                explanation="MACD: insufficient data",
                raw_value=None,
            )
        assert isinstance(histogram, (int, float))

        # Normalize histogram: roughly -5 to +5 range maps to 0-100
        score = _norm(histogram, -5.0, 5.0)

        if histogram > 0.5:
            explanation = f"MACD histogram {histogram:+.2f}: bullish momentum"
        elif histogram > 0:
            explanation = f"MACD histogram {histogram:+.2f}: slightly bullish"
        elif histogram > -0.5:
            explanation = f"MACD histogram {histogram:+.2f}: slightly bearish"
        else:
            explanation = f"MACD histogram {histogram:+.2f}: bearish momentum"

        return TechnicalIndicatorScore(
            name="MACD", value=round(score, 1),
            explanation=explanation, raw_value=histogram,
        )

    def _score_ma(
        self, close: float | None, ma50: float | None, ma200: float | None,
    ) -> TechnicalIndicatorScore:
        """Moving average trend scoring: close vs MA50 vs MA200 relationships."""
        if _is_missing(close):
            return TechnicalIndicatorScore(
                name="MA", value=50.0,
                explanation="MA trend: insufficient data",
                raw_value=None,
            )
        assert isinstance(close, (int, float))

        score = 50.0  # baseline neutral
        parts: list[str] = []

        # Price vs MA200 (40 points of range)
        _ma200: float | None = None if _is_missing(ma200) else float(ma200)  # type: ignore[arg-type]
        _ma50: float | None = None if _is_missing(ma50) else float(ma50)  # type: ignore[arg-type]

        if _ma200 is not None:
            if close > _ma200:
                pct_above = (close - _ma200) / _ma200 * 100
                score += min(40.0, pct_above * 4)
                parts.append(f"above MA200 by {pct_above:.1f}%")
            else:
                pct_below = (_ma200 - close) / _ma200 * 100
                score -= min(40.0, pct_below * 4)
                parts.append(f"below MA200 by {pct_below:.1f}%")

        # Price vs MA50 (20 points of range)
        if _ma50 is not None:
            if close > _ma50:
                pct_above = (close - _ma50) / _ma50 * 100
                score += min(20.0, pct_above * 4)
                parts.append("above MA50")
            else:
                pct_below = (_ma50 - close) / _ma50 * 100
                score -= min(20.0, pct_below * 4)
                parts.append("below MA50")

        # Golden/death cross detection (bonus/penalty)
        if _ma50 is not None and _ma200 is not None:
            if close > _ma50 > _ma200:
                score = min(100.0, score + 10)
                parts.append("golden cross territory")
            elif close < _ma200 < _ma50:
                score = max(0.0, score - 10)
                parts.append("death cross territory")

        score = max(0.0, min(100.0, score))

        if score > 70:
            trend = "strong uptrend"
        elif score > 55:
            trend = "moderate uptrend"
        elif score > 45:
            trend = "neutral trend"
        elif score > 30:
            trend = "moderate downtrend"
        else:
            trend = "strong downtrend"

        detail = ", ".join(parts) if parts else "no MA data"
        explanation = f"MA trend: {trend} ({detail})"

        return TechnicalIndicatorScore(
            name="MA", value=round(score, 1),
            explanation=explanation, raw_value=close,
        )

    def _score_adx(self, adx: float | None) -> TechnicalIndicatorScore:
        """ADX trend strength scoring: higher ADX = stronger trend = higher score."""
        if _is_missing(adx):
            return TechnicalIndicatorScore(
                name="ADX", value=50.0,
                explanation="ADX: insufficient data",
                raw_value=None,
            )
        assert isinstance(adx, (int, float))

        # Normalize ADX 0-50 range to 0-100
        score = _norm(adx, 0.0, 50.0)

        if adx > 40:
            explanation = f"ADX at {adx:.0f}: very strong trend"
        elif adx > 25:
            explanation = f"ADX at {adx:.0f}: strong trend"
        elif adx > 20:
            explanation = f"ADX at {adx:.0f}: developing trend"
        else:
            explanation = f"ADX at {adx:.0f}: weak/no trend"

        return TechnicalIndicatorScore(
            name="ADX", value=round(score, 1),
            explanation=explanation, raw_value=adx,
        )

    def _score_obv(self, obv_change_pct: float | None) -> TechnicalIndicatorScore:
        """OBV volume scoring: positive change = bullish, negative = bearish."""
        if _is_missing(obv_change_pct):
            return TechnicalIndicatorScore(
                name="OBV", value=50.0,
                explanation="OBV: insufficient data",
                raw_value=None,
            )
        assert isinstance(obv_change_pct, (int, float))

        # Normalize OBV change % from -20% to +20% range
        score = _norm(obv_change_pct, -20.0, 20.0)

        if obv_change_pct > 10:
            explanation = f"OBV change {obv_change_pct:+.1f}%: strong positive volume"
        elif obv_change_pct > 0:
            explanation = f"OBV change {obv_change_pct:+.1f}%: positive volume"
        elif obv_change_pct > -10:
            explanation = f"OBV change {obv_change_pct:+.1f}%: negative volume"
        else:
            explanation = f"OBV change {obv_change_pct:+.1f}%: strong negative volume"

        return TechnicalIndicatorScore(
            name="OBV", value=round(score, 1),
            explanation=explanation, raw_value=obv_change_pct,
        )
