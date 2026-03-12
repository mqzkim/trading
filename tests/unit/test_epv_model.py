"""Tests for EPV valuation model pure math.

Covers: compute_epv() with 5-year margin averaging, maintenance capex proxy,
cyclical detection, and edge cases.
"""
from __future__ import annotations

import pytest

from core.valuation.epv import compute_epv


class TestComputeEPV:
    def test_stable_margins_positive_epv(self) -> None:
        """Stable margins with normal inputs produce positive EPV."""
        result = compute_epv(
            revenues=[1_000_000.0] * 5,
            operating_margins=[0.12] * 5,
            tax_rate=0.21,
            depreciation=20_000.0,
            wacc=0.10,
            shares_outstanding=10_000.0,
        )
        assert result["epv_total"] > 0
        assert result["epv_per_share"] > 0

    def test_uses_5year_average_margin(self) -> None:
        """Normalized margin is average of all 5 operating margins."""
        margins = [0.08, 0.10, 0.12, 0.14, 0.16]
        result = compute_epv(
            revenues=[1_000_000.0] * 5,
            operating_margins=margins,
            tax_rate=0.21,
            depreciation=20_000.0,
            wacc=0.10,
            shares_outstanding=10_000.0,
        )
        expected_margin = sum(margins) / len(margins)
        assert result["normalized_margin"] == pytest.approx(
            expected_margin, rel=1e-6
        )

    def test_maintenance_capex_is_depreciation_times_1_1(self) -> None:
        """Maintenance CapEx = depreciation * 1.1."""
        depreciation = 50_000.0
        result = compute_epv(
            revenues=[2_000_000.0] * 5,
            operating_margins=[0.15] * 5,
            tax_rate=0.21,
            depreciation=depreciation,
            wacc=0.10,
            shares_outstanding=10_000.0,
        )
        # adjusted_earnings = NOPAT + depreciation - maintenance_capex
        # maintenance_capex = depreciation * 1.1
        # So adjusted = NOPAT + depreciation - depreciation*1.1
        #             = NOPAT - depreciation*0.1
        normalized_ebit = 2_000_000.0 * 0.15
        nopat = normalized_ebit * (1 - 0.21)
        maintenance_capex = depreciation * 1.1
        expected_adjusted = nopat + depreciation - maintenance_capex
        assert result["adjusted_earnings"] == pytest.approx(
            expected_adjusted, rel=1e-6
        )

    def test_zero_wacc_returns_zero_epv(self) -> None:
        """WACC=0 -> EPV=0 with confidence=0 (division by zero guard)."""
        result = compute_epv(
            revenues=[1_000_000.0] * 5,
            operating_margins=[0.10] * 5,
            tax_rate=0.21,
            depreciation=10_000.0,
            wacc=0.0,
            shares_outstanding=10_000.0,
        )
        assert result["epv_total"] == 0.0
        assert result["confidence"] == 0

    def test_high_cv_flags_cyclical(self) -> None:
        """Earnings CV > 0.5 flags cyclical warning."""
        # Highly variable margins -> high CV of annual earnings
        margins = [0.02, 0.20, 0.05, 0.25, 0.03]
        result = compute_epv(
            revenues=[1_000_000.0, 1_200_000.0, 800_000.0, 1_500_000.0, 900_000.0],
            operating_margins=margins,
            tax_rate=0.21,
            depreciation=20_000.0,
            wacc=0.10,
            shares_outstanding=10_000.0,
        )
        assert result["earnings_cv"] is not None
        assert result["earnings_cv"] > 0.5

    def test_zero_shares_returns_zero_per_share(self) -> None:
        """Zero shares_outstanding -> per_share=0 (no division error)."""
        result = compute_epv(
            revenues=[1_000_000.0] * 5,
            operating_margins=[0.10] * 5,
            tax_rate=0.21,
            depreciation=10_000.0,
            wacc=0.10,
            shares_outstanding=0.0,
        )
        assert result["epv_per_share"] == 0.0
        assert result["epv_total"] > 0
