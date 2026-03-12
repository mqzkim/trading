"""Unit tests for Composite Score v2 — G-Score integration + RegimeWeightAdjuster Protocol.

Tests cover:
  - CompositeScoringService.compute() with G-Score for growth stocks
  - CompositeScoringService.compute() backward compatibility for non-growth stocks
  - RegimeWeightAdjuster Protocol definition and NoOpRegimeAdjuster
  - Composite score 0-100 range after G-Score integration

Reference: Phase 02-01 Plan, Task 2.
"""
import pytest

from src.scoring.domain.value_objects import (
    FundamentalScore,
    TechnicalScore,
    SentimentScore,
    CompositeScore,
)
from src.scoring.domain.services import (
    CompositeScoringService,
    RegimeWeightAdjuster,
    NoOpRegimeAdjuster,
)


@pytest.fixture
def base_fundamental() -> FundamentalScore:
    """Standard fundamental score for testing."""
    return FundamentalScore(value=70.0, f_score=7.0, z_score=3.0, m_score=-2.5)


@pytest.fixture
def technical() -> TechnicalScore:
    return TechnicalScore(value=65.0)


@pytest.fixture
def sentiment() -> SentimentScore:
    return SentimentScore(value=55.0)


@pytest.fixture
def service() -> CompositeScoringService:
    return CompositeScoringService()


# ── G-Score integration in composite ──────────────────────────────────


class TestCompositeWithGScore:
    """Tests for G-Score integration into composite scoring."""

    def test_growth_stock_with_high_g_score_boosts_fundamental(
        self,
        technical: TechnicalScore,
        sentiment: SentimentScore,
        service: CompositeScoringService,
    ) -> None:
        """Growth stock with g_score=7 produces higher composite than without G-Score."""
        fundamental_with_g = FundamentalScore(
            value=70.0, f_score=7.0, z_score=3.0, m_score=-2.5, g_score=7
        )
        fundamental_without_g = FundamentalScore(
            value=70.0, f_score=7.0, z_score=3.0, m_score=-2.5, g_score=None
        )

        score_with = service.compute(
            fundamental=fundamental_with_g,
            technical=technical,
            sentiment=sentiment,
            g_score=7,
            is_growth_stock=True,
        )
        score_without = service.compute(
            fundamental=fundamental_without_g,
            technical=technical,
            sentiment=sentiment,
        )

        assert score_with.value > score_without.value

    def test_non_growth_stock_behaves_identically_to_original(
        self,
        base_fundamental: FundamentalScore,
        technical: TechnicalScore,
        sentiment: SentimentScore,
        service: CompositeScoringService,
    ) -> None:
        """Non-growth stock (g_score=None) produces identical score to original composite."""
        score_new = service.compute(
            fundamental=base_fundamental,
            technical=technical,
            sentiment=sentiment,
            g_score=None,
            is_growth_stock=False,
        )
        score_original = service.compute(
            fundamental=base_fundamental,
            technical=technical,
            sentiment=sentiment,
        )

        assert score_new.value == score_original.value
        assert score_new.risk_adjusted == score_original.risk_adjusted

    def test_low_g_score_reduces_fundamental_contribution(
        self,
        technical: TechnicalScore,
        sentiment: SentimentScore,
        service: CompositeScoringService,
    ) -> None:
        """Growth stock with g_score=0 produces lower score than g_score=7."""
        fundamental = FundamentalScore(
            value=70.0, f_score=7.0, z_score=3.0, m_score=-2.5, g_score=0
        )

        score_low_g = service.compute(
            fundamental=fundamental,
            technical=technical,
            sentiment=sentiment,
            g_score=0,
            is_growth_stock=True,
        )
        score_high_g = service.compute(
            fundamental=fundamental,
            technical=technical,
            sentiment=sentiment,
            g_score=7,
            is_growth_stock=True,
        )

        assert score_low_g.value < score_high_g.value

    def test_composite_still_validates_0_100_range(
        self,
        technical: TechnicalScore,
        sentiment: SentimentScore,
        service: CompositeScoringService,
    ) -> None:
        """Composite score with G-Score integration stays within 0-100."""
        fundamental = FundamentalScore(
            value=95.0, f_score=9.0, z_score=5.0, m_score=-3.0, g_score=8
        )
        tech_max = TechnicalScore(value=100.0)
        sent_max = SentimentScore(value=100.0)

        score = service.compute(
            fundamental=fundamental,
            technical=tech_max,
            sentiment=sent_max,
            g_score=8,
            is_growth_stock=True,
        )

        assert 0 <= score.value <= 100
        assert 0 <= score.risk_adjusted <= 100


# ── RegimeWeightAdjuster Protocol ─────────────────────────────────────


class TestRegimeWeightAdjuster:
    """Tests for RegimeWeightAdjuster Protocol and NoOp default."""

    def test_protocol_has_adjust_weights_method(self) -> None:
        """RegimeWeightAdjuster Protocol has adjust_weights(strategy, regime_type) -> dict."""
        # Verify Protocol exists and has the right signature
        noop = NoOpRegimeAdjuster()
        result = noop.adjust_weights("swing", None)
        assert isinstance(result, dict)
        assert "fundamental" in result
        assert "technical" in result
        assert "sentiment" in result

    def test_noop_adjuster_returns_unchanged_weights(self) -> None:
        """NoOpRegimeAdjuster returns STRATEGY_WEIGHTS unchanged."""
        from src.scoring.domain.value_objects import STRATEGY_WEIGHTS

        noop = NoOpRegimeAdjuster()
        for strategy in STRATEGY_WEIGHTS:
            result = noop.adjust_weights(strategy)
            assert result == STRATEGY_WEIGHTS[strategy]

    def test_service_accepts_optional_regime_adjuster(self) -> None:
        """CompositeScoringService accepts optional regime_adjuster parameter."""
        adjuster = NoOpRegimeAdjuster()
        service = CompositeScoringService(regime_adjuster=adjuster)
        assert service is not None

        # Also works without adjuster (defaults to NoOp)
        service_default = CompositeScoringService()
        assert service_default is not None
