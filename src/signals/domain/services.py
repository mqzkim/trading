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


class SignalFusionService:
    """4가지 방법론 결과를 합산하여 합의 시그널을 생성."""

    def fuse(
        self,
        results: list[MethodologyResult],
        composite_score: float,
        safety_passed: bool,
        threshold: ConsensusThreshold = DEFAULT_THRESHOLD,
    ) -> tuple[SignalDirection, SignalStrength]:
        """
        Args:
            results: 4개 방법론 결과
            composite_score: Scoring 컨텍스트의 복합 점수 (0-100)
            safety_passed: SafetyGate 통과 여부
            threshold: 합의 임계값

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
            strength_value = self._compute_strength(results, SignalDirection.BUY, composite_score)
            return SignalDirection.BUY, SignalStrength(
                value=strength_value,
                consensus_count=buy_count,
                total_count=len(results),
            )

        # SELL 합의: 3/4 방법론 SELL 또는 매우 낮은 점수
        if sell_count >= threshold.required_count or composite_score < SELL_SCORE_THRESHOLD:
            strength_value = self._compute_strength(results, SignalDirection.SELL, composite_score)
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
    ) -> float:
        """방향에 동의한 방법론들의 평균 점수 + 복합 점수 가중 합산."""
        matching = [r for r in results if r.direction == direction]
        if not matching:
            return 0.0
        avg_method_score = sum(r.score for r in matching) / len(matching)
        return round(avg_method_score * 0.6 + composite_score * 0.4, 1)
