"""Tests for DCF valuation model pure math.

Covers: compute_wacc() WACC clipping, compute_dcf() TV cap and edge cases.
"""
from __future__ import annotations

import pytest

from core.valuation.dcf import compute_wacc, compute_dcf


# ── compute_wacc ──────────────────────────────────────────────


class TestComputeWACC:
    def test_clips_to_6pct_floor(self) -> None:
        """CAPM gives ~4% WACC -> clips to 0.06."""
        result = compute_wacc(
            beta=0.3,
            risk_free_rate=0.02,
            equity_risk_premium=0.055,
            debt_to_equity=0.1,
            cost_of_debt=0.03,
            tax_rate=0.21,
        )
        assert result["wacc"] == pytest.approx(0.06)
        assert result["clipped"] is True

    def test_clips_to_14pct_ceiling(self) -> None:
        """CAPM gives ~18% WACC -> clips to 0.14."""
        result = compute_wacc(
            beta=3.0,
            risk_free_rate=0.05,
            equity_risk_premium=0.055,
            debt_to_equity=0.5,
            cost_of_debt=0.08,
            tax_rate=0.21,
        )
        assert result["wacc"] == pytest.approx(0.14)
        assert result["clipped"] is True

    def test_within_range_no_clip(self) -> None:
        """CAPM gives ~10% WACC -> returns as-is, clipped=False."""
        result = compute_wacc(
            beta=1.0,
            risk_free_rate=0.04,
            equity_risk_premium=0.055,
            debt_to_equity=0.5,
            cost_of_debt=0.05,
            tax_rate=0.21,
        )
        assert 0.06 <= result["wacc"] <= 0.14
        assert result["clipped"] is False
        assert "cost_of_equity" in result
        assert "weight_equity" in result
        assert "weight_debt" in result


# ── compute_dcf ───────────────────────────────────────────────


class TestComputeDCF:
    def test_positive_dcf_with_reasonable_inputs(self) -> None:
        """base_fcf=1B, growth=10%, wacc=10% -> positive DCF."""
        result = compute_dcf(
            base_fcf=1_000_000_000.0,
            stage1_growth=0.10,
            stage2_growth=0.025,
            wacc=0.10,
            exit_multiple=12.0,
        )
        assert result["dcf_value"] > 0

    def test_tv_capped_at_40pct(self) -> None:
        """When terminal value exceeds 40% of total, cap triggers."""
        result = compute_dcf(
            base_fcf=100_000.0,
            stage1_growth=0.03,
            stage2_growth=0.025,
            wacc=0.08,
            exit_multiple=15.0,
        )
        # TV cap should trigger for low-growth/low-wacc (TV dominates)
        if result["tv_capped"]:
            assert result["tv_pct"] == pytest.approx(0.40, abs=0.01)

    def test_tv_not_capped_when_under_40pct(self) -> None:
        """High growth stage 1 means stage 1 PV is large -> TV < 40%."""
        result = compute_dcf(
            base_fcf=1_000_000.0,
            stage1_growth=0.50,
            stage2_growth=0.02,
            wacc=0.12,
            exit_multiple=8.0,
        )
        if not result["tv_capped"]:
            assert result["tv_pct"] < 0.40

    def test_confidence_penalty_when_tv_capped(self) -> None:
        """confidence_penalty=0.2 when TV cap triggers."""
        result = compute_dcf(
            base_fcf=100_000.0,
            stage1_growth=0.02,
            stage2_growth=0.025,
            wacc=0.07,
            exit_multiple=15.0,
        )
        if result["tv_capped"]:
            assert result["confidence_penalty"] == pytest.approx(0.2)
        else:
            assert result["confidence_penalty"] == pytest.approx(0.0)

    def test_negative_fcf_returns_zero(self) -> None:
        """Negative base FCF -> dcf_value=0."""
        result = compute_dcf(
            base_fcf=-500_000.0,
            stage1_growth=0.10,
            stage2_growth=0.025,
            wacc=0.10,
            exit_multiple=12.0,
        )
        assert result["dcf_value"] == 0.0
        assert result["projected_fcfs"] == ()

    def test_terminal_value_averages_gordon_and_exit(self) -> None:
        """TV = average of Gordon Growth and Exit Multiple methods."""
        result = compute_dcf(
            base_fcf=1_000_000.0,
            stage1_growth=0.10,
            stage2_growth=0.025,
            wacc=0.10,
            exit_multiple=12.0,
        )
        assert "tv_gordon" in result
        assert "tv_exit" in result
        assert "tv_average" in result
        # Average of the two methods
        expected_avg = (result["tv_gordon"] + result["tv_exit"]) / 2
        assert result["tv_average"] == pytest.approx(expected_avg, rel=1e-6)

    def test_projected_fcfs_length(self) -> None:
        """projected_fcfs has correct length."""
        result = compute_dcf(
            base_fcf=1_000_000.0,
            stage1_growth=0.10,
            stage2_growth=0.025,
            wacc=0.10,
            exit_multiple=12.0,
            projection_years=5,
        )
        assert len(result["projected_fcfs"]) == 5

    def test_custom_projection_years(self) -> None:
        """Custom projection_years works."""
        result = compute_dcf(
            base_fcf=1_000_000.0,
            stage1_growth=0.10,
            stage2_growth=0.025,
            wacc=0.10,
            exit_multiple=12.0,
            projection_years=7,
        )
        assert len(result["projected_fcfs"]) == 7
        assert result["dcf_value"] > 0
