"""Signals 도메인 — Domain Service.

SignalFusionService: 4개 방법론 결과 → 합의 시그널

합의 규칙 (변경 불가, DOMAIN.md):
  BUY: 3/4 방법론 BUY + CompositeScore >= 60 + SafetyGate 통과
  SELL: 3/4 방법론 SELL 또는 CompositeScore < 30
  HOLD: 그 외 모든 경우
"""
from __future__ import annotations

from .value_objects import (
    SignalDirection,
    MethodologyResult,
    SignalStrength,
    ConsensusThreshold,
)

# 불변 임계값
BUY_SCORE_THRESHOLD = 60.0
SELL_SCORE_THRESHOLD = 30.0
DEFAULT_THRESHOLD = ConsensusThreshold(required_count=3, total_count=4)

# Regime-specific per-strategy weights (DDD 4-enum regime names)
# Keys: RegimeType.value strings. Do NOT import RegimeType -- cross-context boundary.
# Values: MethodologyType.value strings.
SIGNAL_STRATEGY_WEIGHTS: dict[str, dict[str, float]] = {
    "Bull":     {"CAN_SLIM": 0.20, "MAGIC_FORMULA": 0.20, "DUAL_MOMENTUM": 0.30, "TREND_FOLLOWING": 0.30},
    "Bear":     {"CAN_SLIM": 0.15, "MAGIC_FORMULA": 0.35, "DUAL_MOMENTUM": 0.25, "TREND_FOLLOWING": 0.25},
    "Sideways": {"CAN_SLIM": 0.25, "MAGIC_FORMULA": 0.35, "DUAL_MOMENTUM": 0.15, "TREND_FOLLOWING": 0.25},
    "Crisis":   {"CAN_SLIM": 0.10, "MAGIC_FORMULA": 0.40, "DUAL_MOMENTUM": 0.30, "TREND_FOLLOWING": 0.20},
}
DEFAULT_SIGNAL_WEIGHTS: dict[str, float] = {
    "CAN_SLIM": 0.25, "MAGIC_FORMULA": 0.25, "DUAL_MOMENTUM": 0.25, "TREND_FOLLOWING": 0.25,
}


class SignalFusionService:
    """4가지 방법론 결과를 합산하여 합의 시그널을 생성."""

    def fuse(
        self,
        results: list[MethodologyResult],
        composite_score: float,
        safety_passed: bool,
        threshold: ConsensusThreshold = DEFAULT_THRESHOLD,
        regime_type: str | None = None,
    ) -> tuple[SignalDirection, SignalStrength]:
        """
        Args:
            results: 4개 방법론 결과
            composite_score: Scoring 컨텍스트의 복합 점수 (0-100)
            safety_passed: SafetyGate 통과 여부
            threshold: 합의 임계값
            regime_type: 현재 시장 레짐 ("Bull"/"Bear"/"Sideways"/"Crisis" 또는 None)

        Returns:
            (SignalDirection, SignalStrength)
        """
        buy_count = sum(1 for r in results if r.direction == SignalDirection.BUY)
        sell_count = sum(1 for r in results if r.direction == SignalDirection.SELL)

        # Safety Gate 탈락 → 즉시 HOLD
        if not safety_passed:
            return SignalDirection.HOLD, SignalStrength(
                value=0.0,
                consensus_count=0,
                total_count=len(results),
            )

        # BUY 합의: 3/4 방법론 BUY + 점수 기준
        if buy_count >= threshold.required_count and composite_score >= BUY_SCORE_THRESHOLD:
            strength_value = self._compute_strength(results, SignalDirection.BUY, composite_score, regime_type)
            return SignalDirection.BUY, SignalStrength(
                value=strength_value,
                consensus_count=buy_count,
                total_count=len(results),
            )

        # SELL 합의: 3/4 방법론 SELL 또는 매우 낮은 점수
        if sell_count >= threshold.required_count or composite_score < SELL_SCORE_THRESHOLD:
            strength_value = self._compute_strength(results, SignalDirection.SELL, composite_score, regime_type)
            return SignalDirection.SELL, SignalStrength(
                value=strength_value,
                consensus_count=sell_count,
                total_count=len(results),
            )

        # HOLD: 합의 미달
        max_consensus = max(buy_count, sell_count)
        return SignalDirection.HOLD, SignalStrength(
            value=composite_score * 0.5,
            consensus_count=max_consensus,
            total_count=len(results),
        )

    def _compute_strength(
        self,
        results: list[MethodologyResult],
        direction: SignalDirection,
        composite_score: float,
        regime_type: str | None = None,
    ) -> float:
        """방향에 동의한 방법론들의 가중 평균 점수 + 복합 점수 합산.

        regime_type이 주어지면 해당 레짐의 전략별 가중치를 사용.
        None이면 균등 가중치 (25%) 사용 (하위 호환).
        """
        weights = SIGNAL_STRATEGY_WEIGHTS.get(regime_type, DEFAULT_SIGNAL_WEIGHTS) if regime_type else DEFAULT_SIGNAL_WEIGHTS
        matching = [r for r in results if r.direction == direction]
        if not matching:
            return 0.0
        total_weight = sum(weights.get(r.methodology.value, 0.25) for r in matching)
        if total_weight == 0:
            return 0.0
        weighted_avg = sum(r.score * weights.get(r.methodology.value, 0.25) for r in matching) / total_weight
        return round(weighted_avg * 0.6 + composite_score * 0.4, 1)
