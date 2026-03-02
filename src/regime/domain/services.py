"""Regime 도메인 — Domain Service.

RegimeDetectionService: 4가지 지표 → 레짐 판별
불변 판별 기준 (DOMAIN.md 참조):
  Bull:     VIX < 20  AND  S&P > 200MA  AND  ADX > 25  AND  YieldCurve > 0
  Bear:     VIX > 30  AND  S&P < 200MA
  Sideways: ADX < 20
  Crisis:   VIX > 40  OR  YieldCurve < -0.5
"""
from __future__ import annotations

from .value_objects import RegimeType, VIXLevel, TrendStrength, YieldCurve, SP500Position


class RegimeDetectionService:
    """4가지 지표를 종합하여 레짐을 판별하는 도메인 서비스."""

    def detect(
        self,
        vix: VIXLevel,
        sp500: SP500Position,
        trend: TrendStrength,
        yield_curve: YieldCurve,
    ) -> tuple[RegimeType, float]:
        """
        Returns:
            (RegimeType, confidence: float 0.0-1.0)
        """
        # Crisis: 최우선 체크 (VIX > 40 OR 심각한 역전)
        if vix.is_extreme or yield_curve.is_severely_inverted:
            confidence = self._crisis_confidence(vix, yield_curve)
            return RegimeType.CRISIS, confidence

        # Sideways: 추세가 없는 경우
        if not trend.has_trend:
            return RegimeType.SIDEWAYS, 0.6

        # Bear: VIX 높고 S&P 200MA 아래
        if vix.is_high and not sp500.is_above_ma200:
            confidence = self._bear_confidence(vix, sp500)
            return RegimeType.BEAR, confidence

        # Bull: VIX 낮고 S&P 200MA 위, 강한 추세, 정상 금리차
        if (
            vix.is_low
            and sp500.is_above_ma200
            and trend.is_strong_trend
            and not yield_curve.is_inverted
        ):
            return RegimeType.BULL, 0.85

        # 불명확: 가장 근접한 레짐 반환
        return self._resolve_ambiguous(vix, sp500, trend, yield_curve)

    def _crisis_confidence(self, vix: VIXLevel, yc: YieldCurve) -> float:
        score = 0.0
        if vix.is_extreme:
            score += 0.5
        if yc.is_severely_inverted:
            score += 0.4
        return min(score + 0.1, 1.0)

    def _bear_confidence(self, vix: VIXLevel, sp500: SP500Position) -> float:
        score = 0.5
        if vix.value > 35:
            score += 0.2
        if sp500.deviation_pct < -5:
            score += 0.2
        return min(score, 1.0)

    def _resolve_ambiguous(
        self,
        vix: VIXLevel,
        sp500: SP500Position,
        trend: TrendStrength,
        yield_curve: YieldCurve,
    ) -> tuple[RegimeType, float]:
        """명확하지 않은 경우 점수 기반 판별."""
        bull_score = 0
        bear_score = 0

        if vix.is_low:
            bull_score += 2
        elif vix.is_high:
            bear_score += 2
        if sp500.is_above_ma200:
            bull_score += 2
        else:
            bear_score += 2
        if trend.is_strong_trend:
            bull_score += 1
        if not yield_curve.is_inverted:
            bull_score += 1
        else:
            bear_score += 1

        if bull_score > bear_score:
            return RegimeType.BULL, 0.55
        elif bear_score > bull_score:
            return RegimeType.BEAR, 0.55
        return RegimeType.SIDEWAYS, 0.5
