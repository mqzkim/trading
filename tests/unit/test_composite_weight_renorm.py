"""Unit tests for CompositeScore confidence-aware weight renormalization.

Phase 27-02: Proves that when SentimentConfidence=NONE, the 20% sentiment
axis is dropped and fundamental+technical weights are renormalized (0.5/0.5
for swing, 5/8 + 3/8 for position).
"""
import pytest

from src.scoring.domain.value_objects import (
    FundamentalScore,
    TechnicalScore,
    SentimentScore,
    SentimentConfidence,
)
from src.scoring.domain.services import CompositeScoringService


@pytest.fixture
def svc() -> CompositeScoringService:
    return CompositeScoringService()


@pytest.fixture
def fund60() -> FundamentalScore:
    return FundamentalScore(value=60)


@pytest.fixture
def tech70() -> TechnicalScore:
    return TechnicalScore(value=70)


@pytest.fixture
def sent_none() -> SentimentScore:
    return SentimentScore(value=50, confidence=SentimentConfidence.NONE)


# -- NONE confidence: swing strategy renormalization ---------------------------


class TestNoneConfidenceSwingRenormalization:
    """With NONE confidence and swing strategy, weights renormalize from 0.4/0.4 to 0.5/0.5."""

    def test_none_confidence_renormalizes_to_half_half(
        self,
        svc: CompositeScoringService,
        fund60: FundamentalScore,
        tech70: TechnicalScore,
        sent_none: SentimentScore,
    ) -> None:
        """Swing: 0.4/0.4/0.2 → drop sentiment → 0.5/0.5.
        Expected: 0.5*60 + 0.5*70 = 65.0
        """
        result = svc.compute(
            fund60, tech70, sent_none,
            strategy="swing",
            sentiment_confidence=SentimentConfidence.NONE,
        )
        assert abs(result.value - 65.0) < 0.5, (
            f"Expected ~65.0 (0.5*60 + 0.5*70), got {result.value}"
        )

    def test_none_confidence_different_values(
        self, svc: CompositeScoringService
    ) -> None:
        """Verify renormalization with different fund/tech values."""
        fund = FundamentalScore(value=80)
        tech = TechnicalScore(value=40)
        sent = SentimentScore(value=50, confidence=SentimentConfidence.NONE)
        # Expected: 0.5*80 + 0.5*40 = 60.0
        result = svc.compute(fund, tech, sent, sentiment_confidence=SentimentConfidence.NONE)
        assert abs(result.value - 60.0) < 0.5, (
            f"Expected ~60.0 (0.5*80 + 0.5*40), got {result.value}"
        )

    def test_none_confidence_weights_recorded_in_result(
        self,
        svc: CompositeScoringService,
        fund60: FundamentalScore,
        tech70: TechnicalScore,
        sent_none: SentimentScore,
    ) -> None:
        """Result weights reflect renormalization: sentiment weight = 0.0."""
        result = svc.compute(
            fund60, tech70, sent_none,
            sentiment_confidence=SentimentConfidence.NONE,
        )
        assert result.weights is not None
        assert result.weights.get("sentiment", -1) == 0.0


# -- Full confidence levels: sentiment included --------------------------------


class TestFullConfidenceLevels:
    """With LOW/MEDIUM/HIGH confidence, sentiment axis is fully included."""

    def test_high_confidence_uses_full_3_axis_weights(
        self, svc: CompositeScoringService
    ) -> None:
        """HIGH: full 3-axis swing weights 0.4/0.4/0.2.
        Expected: 0.4*60 + 0.4*70 + 0.2*50 = 24+28+10 = 62.0
        """
        fund = FundamentalScore(value=60)
        tech = TechnicalScore(value=70)
        sent = SentimentScore(value=50, confidence=SentimentConfidence.HIGH)
        result = svc.compute(
            fund, tech, sent,
            sentiment_confidence=SentimentConfidence.HIGH,
        )
        assert abs(result.value - 62.0) < 0.5, (
            f"Expected ~62.0 (full 3-axis), got {result.value}"
        )

    def test_medium_confidence_uses_full_3_axis_weights(
        self, svc: CompositeScoringService
    ) -> None:
        """MEDIUM: uses full 3-axis weights (NONE is the only special case)."""
        fund = FundamentalScore(value=60)
        tech = TechnicalScore(value=70)
        sent = SentimentScore(value=50, confidence=SentimentConfidence.MEDIUM)
        result = svc.compute(
            fund, tech, sent,
            sentiment_confidence=SentimentConfidence.MEDIUM,
        )
        # 0.4*60 + 0.4*70 + 0.2*50 = 62.0
        assert abs(result.value - 62.0) < 0.5

    def test_low_confidence_uses_full_3_axis_weights(
        self, svc: CompositeScoringService
    ) -> None:
        """LOW: uses full 3-axis weights (NONE is the only special case)."""
        fund = FundamentalScore(value=60)
        tech = TechnicalScore(value=70)
        sent = SentimentScore(value=50, confidence=SentimentConfidence.LOW)
        result = svc.compute(
            fund, tech, sent,
            sentiment_confidence=SentimentConfidence.LOW,
        )
        # 0.4*60 + 0.4*70 + 0.2*50 = 62.0
        assert abs(result.value - 62.0) < 0.5

    def test_default_parameter_not_none_uses_sentiment(
        self, svc: CompositeScoringService
    ) -> None:
        """Default sentiment_confidence=MEDIUM — sentiment is included by default."""
        fund = FundamentalScore(value=80)
        tech = TechnicalScore(value=30)
        sent = SentimentScore(value=50)
        # Default: sentiment_confidence=MEDIUM → 0.4*80+0.4*30+0.2*50 = 32+12+10 = 54.0
        result = svc.compute(fund, tech, sent)
        assert abs(result.value - 54.0) < 0.5


# -- Position strategy renormalization -----------------------------------------


class TestPositionStrategyRenormalization:
    """Position strategy (0.5/0.3/0.2): NONE confidence → 5/8 fund + 3/8 tech."""

    def test_none_confidence_position_strategy(
        self, svc: CompositeScoringService
    ) -> None:
        """Position: 0.50/0.30/0.20 → drop sentiment → 0.5/0.8 fund + 0.3/0.8 tech.
        Expected: (5/8)*80 + (3/8)*60 = 50 + 22.5 = 72.5
        """
        fund = FundamentalScore(value=80)
        tech = TechnicalScore(value=60)
        sent = SentimentScore(value=50, confidence=SentimentConfidence.NONE)
        result = svc.compute(
            fund, tech, sent,
            strategy="position",
            sentiment_confidence=SentimentConfidence.NONE,
        )
        # 0.50/(0.50+0.30)=0.625 fund; 0.30/0.80=0.375 tech
        # 0.625*80 + 0.375*60 = 50 + 22.5 = 72.5
        assert abs(result.value - 72.5) < 0.5, (
            f"Expected ~72.5 (position strategy renorm), got {result.value}"
        )


# -- G-Score growth stock with NONE confidence ---------------------------------


class TestGScoreWithNoneConfidence:
    """G-Score blending still works correctly when confidence=NONE."""

    def test_g_score_growth_stock_with_none_confidence(
        self, svc: CompositeScoringService
    ) -> None:
        """G-Score is applied to fundamental before NONE renormalization."""
        # fund=60, g_score=8 (max) → +15 = 75 effective fundamental
        fund = FundamentalScore(value=60, g_score=8)
        tech = TechnicalScore(value=70)
        sent = SentimentScore(value=50, confidence=SentimentConfidence.NONE)
        result = svc.compute(
            fund, tech, sent,
            strategy="swing",
            g_score=8,
            is_growth_stock=True,
            sentiment_confidence=SentimentConfidence.NONE,
        )
        # Effective fund = min(100, 60 + (8/8)*15) = 75
        # Renorm (NONE): 0.5*75 + 0.5*70 = 37.5 + 35 = 72.5
        assert abs(result.value - 72.5) < 0.5, (
            f"Expected ~72.5 (g_score+NONE renorm), got {result.value}"
        )

    def test_g_score_growth_stock_with_high_confidence(
        self, svc: CompositeScoringService
    ) -> None:
        """G-Score blending + HIGH confidence (full 3-axis) still correct."""
        fund = FundamentalScore(value=60, g_score=4)
        tech = TechnicalScore(value=70)
        sent = SentimentScore(value=50, confidence=SentimentConfidence.HIGH)
        result = svc.compute(
            fund, tech, sent,
            strategy="swing",
            g_score=4,
            is_growth_stock=True,
            sentiment_confidence=SentimentConfidence.HIGH,
        )
        # Effective fund = min(100, 60 + (4/8)*15) = 67.5
        # Full: 0.4*67.5 + 0.4*70 + 0.2*50 = 27 + 28 + 10 = 65.0
        assert abs(result.value - 65.0) < 0.5, (
            f"Expected ~65.0 (g_score+HIGH), got {result.value}"
        )
