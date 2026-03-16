"""Unit tests for MACD ATR-based normalization fix.

Phase 27-02: Proves the hardcoded [-5, +5] bug is fixed for high-priced stocks.
The new implementation uses [-2*atr21, +2*atr21] as the dynamic normalization range.
"""
import pytest

from src.scoring.domain.services import TechnicalScoringService


@pytest.fixture
def service() -> TechnicalScoringService:
    return TechnicalScoringService()


# -- Core parameter tests ------------------------------------------------------


class TestMACDATRParameterAccepted:
    """TechnicalScoringService.compute() accepts atr21 parameter."""

    def test_atr_parameter_accepted_returns_score(
        self, service: TechnicalScoringService
    ) -> None:
        result = service.compute(
            rsi=50.0,
            macd_histogram=1.0,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=25.0,
            obv_change_pct=0.0,
            atr21=3.5,
        )
        assert result.macd_score is not None
        assert 0 <= result.macd_score.value <= 100

    def test_no_atr_backward_compat(self, service: TechnicalScoringService) -> None:
        """compute() without atr21 still works (backward compat, no crash)."""
        result = service.compute(
            rsi=50.0,
            macd_histogram=0.5,
            close=100.0,
            ma50=100.0,
            ma200=100.0,
            adx=25.0,
            obv_change_pct=0.0,
        )
        assert result.macd_score is not None
        assert 0 <= result.macd_score.value <= 100

    def test_atr_none_explicit_backward_compat(
        self, service: TechnicalScoringService
    ) -> None:
        """atr21=None falls back to 1-dollar range (no crash)."""
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


# -- NVR high-priced stock case ------------------------------------------------


class TestMACDNVRHighPricedStock:
    """NVR-like stock (price ~$6500, ATR ~$198) must not saturate MACD to 100."""

    def test_nvr_histogram_50_with_atr_198_gives_moderate_score(
        self, service: TechnicalScoringService
    ) -> None:
        """NVR case: histogram=50, atr21=198 → range [-396,+396] → score ~56, not 100."""
        result = service.compute(
            rsi=50,
            macd_histogram=50.0,
            close=6537,
            ma50=6400,
            ma200=6000,
            adx=25,
            obv_change_pct=0,
            atr21=198.0,
        )
        assert result.macd_score is not None
        # With range [-396, +396], histogram=50 → (50+396)/792 * 100 ≈ 56.3
        # Must NOT be saturated at 100 (old hardcoded [-5,+5] bug)
        assert result.macd_score.value < 90, (
            f"MACD score should not saturate for moderate histogram. "
            f"Got {result.macd_score.value} — old hardcoded range bug?"
        )
        assert result.macd_score.value > 50, (
            f"Score should be > 50 for positive histogram. Got {result.macd_score.value}"
        )

    def test_nvr_score_approximately_correct(
        self, service: TechnicalScoringService
    ) -> None:
        """NVR: (50+396)/792 * 100 = 56.3 ± 2."""
        result = service.compute(
            rsi=50,
            macd_histogram=50.0,
            close=6537,
            ma50=6400,
            ma200=6000,
            adx=25,
            obv_change_pct=0,
            atr21=198.0,
        )
        assert result.macd_score is not None
        assert abs(result.macd_score.value - 56.3) < 2.0, (
            f"Expected ~56.3, got {result.macd_score.value}"
        )


# -- AAPL typical stock case ---------------------------------------------------


class TestMACDAAPLCase:
    """AAPL-like stock (price ~$252, ATR ~$3.5)."""

    def test_aapl_histogram_1_5_with_atr_3_5(
        self, service: TechnicalScoringService
    ) -> None:
        """AAPL: histogram=1.5, atr21=3.5 → range [-7,+7] → _norm(1.5,-7,7)=(8.5/14)*100~60.7."""
        result = service.compute(
            rsi=50,
            macd_histogram=1.5,
            close=252,
            ma50=245,
            ma200=230,
            adx=20,
            obv_change_pct=0,
            atr21=3.5,
        )
        assert result.macd_score is not None
        # (1.5 + 7) / 14 * 100 = 8.5 / 14 * 100 ≈ 60.7
        assert abs(result.macd_score.value - 60.7) < 2.0, (
            f"Expected ~60.7, got {result.macd_score.value}"
        )

    def test_aapl_positive_histogram_above_neutral(
        self, service: TechnicalScoringService
    ) -> None:
        """Positive histogram always scores above 50."""
        result = service.compute(
            rsi=50,
            macd_histogram=1.5,
            close=252,
            ma50=245,
            ma200=230,
            adx=20,
            obv_change_pct=0,
            atr21=3.5,
        )
        assert result.macd_score is not None
        assert result.macd_score.value > 50


# -- Fallback range behavior (no ATR) ------------------------------------------


class TestMACDFallbackRange:
    """When atr21 is None, fallback range [-1, +1] is used."""

    def test_histogram_large_with_no_atr_saturates(
        self, service: TechnicalScoringService
    ) -> None:
        """Without ATR, large histogram (>1) saturates to 100 — acceptable/documented behavior.

        This is the OLD behavior for when ATR is unavailable.
        With atr21=None, range is [-1, +1], so histogram=50 clamps to 100.
        This documents (not fixes) the saturation behavior for the no-ATR fallback.
        """
        result = service.compute(
            rsi=50,
            macd_histogram=50.0,  # large histogram for high-priced stock
            close=6537,
            ma50=6400,
            ma200=6000,
            adx=25,
            obv_change_pct=0,
            atr21=None,  # no ATR
        )
        assert result.macd_score is not None
        # With [-1,+1] fallback range and histogram=50, score = 100 (saturated)
        # This is acceptable when atr is unavailable — callers should pass atr21
        assert result.macd_score.value == 100.0, (
            f"With no ATR, large histogram should saturate to 100. Got {result.macd_score.value}"
        )

    def test_histogram_zero_gives_neutral(self, service: TechnicalScoringService) -> None:
        """Histogram=0 always gives 50 (neutral) regardless of ATR."""
        result_with_atr = service.compute(
            rsi=50, macd_histogram=0.0, close=100.0, ma50=100.0,
            ma200=100.0, adx=25.0, obv_change_pct=0.0, atr21=5.0,
        )
        result_no_atr = service.compute(
            rsi=50, macd_histogram=0.0, close=100.0, ma50=100.0,
            ma200=100.0, adx=25.0, obv_change_pct=0.0, atr21=None,
        )
        assert result_with_atr.macd_score is not None
        assert result_no_atr.macd_score is not None
        assert abs(result_with_atr.macd_score.value - 50.0) < 1.0
        assert abs(result_no_atr.macd_score.value - 50.0) < 1.0


# -- Other indicators unaffected -----------------------------------------------


class TestOtherIndicatorsUnchanged:
    """Non-MACD indicators are unchanged when atr21 is passed."""

    def test_rsi_score_unchanged_with_atr(self, service: TechnicalScoringService) -> None:
        """RSI score is independent of atr21."""
        result_with = service.compute(
            rsi=65.0, macd_histogram=0.5, close=100.0, ma50=98.0,
            ma200=90.0, adx=30.0, obv_change_pct=5.0, atr21=3.0,
        )
        result_without = service.compute(
            rsi=65.0, macd_histogram=0.5, close=100.0, ma50=98.0,
            ma200=90.0, adx=30.0, obv_change_pct=5.0, atr21=None,
        )
        assert result_with.rsi_score is not None
        assert result_without.rsi_score is not None
        assert result_with.rsi_score.value == result_without.rsi_score.value

    def test_adx_score_unchanged_with_atr(self, service: TechnicalScoringService) -> None:
        """ADX score is independent of atr21."""
        result_with = service.compute(
            rsi=50.0, macd_histogram=0.0, close=100.0, ma50=100.0,
            ma200=100.0, adx=35.0, obv_change_pct=0.0, atr21=5.0,
        )
        result_without = service.compute(
            rsi=50.0, macd_histogram=0.0, close=100.0, ma50=100.0,
            ma200=100.0, adx=35.0, obv_change_pct=0.0, atr21=None,
        )
        assert result_with.adx_score is not None
        assert result_without.adx_score is not None
        assert result_with.adx_score.value == result_without.adx_score.value

    def test_obv_score_unchanged_with_atr(self, service: TechnicalScoringService) -> None:
        """OBV score is independent of atr21."""
        result_with = service.compute(
            rsi=50.0, macd_histogram=0.0, close=100.0, ma50=100.0,
            ma200=100.0, adx=25.0, obv_change_pct=10.0, atr21=5.0,
        )
        result_without = service.compute(
            rsi=50.0, macd_histogram=0.0, close=100.0, ma50=100.0,
            ma200=100.0, adx=25.0, obv_change_pct=10.0, atr21=None,
        )
        assert result_with.obv_score is not None
        assert result_without.obv_score is not None
        assert result_with.obv_score.value == result_without.obv_score.value

    def test_all_five_subscores_present_with_atr(
        self, service: TechnicalScoringService
    ) -> None:
        """All 5 sub-scores are present regardless of atr21."""
        result = service.compute(
            rsi=65.0, macd_histogram=0.5, close=150.0, ma50=145.0,
            ma200=130.0, adx=25.0, obv_change_pct=5.0, atr21=4.5,
        )
        assert len(result.sub_scores) == 5
        names = {s.name for s in result.sub_scores}
        assert names == {"RSI", "MACD", "MA", "ADX", "OBV"}
