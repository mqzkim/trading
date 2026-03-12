"""Unit tests for TechnicalScoringService and TechnicalIndicatorScore VO.

Tests cover:
  - TechnicalIndicatorScore VO creation and validation
  - TechnicalScore backward compatibility (value-only)
  - TechnicalScore with full sub-score breakdown
  - TechnicalScoringService.compute() produces 5 sub-scores with explanations
  - None/NaN handling -> neutral 50 scores
  - Indicator-specific explanation content (overbought/oversold/bullish/bearish)
  - Composite score range 0-100
  - STRATEGY_WEIGHTS swing = 40/40/20

Reference: Phase 07-01 Plan, Task 1.
"""
import math

import pytest

from src.scoring.domain.value_objects import (
    TechnicalIndicatorScore,
    TechnicalScore,
    STRATEGY_WEIGHTS,
)
from src.scoring.domain.services import (
    TechnicalScoringService,
    TECHNICAL_INDICATOR_WEIGHTS,
)


# -- TechnicalIndicatorScore VO tests -------------------------------------------


class TestTechnicalIndicatorScore:
    """Tests for TechnicalIndicatorScore value object."""

    def test_valid_creation(self) -> None:
        """TechnicalIndicatorScore with valid values creates successfully."""
        score = TechnicalIndicatorScore(
            name="RSI", value=65.0, explanation="RSI at 65: bullish momentum", raw_value=65.0
        )
        assert score.name == "RSI"
        assert score.value == 65.0
        assert score.explanation == "RSI at 65: bullish momentum"
        assert score.raw_value == 65.0

    def test_value_below_zero_raises(self) -> None:
        """TechnicalIndicatorScore with value < 0 raises ValueError."""
        with pytest.raises(ValueError):
            TechnicalIndicatorScore(name="RSI", value=-1.0, explanation="bad")

    def test_value_above_100_raises(self) -> None:
        """TechnicalIndicatorScore with value > 100 raises ValueError."""
        with pytest.raises(ValueError):
            TechnicalIndicatorScore(name="RSI", value=101.0, explanation="bad")

    def test_boundary_values(self) -> None:
        """TechnicalIndicatorScore at boundaries 0 and 100 are valid."""
        zero = TechnicalIndicatorScore(name="RSI", value=0.0, explanation="min")
        assert zero.value == 0.0

        hundred = TechnicalIndicatorScore(name="RSI", value=100.0, explanation="max")
        assert hundred.value == 100.0

    def test_raw_value_optional(self) -> None:
        """TechnicalIndicatorScore works without raw_value (defaults to None)."""
        score = TechnicalIndicatorScore(name="RSI", value=50.0, explanation="neutral")
        assert score.raw_value is None


# -- TechnicalScore backward compatibility tests --------------------------------


class TestTechnicalScoreBackwardCompat:
    """Tests for TechnicalScore backward compatibility."""

    def test_value_only_creation(self) -> None:
        """TechnicalScore(value=65.0) still works without sub-scores."""
        score = TechnicalScore(value=65.0)
        assert score.value == 65.0

    def test_sub_scores_default_to_none(self) -> None:
        """All sub-score fields default to None when not provided."""
        score = TechnicalScore(value=65.0)
        assert score.rsi_score is None
        assert score.macd_score is None
        assert score.ma_score is None
        assert score.adx_score is None
        assert score.obv_score is None
        assert score.weights is None

    def test_sub_scores_property_empty_when_none(self) -> None:
        """sub_scores property returns empty list when no sub-scores."""
        score = TechnicalScore(value=65.0)
        assert score.sub_scores == []

    def test_validation_still_works(self) -> None:
        """TechnicalScore validation still rejects out-of-range values."""
        with pytest.raises(ValueError):
            TechnicalScore(value=-1.0)
        with pytest.raises(ValueError):
            TechnicalScore(value=101.0)


# -- TechnicalScore with sub-scores tests --------------------------------------


class TestTechnicalScoreWithSubScores:
    """Tests for TechnicalScore with populated sub-scores."""

    def test_all_sub_scores_populated(self) -> None:
        """TechnicalScore with all 5 sub-scores returns them via .sub_scores."""
        rsi = TechnicalIndicatorScore(name="RSI", value=60.0, explanation="bullish")
        macd = TechnicalIndicatorScore(name="MACD", value=70.0, explanation="positive")
        ma_s = TechnicalIndicatorScore(name="MA", value=80.0, explanation="uptrend")
        adx = TechnicalIndicatorScore(name="ADX", value=55.0, explanation="strong")
        obv = TechnicalIndicatorScore(name="OBV", value=65.0, explanation="positive vol")

        score = TechnicalScore(
            value=66.0,
            rsi_score=rsi,
            macd_score=macd,
            ma_score=ma_s,
            adx_score=adx,
            obv_score=obv,
        )
        assert len(score.sub_scores) == 5
        assert score.rsi_score == rsi
        assert score.macd_score == macd

    def test_partial_sub_scores(self) -> None:
        """TechnicalScore with only some sub-scores returns only non-None ones."""
        rsi = TechnicalIndicatorScore(name="RSI", value=60.0, explanation="test")
        score = TechnicalScore(value=60.0, rsi_score=rsi)
        assert len(score.sub_scores) == 1
        assert score.sub_scores[0] == rsi


# -- STRATEGY_WEIGHTS tests ----------------------------------------------------


class TestStrategyWeights:
    """Tests for STRATEGY_WEIGHTS swing = 40/40/20 (TECH-03)."""

    def test_swing_weights_40_40_20(self) -> None:
        """STRATEGY_WEIGHTS swing must be fundamental=0.40, technical=0.40, sentiment=0.20."""
        sw = STRATEGY_WEIGHTS["swing"]
        assert sw["fundamental"] == 0.40
        assert sw["technical"] == 0.40
        assert sw["sentiment"] == 0.20

    def test_swing_weights_sum_to_one(self) -> None:
        """Swing weights must sum to 1.0."""
        sw = STRATEGY_WEIGHTS["swing"]
        assert abs(sum(sw.values()) - 1.0) < 1e-9

    def test_position_weights_unchanged(self) -> None:
        """Position weights remain 50/30/20 (not affected by TECH-03)."""
        pw = STRATEGY_WEIGHTS["position"]
        assert pw["fundamental"] == 0.50
        assert pw["technical"] == 0.30
        assert pw["sentiment"] == 0.20


# -- TechnicalScoringService tests ---------------------------------------------


class TestTechnicalScoringService:
    """Tests for TechnicalScoringService.compute()."""

    @pytest.fixture
    def service(self) -> TechnicalScoringService:
        return TechnicalScoringService()

    def test_compute_returns_technical_score(self, service: TechnicalScoringService) -> None:
        """compute() returns a TechnicalScore with value 0-100."""
        result = service.compute(
            rsi=65.0,
            macd_histogram=0.5,
            close=150.0,
            ma50=145.0,
            ma200=130.0,
            adx=25.0,
            obv_change_pct=5.0,
        )
        assert isinstance(result, TechnicalScore)
        assert 0 <= result.value <= 100

    def test_compute_produces_5_sub_scores(self, service: TechnicalScoringService) -> None:
        """compute() produces exactly 5 sub-scores."""
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

    def test_all_none_returns_neutral_50(self, service: TechnicalScoringService) -> None:
        """All None inputs produce neutral score 50 with 'insufficient data' explanations."""
        result = service.compute(
            rsi=None,
            macd_histogram=None,
            close=None,
            ma50=None,
            ma200=None,
            adx=None,
            obv_change_pct=None,
        )
        assert result.value == 50.0
        for sub in result.sub_scores:
            assert sub.value == 50.0
            assert "insufficient data" in sub.explanation.lower()

    def test_nan_treated_as_none(self, service: TechnicalScoringService) -> None:
        """NaN inputs produce same result as None (neutral 50)."""
        result = service.compute(
            rsi=float("nan"),
            macd_histogram=float("nan"),
            close=float("nan"),
            ma50=float("nan"),
            ma200=float("nan"),
            adx=float("nan"),
            obv_change_pct=float("nan"),
        )
        assert result.value == 50.0

    def test_each_sub_score_has_explanation(self, service: TechnicalScoringService) -> None:
        """Each sub-score has a non-empty explanation string."""
        result = service.compute(
            rsi=65.0,
            macd_histogram=0.5,
            close=150.0,
            ma50=145.0,
            ma200=130.0,
            adx=25.0,
            obv_change_pct=5.0,
        )
        for sub in result.sub_scores:
            assert isinstance(sub.explanation, str)
            assert len(sub.explanation) > 0

    def test_sub_scores_in_0_100_range(self, service: TechnicalScoringService) -> None:
        """All sub-scores are in 0-100 range."""
        result = service.compute(
            rsi=65.0,
            macd_histogram=0.5,
            close=150.0,
            ma50=145.0,
            ma200=130.0,
            adx=25.0,
            obv_change_pct=5.0,
        )
        for sub in result.sub_scores:
            assert 0 <= sub.value <= 100

    # -- RSI explanation tests --

    def test_rsi_overbought_explanation(self, service: TechnicalScoringService) -> None:
        """RSI 75 -> explanation contains 'overbought'."""
        result = service.compute(
            rsi=75.0,
            macd_histogram=0.0,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=20.0,
            obv_change_pct=0.0,
        )
        assert result.rsi_score is not None
        assert "overbought" in result.rsi_score.explanation.lower()

    def test_rsi_oversold_explanation(self, service: TechnicalScoringService) -> None:
        """RSI 25 -> explanation contains 'oversold'."""
        result = service.compute(
            rsi=25.0,
            macd_histogram=0.0,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=20.0,
            obv_change_pct=0.0,
        )
        assert result.rsi_score is not None
        assert "oversold" in result.rsi_score.explanation.lower()

    def test_rsi_neutral_explanation(self, service: TechnicalScoringService) -> None:
        """RSI 50 -> explanation contains 'neutral'."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=0.0,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=20.0,
            obv_change_pct=0.0,
        )
        assert result.rsi_score is not None
        assert "neutral" in result.rsi_score.explanation.lower()

    # -- MACD explanation tests --

    def test_macd_positive_bullish(self, service: TechnicalScoringService) -> None:
        """Positive MACD histogram -> bullish."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=2.0,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=20.0,
            obv_change_pct=0.0,
        )
        assert result.macd_score is not None
        assert "bullish" in result.macd_score.explanation.lower()

    def test_macd_negative_bearish(self, service: TechnicalScoringService) -> None:
        """Negative MACD histogram -> bearish."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=-2.0,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=20.0,
            obv_change_pct=0.0,
        )
        assert result.macd_score is not None
        assert "bearish" in result.macd_score.explanation.lower()

    # -- MA trend tests --

    def test_ma_strong_uptrend(self, service: TechnicalScoringService) -> None:
        """close > ma50 > ma200 -> strong uptrend, high score."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=0.0,
            close=150.0,
            ma50=140.0,
            ma200=120.0,
            adx=20.0,
            obv_change_pct=0.0,
        )
        assert result.ma_score is not None
        assert result.ma_score.value > 70  # strong uptrend = high score

    def test_ma_bearish_below_ma200(self, service: TechnicalScoringService) -> None:
        """close < ma200 -> bearish, low score."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=0.0,
            close=100.0,
            ma50=120.0,
            ma200=130.0,
            adx=20.0,
            obv_change_pct=0.0,
        )
        assert result.ma_score is not None
        assert result.ma_score.value < 30  # bearish = low score

    # -- ADX trend strength tests --

    def test_adx_strong_trend(self, service: TechnicalScoringService) -> None:
        """ADX > 25 -> strong trend, higher score."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=0.0,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=35.0,
            obv_change_pct=0.0,
        )
        assert result.adx_score is not None
        assert result.adx_score.value > 50  # strong trend

    def test_adx_weak_trend(self, service: TechnicalScoringService) -> None:
        """ADX < 20 -> weak/no trend, lower score."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=0.0,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=15.0,
            obv_change_pct=0.0,
        )
        assert result.adx_score is not None
        assert result.adx_score.value < 50  # weak trend

    # -- OBV volume tests --

    def test_obv_positive_volume(self, service: TechnicalScoringService) -> None:
        """OBV change > 0 -> positive volume, higher score."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=0.0,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=20.0,
            obv_change_pct=10.0,
        )
        assert result.obv_score is not None
        assert result.obv_score.value > 50

    def test_obv_negative_volume(self, service: TechnicalScoringService) -> None:
        """OBV change < 0 -> negative volume, lower score."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=0.0,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=20.0,
            obv_change_pct=-10.0,
        )
        assert result.obv_score is not None
        assert result.obv_score.value < 50

    # -- Composite weighted sum test --

    def test_composite_is_weighted_sum(self, service: TechnicalScoringService) -> None:
        """Composite value equals weighted sum of 5 sub-scores."""
        result = service.compute(
            rsi=65.0,
            macd_histogram=0.5,
            close=150.0,
            ma50=145.0,
            ma200=130.0,
            adx=25.0,
            obv_change_pct=5.0,
        )
        weights = TECHNICAL_INDICATOR_WEIGHTS
        expected = (
            weights["rsi"] * result.rsi_score.value
            + weights["macd"] * result.macd_score.value
            + weights["ma"] * result.ma_score.value
            + weights["adx"] * result.adx_score.value
            + weights["obv"] * result.obv_score.value
        )
        assert abs(result.value - round(expected, 1)) < 0.2

    def test_indicator_weights_sum_to_one(self) -> None:
        """TECHNICAL_INDICATOR_WEIGHTS must sum to 1.0."""
        assert abs(sum(TECHNICAL_INDICATOR_WEIGHTS.values()) - 1.0) < 1e-9
