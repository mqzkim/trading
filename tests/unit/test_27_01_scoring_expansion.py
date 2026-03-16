"""Tests for Phase 27-01: Scoring Expansion.

Covers:
  - SentimentConfidence enum (NONE/LOW/MEDIUM/HIGH)
  - SentimentScore VO expansion with sub-scores + confidence
  - SentimentScore backward compatibility
  - SentimentUpdatedEvent domain event
  - MACD ATR-based normalization fix
  - CompositeScoringService NONE confidence weight renormalization
  - RealSentimentAdapter interface
"""
import pytest

from src.scoring.domain.value_objects import (
    SentimentScore,
    SentimentConfidence,
    FundamentalScore,
    TechnicalScore,
)
from src.scoring.domain.events import SentimentUpdatedEvent
from src.scoring.domain.services import (
    TechnicalScoringService,
    CompositeScoringService,
)
from src.scoring.domain import SentimentConfidence as DomainSentimentConfidence


# -- SentimentConfidence enum --------------------------------------------------


class TestSentimentConfidence:
    """Tests for SentimentConfidence enum."""

    def test_enum_has_four_values(self) -> None:
        """SentimentConfidence has NONE, LOW, MEDIUM, HIGH."""
        assert SentimentConfidence.NONE is not None
        assert SentimentConfidence.LOW is not None
        assert SentimentConfidence.MEDIUM is not None
        assert SentimentConfidence.HIGH is not None

    def test_enum_importable_from_domain(self) -> None:
        """SentimentConfidence importable from src.scoring.domain."""
        assert DomainSentimentConfidence is not None

    def test_enum_values_distinct(self) -> None:
        """All four confidence levels are distinct."""
        levels = [
            SentimentConfidence.NONE,
            SentimentConfidence.LOW,
            SentimentConfidence.MEDIUM,
            SentimentConfidence.HIGH,
        ]
        assert len(set(levels)) == 4


# -- SentimentScore VO expansion -----------------------------------------------


class TestSentimentScoreExpanded:
    """Tests for expanded SentimentScore VO."""

    def test_backward_compat_value_only(self) -> None:
        """SentimentScore(value=50) still works (backward compat)."""
        score = SentimentScore(value=50)
        assert score.value == 50
        assert score.confidence == SentimentConfidence.NONE

    def test_full_construction(self) -> None:
        """SentimentScore with all sub-fields works."""
        score = SentimentScore(
            value=70.0,
            news_score=65.0,
            insider_score=75.0,
            institutional_score=60.0,
            analyst_score=80.0,
            confidence=SentimentConfidence.HIGH,
        )
        assert score.value == 70.0
        assert score.news_score == 65.0
        assert score.insider_score == 75.0
        assert score.institutional_score == 60.0
        assert score.analyst_score == 80.0
        assert score.confidence == SentimentConfidence.HIGH

    def test_partial_sub_scores(self) -> None:
        """SentimentScore with only some sub-scores works."""
        score = SentimentScore(
            value=60.0,
            news_score=55.0,
            confidence=SentimentConfidence.LOW,
        )
        assert score.news_score == 55.0
        assert score.insider_score is None
        assert score.institutional_score is None
        assert score.analyst_score is None

    def test_sub_scores_default_to_none(self) -> None:
        """Sub-score fields default to None when not provided."""
        score = SentimentScore(value=50)
        assert score.news_score is None
        assert score.insider_score is None
        assert score.institutional_score is None
        assert score.analyst_score is None

    def test_validation_still_applies(self) -> None:
        """SentimentScore validation still rejects out-of-range values."""
        with pytest.raises(ValueError):
            SentimentScore(value=-1.0)
        with pytest.raises(ValueError):
            SentimentScore(value=101.0)


# -- SentimentUpdatedEvent -----------------------------------------------------


class TestSentimentUpdatedEvent:
    """Tests for SentimentUpdatedEvent domain event."""

    def test_event_creation(self) -> None:
        """SentimentUpdatedEvent is creatable with required fields."""
        event = SentimentUpdatedEvent(
            symbol="AAPL",
            sentiment_score=70.0,
            confidence="HIGH",
            news_score=65.0,
            insider_score=None,
            institutional_score=75.0,
            analyst_score=80.0,
        )
        assert event.symbol == "AAPL"
        assert event.sentiment_score == 70.0
        assert event.confidence == "HIGH"
        assert event.news_score == 65.0
        assert event.insider_score is None

    def test_event_importable_from_domain(self) -> None:
        """SentimentUpdatedEvent importable from src.scoring.domain."""
        from src.scoring.domain import SentimentUpdatedEvent as SentimentUpdatedEventDomain
        assert SentimentUpdatedEventDomain is not None

    def test_event_is_frozen(self) -> None:
        """SentimentUpdatedEvent is immutable (frozen dataclass)."""
        event = SentimentUpdatedEvent(
            symbol="AAPL",
            sentiment_score=70.0,
            confidence="HIGH",
            news_score=65.0,
            insider_score=None,
            institutional_score=75.0,
            analyst_score=80.0,
        )
        with pytest.raises((AttributeError, TypeError)):
            event.symbol = "TSLA"  # type: ignore[misc]


# -- MACD ATR normalization fix ------------------------------------------------


class TestMACDATRNormalization:
    """Tests for MACD ATR-based dynamic range normalization."""

    @pytest.fixture
    def service(self) -> TechnicalScoringService:
        return TechnicalScoringService()

    def test_atr_parameter_accepted(self, service: TechnicalScoringService) -> None:
        """TechnicalScoringService.compute() accepts atr21 parameter."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=0.5,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=25.0,
            obv_change_pct=0.0,
            atr21=3.5,
        )
        assert result.macd_score is not None

    def test_atr_none_uses_fallback(self, service: TechnicalScoringService) -> None:
        """atr21=None falls back gracefully (no crash)."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=0.5,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=25.0,
            obv_change_pct=0.0,
            atr21=None,
        )
        assert result.macd_score is not None
        assert 0 <= result.macd_score.value <= 100

    def test_nvr_high_priced_stock_moderate_macd(self, service: TechnicalScoringService) -> None:
        """NVR-like stock (histogram=50, atr21=198) gets moderate MACD score (not 100)."""
        result = service.compute(
            rsi=50,
            macd_histogram=50.0,
            close=6500,
            ma50=6400,
            ma200=6000,
            adx=25,
            obv_change_pct=0,
            atr21=198.0,
        )
        # With ATR=198, range = [-396, +396]. Histogram=50 => ~63 score (not 100)
        assert result.macd_score is not None
        assert result.macd_score.value < 90, (
            f"Expected moderate score < 90 for moderate histogram, got {result.macd_score.value}"
        )
        assert result.macd_score.value > 50, (
            f"Expected score > 50 for positive histogram, got {result.macd_score.value}"
        )

    def test_atr_small_stock_uses_atr_range(self, service: TechnicalScoringService) -> None:
        """Small stock with ATR=3.5 uses range [-7, +7] for MACD scoring."""
        result_with_atr = service.compute(
            rsi=50.0,
            macd_histogram=3.5,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=25.0,
            obv_change_pct=0.0,
            atr21=3.5,
        )
        # histogram=3.5, range=[-7, +7] -> 75 score (above midpoint)
        assert result_with_atr.macd_score is not None
        assert result_with_atr.macd_score.value > 50

    def test_macd_backward_compat_without_atr(self, service: TechnicalScoringService) -> None:
        """compute() without atr21 still produces valid MACD score (backward compat)."""
        result = service.compute(
            rsi=65.0,
            macd_histogram=0.5,
            close=150.0,
            ma50=145.0,
            ma200=130.0,
            adx=25.0,
            obv_change_pct=5.0,
        )
        assert result.macd_score is not None
        assert 0 <= result.macd_score.value <= 100

    def test_existing_tests_still_pass_with_atr(self, service: TechnicalScoringService) -> None:
        """Existing test: compute produces 5 sub-scores still works."""
        result = service.compute(
            rsi=65.0,
            macd_histogram=0.5,
            close=150.0,
            ma50=145.0,
            ma200=130.0,
            adx=25.0,
            obv_change_pct=5.0,
        )
        assert len(result.sub_scores) == 5
        assert result.rsi_score is not None
        assert result.macd_score is not None
        assert result.ma_score is not None
        assert result.adx_score is not None
        assert result.obv_score is not None


# -- Composite re-normalization when confidence=NONE ---------------------------


class TestCompositeNoneConfidence:
    """Tests for CompositeScore re-normalization when sentiment confidence is NONE."""

    @pytest.fixture
    def service(self) -> CompositeScoringService:
        return CompositeScoringService()

    def test_none_confidence_omits_sentiment(self, service: CompositeScoringService) -> None:
        """With NONE confidence, composite drops sentiment and renormalizes 40/40."""
        fund = FundamentalScore(value=60)
        tech = TechnicalScore(value=70)
        sent = SentimentScore(value=50, confidence=SentimentConfidence.NONE)

        result = service.compute(
            fund, tech, sent, sentiment_confidence=SentimentConfidence.NONE
        )
        # Swing weights: fundamental=0.40, technical=0.40, sentiment=0.20
        # Without sentiment: renormalized 0.40/0.80 = 0.50 each
        # 0.50 * 60 + 0.50 * 70 = 65.0
        assert abs(result.value - 65.0) < 1.0, (
            f"Expected ~65.0 for NONE confidence, got {result.value}"
        )

    def test_medium_confidence_uses_sentiment(self, service: CompositeScoringService) -> None:
        """With MEDIUM confidence, composite includes sentiment (default behavior)."""
        fund = FundamentalScore(value=60)
        tech = TechnicalScore(value=70)
        sent = SentimentScore(value=50, confidence=SentimentConfidence.MEDIUM)

        result = service.compute(
            fund, tech, sent, sentiment_confidence=SentimentConfidence.MEDIUM
        )
        # 0.40 * 60 + 0.40 * 70 + 0.20 * 50 = 24 + 28 + 10 = 62.0
        assert abs(result.value - 62.0) < 0.5

    def test_none_confidence_is_default_parameter(self, service: CompositeScoringService) -> None:
        """sentiment_confidence parameter has a default value (not required)."""
        fund = FundamentalScore(value=70)
        tech = TechnicalScore(value=65)
        sent = SentimentScore(value=55)

        # Should not raise TypeError
        result = service.compute(fund, tech, sent)
        assert result is not None

    def test_none_confidence_with_position_strategy(self, service: CompositeScoringService) -> None:
        """NONE confidence works with position strategy too (50/30/20 -> renorm 50/30)."""
        fund = FundamentalScore(value=80)
        tech = TechnicalScore(value=60)
        sent = SentimentScore(value=50, confidence=SentimentConfidence.NONE)

        result = service.compute(
            fund, tech, sent,
            strategy="position",
            sentiment_confidence=SentimentConfidence.NONE,
        )
        # Position weights: 0.50, 0.30, 0.20; drop sentiment
        # Renorm: 0.50/(0.50+0.30) = 0.625 fund; 0.30/0.80 = 0.375 tech
        # 0.625 * 80 + 0.375 * 60 = 50 + 22.5 = 72.5
        assert abs(result.value - 72.5) < 1.0

    def test_existing_composite_tests_unaffected(self, service: CompositeScoringService) -> None:
        """Existing exact computation test still passes (54.0)."""
        fund = FundamentalScore(value=80.0, f_score=7.0, z_score=3.0, m_score=-2.5)
        tech = TechnicalScore(value=30.0)
        sent = SentimentScore(value=50.0)

        result = service.compute(
            fundamental=fund,
            technical=tech,
            sentiment=sent,
            strategy="swing",
        )
        # 0.40*80 + 0.40*30 + 0.20*50 = 32 + 12 + 10 = 54.0
        assert result.value == 54.0


# -- RealSentimentAdapter interface --------------------------------------------


class TestRealSentimentAdapterInterface:
    """Tests for RealSentimentAdapter basic interface."""

    def test_importable(self) -> None:
        """RealSentimentAdapter is importable from infrastructure."""
        from src.scoring.infrastructure.core_scoring_adapter import RealSentimentAdapter
        assert RealSentimentAdapter is not None

    def test_get_returns_dict_with_required_keys(self) -> None:
        """RealSentimentAdapter.get(symbol) returns dict with required keys."""
        from src.scoring.infrastructure.core_scoring_adapter import RealSentimentAdapter
        adapter = RealSentimentAdapter()
        result = adapter.get("AAPL")
        assert "sentiment_score" in result
        assert "news_score" in result
        assert "insider_score" in result
        assert "institutional_score" in result
        assert "analyst_score" in result
        assert "confidence" in result

    def test_confidence_is_sentiment_confidence_enum(self) -> None:
        """confidence field is a SentimentConfidence enum value."""
        from src.scoring.infrastructure.core_scoring_adapter import RealSentimentAdapter
        adapter = RealSentimentAdapter()
        result = adapter.get("AAPL")
        assert isinstance(result["confidence"], SentimentConfidence)

    def test_sentiment_score_in_range(self) -> None:
        """sentiment_score is in 0-100 range."""
        from src.scoring.infrastructure.core_scoring_adapter import RealSentimentAdapter
        adapter = RealSentimentAdapter()
        result = adapter.get("AAPL")
        assert 0 <= result["sentiment_score"] <= 100

    def test_no_alpaca_keys_news_none(self) -> None:
        """Without Alpaca keys, news_score is None."""
        from src.scoring.infrastructure.core_scoring_adapter import RealSentimentAdapter
        adapter = RealSentimentAdapter(alpaca_key=None, alpaca_secret=None)
        result = adapter.get("AAPL")
        assert result["news_score"] is None

    def test_exportable_from_infrastructure_init(self) -> None:
        """RealSentimentAdapter is in infrastructure __init__.py exports."""
        from src.scoring.infrastructure import RealSentimentAdapter
        assert RealSentimentAdapter is not None
