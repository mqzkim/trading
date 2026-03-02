"""Scoring 도메인 — Domain Services.

CompositeScoringService: 3축 점수 → 복합 점수
SafetyFilterService: 안전성 필터 판정

참조: core/scoring/composite.py, core/scoring/safety.py (원본 로직)
"""
from __future__ import annotations

from .value_objects import (
    FundamentalScore,
    TechnicalScore,
    SentimentScore,
    SafetyGate,
    CompositeScore,
    DEFAULT_STRATEGY,
)


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
    """3축 점수를 전략별 가중치로 합산하여 복합 점수 산출."""

    def compute(
        self,
        fundamental: FundamentalScore,
        technical: TechnicalScore,
        sentiment: SentimentScore,
        strategy: str = DEFAULT_STRATEGY,
        tail_risk_penalty: float = 0.0,
    ) -> CompositeScore:
        """
        Safety Gate 탈락 종목은 호출하지 않는다.
        탈락 시 zero 처리는 Application Layer(ScoringHandler)에서 담당.
        """
        return CompositeScore.compute(
            fundamental=fundamental,
            technical=technical,
            sentiment=sentiment,
            strategy=strategy,
            tail_risk_penalty=tail_risk_penalty,
        )
