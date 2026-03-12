"""Unit tests for Mohanram G-Score — pure math, FundamentalScore VO, CoreScoringAdapter.

Tests cover:
  - mohanram_g_score() pure function (criteria G1-G8)
  - FundamentalScore VO g_score field validation
  - CoreScoringAdapter.compute_mohanram_g() adapter method

Reference: Mohanram (2004), 8-criterion binary scoring.
"""
import pytest

from core.scoring.fundamental import mohanram_g_score
from src.scoring.domain.value_objects import FundamentalScore
from src.scoring.infrastructure.core_scoring_adapter import CoreScoringAdapter


# ── mohanram_g_score() pure function ──────────────────────────────────


class TestMohanramGScorePureMath:
    """Reference-value tests for the 8-criterion G-Score."""

    def test_perfect_score_all_criteria_exceed_sector_medians(self) -> None:
        """All 8 criteria met -> G-Score = 8."""
        score = mohanram_g_score(
            roa=0.15,
            cfo_to_assets=0.12,
            cfo=100_000,
            net_income=50_000,
            roa_variance=0.002,
            sales_growth_variance=0.01,
            rd_to_assets=0.10,
            capex_to_assets=0.08,
            ad_to_assets=0.05,
            sector_median_roa=0.10,
            sector_median_cfo_to_assets=0.08,
            sector_median_roa_variance=0.005,
            sector_median_sales_growth_variance=0.03,
            sector_median_rd_to_assets=0.06,
            sector_median_capex_to_assets=0.05,
            sector_median_ad_to_assets=0.03,
        )
        assert score == 8

    def test_zero_score_all_criteria_below_sector_medians(self) -> None:
        """All 8 criteria unmet -> G-Score = 0."""
        score = mohanram_g_score(
            roa=0.02,
            cfo_to_assets=0.03,
            cfo=30_000,
            net_income=50_000,  # cfo < net_income -> G3 = 0
            roa_variance=0.010,
            sales_growth_variance=0.05,
            rd_to_assets=0.01,
            capex_to_assets=0.02,
            ad_to_assets=0.01,
            sector_median_roa=0.10,
            sector_median_cfo_to_assets=0.08,
            sector_median_roa_variance=0.005,
            sector_median_sales_growth_variance=0.03,
            sector_median_rd_to_assets=0.06,
            sector_median_capex_to_assets=0.05,
            sector_median_ad_to_assets=0.03,
        )
        assert score == 0

    def test_only_profitability_criteria_met(self) -> None:
        """Only G1, G2, G3 met -> G-Score = 3."""
        score = mohanram_g_score(
            roa=0.15,               # G1: above median 0.10 -> 1
            cfo_to_assets=0.12,     # G2: above median 0.08 -> 1
            cfo=100_000,            # G3: cfo > net_income -> 1
            net_income=50_000,
            roa_variance=0.010,     # G4: above median 0.005 -> 0
            sales_growth_variance=0.05,  # G5: above median 0.03 -> 0
            rd_to_assets=0.01,      # G6: below median 0.06 -> 0
            capex_to_assets=0.02,   # G7: below median 0.05 -> 0
            ad_to_assets=0.01,      # G8: below median 0.03 -> 0
            sector_median_roa=0.10,
            sector_median_cfo_to_assets=0.08,
            sector_median_roa_variance=0.005,
            sector_median_sales_growth_variance=0.03,
            sector_median_rd_to_assets=0.06,
            sector_median_capex_to_assets=0.05,
            sector_median_ad_to_assets=0.03,
        )
        assert score == 3

    def test_g3_cash_flow_exceeds_net_income_independent_of_medians(self) -> None:
        """G3 (CFO > net income) does not depend on sector medians."""
        score = mohanram_g_score(
            roa=0.01,               # G1: below -> 0
            cfo_to_assets=0.01,     # G2: below -> 0
            cfo=100,                # G3: cfo > net_income -> 1
            net_income=50,
            roa_variance=0.99,      # G4: above -> 0
            sales_growth_variance=0.99,  # G5: above -> 0
            rd_to_assets=0.0,       # G6: below -> 0
            capex_to_assets=0.0,    # G7: below -> 0
            ad_to_assets=0.0,       # G8: below -> 0
            sector_median_roa=0.10,
            sector_median_cfo_to_assets=0.08,
            sector_median_roa_variance=0.005,
            sector_median_sales_growth_variance=0.03,
            sector_median_rd_to_assets=0.06,
            sector_median_capex_to_assets=0.05,
            sector_median_ad_to_assets=0.03,
        )
        assert score == 1  # Only G3

    def test_stability_criteria_lower_variance_is_better(self) -> None:
        """G4, G5 award points for LOWER variance than sector median."""
        score = mohanram_g_score(
            roa=0.01,               # G1: below -> 0
            cfo_to_assets=0.01,     # G2: below -> 0
            cfo=10,                 # G3: below -> 0
            net_income=20,
            roa_variance=0.001,     # G4: below median 0.005 -> 1
            sales_growth_variance=0.01,  # G5: below median 0.03 -> 1
            rd_to_assets=0.0,       # G6: below -> 0
            capex_to_assets=0.0,    # G7: below -> 0
            ad_to_assets=0.0,       # G8: below -> 0
            sector_median_roa=0.10,
            sector_median_cfo_to_assets=0.08,
            sector_median_roa_variance=0.005,
            sector_median_sales_growth_variance=0.03,
            sector_median_rd_to_assets=0.06,
            sector_median_capex_to_assets=0.05,
            sector_median_ad_to_assets=0.03,
        )
        assert score == 2  # Only G4 + G5


# ── FundamentalScore VO with g_score ──────────────────────────────────


class TestFundamentalScoreGScore:
    """Tests for g_score field validation on FundamentalScore VO."""

    def test_valid_g_score_accepted(self) -> None:
        """FundamentalScore(value=50, g_score=6) validates successfully."""
        fs = FundamentalScore(value=50.0, g_score=6)
        assert fs.g_score == 6
        assert fs.value == 50.0

    def test_g_score_out_of_range_raises(self) -> None:
        """g_score=9 should raise ValueError (max is 8)."""
        with pytest.raises(ValueError, match="G-Score must be 0-8"):
            FundamentalScore(value=50.0, g_score=9)

    def test_none_g_score_for_non_growth_stock(self) -> None:
        """g_score=None validates (non-growth stock, PBR <= 3)."""
        fs = FundamentalScore(value=50.0, g_score=None)
        assert fs.g_score is None


# ── CoreScoringAdapter.compute_mohanram_g() ───────────────────────────


class TestCoreAdapterGScore:
    """Tests for G-Score adapter wrapping pure function."""

    @pytest.fixture
    def adapter(self) -> CoreScoringAdapter:
        return CoreScoringAdapter()

    def test_adapter_returns_int_0_to_8(self, adapter: CoreScoringAdapter) -> None:
        """compute_mohanram_g() returns int 0-8 from dict inputs."""
        result = adapter.compute_mohanram_g({
            "roa": 0.15,
            "cfo_to_assets": 0.12,
            "cfo": 100_000,
            "net_income": 50_000,
            "roa_variance": 0.002,
            "sales_growth_variance": 0.01,
            "rd_to_assets": 0.10,
            "capex_to_assets": 0.08,
            "ad_to_assets": 0.05,
            "sector_median_roa": 0.10,
            "sector_median_cfo_to_assets": 0.08,
            "sector_median_roa_variance": 0.005,
            "sector_median_sales_growth_variance": 0.03,
            "sector_median_rd_to_assets": 0.06,
            "sector_median_capex_to_assets": 0.05,
            "sector_median_ad_to_assets": 0.03,
        })
        assert isinstance(result, int)
        assert 0 <= result <= 8
        assert result == 8  # All criteria met

    def test_adapter_missing_rd_ad_defaults_to_zero(self, adapter: CoreScoringAdapter) -> None:
        """Missing R&D/advertising keys default to 0 (conservative: G6/G7/G8 = 0)."""
        result = adapter.compute_mohanram_g({
            "roa": 0.15,
            "cfo_to_assets": 0.12,
            "cfo": 100_000,
            "net_income": 50_000,
            "roa_variance": 0.002,
            "sales_growth_variance": 0.01,
            # rd_to_assets, capex_to_assets, ad_to_assets missing
            "sector_median_roa": 0.10,
            "sector_median_cfo_to_assets": 0.08,
            "sector_median_roa_variance": 0.005,
            "sector_median_sales_growth_variance": 0.03,
            "sector_median_rd_to_assets": 0.06,
            "sector_median_capex_to_assets": 0.05,
            "sector_median_ad_to_assets": 0.03,
        })
        assert isinstance(result, int)
        # G1-G5 pass (5), G6-G8 fail due to defaults of 0 < median
        assert result == 5
