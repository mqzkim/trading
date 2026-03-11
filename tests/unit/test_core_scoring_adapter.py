"""Unit tests for CoreScoringAdapter — DDD infrastructure adapter wrapping core scoring.

Tests use known reference data to verify the adapter correctly delegates to core
scoring functions AND that the results match expected values. No mocking of core
functions — these are integration-style unit tests that validate both adapter + core math.
"""
import pytest

from src.scoring.infrastructure.core_scoring_adapter import CoreScoringAdapter
from src.scoring.domain.value_objects import SafetyGate


@pytest.fixture
def adapter() -> CoreScoringAdapter:
    return CoreScoringAdapter()


# ── Altman Z-Score ──────────────────────────────────────────────────────


class TestAltmanZScore:
    """Reference-value tests for Altman Z-Score via adapter."""

    def test_healthy_company_z_score_above_threshold(self, adapter: CoreScoringAdapter) -> None:
        """AAPL-like healthy company should produce Z > 1.81."""
        z = adapter.compute_altman_z({
            "working_capital": 5_000_000_000,
            "total_assets": 50_000_000_000,
            "retained_earnings": 15_000_000_000,
            "ebit": 8_000_000_000,
            "market_cap": 100_000_000_000,
            "total_liabilities": 30_000_000_000,
            "revenue": 60_000_000_000,
        })
        assert isinstance(z, float)
        assert z > 1.81, f"Healthy company Z should be > 1.81, got {z}"

    def test_distressed_company_z_score_below_threshold(self, adapter: CoreScoringAdapter) -> None:
        """Distressed company with negative WC should produce Z < 1.81."""
        z = adapter.compute_altman_z({
            "working_capital": -2_000_000_000,
            "total_assets": 10_000_000_000,
            "retained_earnings": -1_000_000_000,
            "ebit": -500_000_000,
            "market_cap": 2_000_000_000,
            "total_liabilities": 12_000_000_000,
            "revenue": 5_000_000_000,
        })
        assert isinstance(z, float)
        assert z < 1.81, f"Distressed company Z should be < 1.81, got {z}"


# ── Beneish M-Score ─────────────────────────────────────────────────────


class TestBeneishMScore:
    """Reference-value tests for Beneish M-Score via adapter."""

    def test_clean_company_m_score_below_threshold(self, adapter: CoreScoringAdapter) -> None:
        """Neutral/clean financials should produce M < -1.78."""
        m = adapter.compute_beneish_m(
            current={
                "receivables": 5_000_000,
                "revenue": 100_000_000,
                "gross_profit": 40_000_000,
                "total_assets": 200_000_000,
                "ppe": 50_000_000,
                "depreciation": 10_000_000,
                "sga": 20_000_000,
                "total_liabilities": 80_000_000,
                "net_income": 15_000_000,
                "operating_cashflow": 20_000_000,
            },
            previous={
                "receivables": 5_000_000,
                "revenue": 95_000_000,
                "gross_profit": 38_000_000,
                "total_assets": 190_000_000,
                "ppe": 48_000_000,
                "depreciation": 9_500_000,
                "sga": 19_000_000,
                "total_liabilities": 78_000_000,
                "net_income": 14_000_000,
                "operating_cashflow": 18_000_000,
            },
        )
        assert isinstance(m, float)
        assert m < -1.78, f"Clean company M should be < -1.78, got {m}"

    def test_manipulation_suspect_m_score_above_threshold(self, adapter: CoreScoringAdapter) -> None:
        """Company with aggressive accounting signals should produce M > -1.78."""
        m = adapter.compute_beneish_m(
            current={
                "receivables": 20_000_000,  # receivables spike (DSRI high)
                "revenue": 100_000_000,
                "gross_profit": 30_000_000,  # margin squeeze (GMI high)
                "total_assets": 200_000_000,
                "ppe": 30_000_000,  # low PP&E (AQI high)
                "depreciation": 5_000_000,  # low depreciation (DEPI high)
                "sga": 30_000_000,  # high SGA
                "total_liabilities": 120_000_000,  # high leverage
                "net_income": 5_000_000,  # low income
                "operating_cashflow": 2_000_000,  # low cashflow (TATA high)
            },
            previous={
                "receivables": 8_000_000,  # was much lower -> spike
                "revenue": 70_000_000,  # revenue grew fast (SGI high)
                "gross_profit": 35_000_000,  # was higher margin
                "total_assets": 150_000_000,
                "ppe": 40_000_000,
                "depreciation": 8_000_000,
                "sga": 18_000_000,
                "total_liabilities": 80_000_000,
                "net_income": 10_000_000,
                "operating_cashflow": 12_000_000,
            },
        )
        assert isinstance(m, float)
        assert m > -1.78, f"Manipulation suspect M should be > -1.78, got {m}"


# ── Piotroski F-Score ───────────────────────────────────────────────────


class TestPiotroskiFScore:
    """Reference-value tests for Piotroski F-Score via adapter."""

    def test_good_fundamentals_high_f_score(self, adapter: CoreScoringAdapter) -> None:
        """Company with strong fundamentals should score 6+."""
        f = adapter.compute_piotroski_f({
            "roa": 0.15,
            "fcf": 1_000_000_000,
            "debt_to_equity": 0.3,
            "current_ratio": 2.0,
            "roe": 0.30,
            "revenue": 10_000_000_000,
            "market_cap": 50_000_000_000,
        })
        assert isinstance(f, int)
        assert 0 <= f <= 9
        assert f >= 6, f"Good fundamentals should score >= 6, got {f}"

    def test_poor_fundamentals_low_f_score(self, adapter: CoreScoringAdapter) -> None:
        """Company with poor fundamentals should score < 5."""
        f = adapter.compute_piotroski_f({
            "roa": -0.05,
            "fcf": -100_000_000,
            "debt_to_equity": 3.0,
            "current_ratio": 0.5,
            "roe": -0.10,
            "revenue": 100_000_000,
            "market_cap": 500_000_000,
        })
        assert isinstance(f, int)
        assert 0 <= f <= 9
        assert f < 5, f"Poor fundamentals should score < 5, got {f}"

    def test_returns_int_in_range(self, adapter: CoreScoringAdapter) -> None:
        """F-Score must always be int in [0, 9]."""
        f = adapter.compute_piotroski_f({})
        assert isinstance(f, int)
        assert 0 <= f <= 9


# ── Safety Gate ─────────────────────────────────────────────────────────


class TestSafetyGate:
    """Tests for SafetyGate VO creation through adapter."""

    def test_both_conditions_pass(self, adapter: CoreScoringAdapter) -> None:
        """Z > 1.81 AND M < -1.78 -> passes."""
        gate = adapter.check_safety_gate(z_score=3.0, m_score=-2.5)
        assert isinstance(gate, SafetyGate)
        assert gate.passed is True
        assert gate.z_score == 3.0
        assert gate.m_score == -2.5

    def test_z_fails_even_if_m_passes(self, adapter: CoreScoringAdapter) -> None:
        """Z <= 1.81 -> fails, regardless of M."""
        gate = adapter.check_safety_gate(z_score=1.0, m_score=-2.5)
        assert gate.passed is False

    def test_m_fails_even_if_z_passes(self, adapter: CoreScoringAdapter) -> None:
        """M >= -1.78 -> fails, regardless of Z."""
        gate = adapter.check_safety_gate(z_score=3.0, m_score=-1.0)
        assert gate.passed is False

    def test_boundary_z_at_threshold_fails(self, adapter: CoreScoringAdapter) -> None:
        """Z exactly at 1.81 -> fails (must be strictly greater)."""
        gate = adapter.check_safety_gate(z_score=1.81, m_score=-2.5)
        assert gate.passed is False

    def test_boundary_m_at_threshold_fails(self, adapter: CoreScoringAdapter) -> None:
        """M exactly at -1.78 -> fails (must be strictly less)."""
        gate = adapter.check_safety_gate(z_score=3.0, m_score=-1.78)
        assert gate.passed is False

    def test_healthy_company_full_flow(self, adapter: CoreScoringAdapter) -> None:
        """AAPL-like data through compute -> check -> SafetyGate passes."""
        z = adapter.compute_altman_z({
            "working_capital": 5_000_000_000,
            "total_assets": 50_000_000_000,
            "retained_earnings": 15_000_000_000,
            "ebit": 8_000_000_000,
            "market_cap": 100_000_000_000,
            "total_liabilities": 30_000_000_000,
            "revenue": 60_000_000_000,
        })
        # Use neutral M-Score to isolate Z
        gate = adapter.check_safety_gate(z_score=z, m_score=-3.0)
        assert gate.passed is True

    def test_distressed_company_full_flow(self, adapter: CoreScoringAdapter) -> None:
        """Distressed company through compute -> check -> SafetyGate fails."""
        z = adapter.compute_altman_z({
            "working_capital": -2_000_000_000,
            "total_assets": 10_000_000_000,
            "retained_earnings": -1_000_000_000,
            "ebit": -500_000_000,
            "market_cap": 2_000_000_000,
            "total_liabilities": 12_000_000_000,
            "revenue": 5_000_000_000,
        })
        gate = adapter.check_safety_gate(z_score=z, m_score=-3.0)
        assert gate.passed is False


# ── Full Fundamental Score ──────────────────────────────────────────────


class TestFullFundamental:
    """Tests for compute_full_fundamental delegation."""

    def test_returns_dict_with_expected_keys(self, adapter: CoreScoringAdapter) -> None:
        """compute_full_fundamental delegates to core and returns result dict."""
        result = adapter.compute_full_fundamental(
            highlights={
                "market_cap": 2_500_000_000_000,
                "revenue": 400_000_000_000,
                "net_income": 97_000_000_000,
                "debt_to_equity": 0.5,
                "current_ratio": 1.5,
                "roa": 0.18,
                "roe": 0.45,
                "fcf": 90_000_000_000,
                "pe_ratio": 28.5,
            },
            valuation={"pb": 3.5},
        )
        assert isinstance(result, dict)
        assert "fundamental_score" in result
        assert "f_score" in result
        assert "safety_passed" in result
