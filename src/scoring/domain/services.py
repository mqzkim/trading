"""Scoring 도메인 — Domain Services.

CompositeScoringService: 3축 점수 → 복합 점수 (G-Score 통합)
SafetyFilterService: 안전성 필터 판정
RegimeWeightAdjuster: 레짐별 가중치 조정 프로토콜 (Phase 3 구현 대비)

참조: core/scoring/composite.py, core/scoring/safety.py (원본 로직)
"""
from __future__ import annotations

from typing import Protocol

from .value_objects import (
    FundamentalScore,
    TechnicalScore,
    SentimentScore,
    SafetyGate,
    CompositeScore,
    STRATEGY_WEIGHTS,
    DEFAULT_STRATEGY,
)


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
