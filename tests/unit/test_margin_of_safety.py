"""Tests for compute_margin_of_safety() -- sector-adjusted margin of safety thresholds.

Tests cover:
- Basic MoS calculation: (intrinsic - market) / intrinsic
- Sector-specific thresholds: Tech 25%, Consumer Staples 15%, default 20%
- has_margin flag: True when MoS >= threshold, False otherwise
- Negative MoS when price > intrinsic
"""
from __future__ import annotations

import pytest

from core.valuation.ensemble import compute_margin_of_safety


class TestMarginOfSafetyBasic:
    """Test 1: MoS = (intrinsic - market) / intrinsic."""

    def test_basic_mos_calculation(self) -> None:
        result = compute_margin_of_safety(
            intrinsic_mid=100.0, market_price=70.0, sector="Industrials"
        )
        assert result["margin_of_safety"] == pytest.approx(0.30, abs=0.001)


class TestMarginOfSafetyTechSector:
    """Test 2: Tech sector uses 25% threshold (not default 20%)."""

    def test_tech_uses_25_threshold(self) -> None:
        result = compute_margin_of_safety(
            intrinsic_mid=100.0, market_price=70.0, sector="Information Technology"
        )
        assert result["sector_threshold"] == pytest.approx(0.25, abs=0.001)


class TestMarginOfSafetyConsumerStaples:
    """Test 3: Consumer Staples uses 15% threshold."""

    def test_consumer_staples_uses_15_threshold(self) -> None:
        result = compute_margin_of_safety(
            intrinsic_mid=100.0, market_price=70.0, sector="Consumer Staples"
        )
        assert result["sector_threshold"] == pytest.approx(0.15, abs=0.001)


class TestMarginOfSafetyUnknownSector:
    """Test 4: Unknown sector uses 20% default threshold."""

    def test_unknown_sector_uses_default(self) -> None:
        result = compute_margin_of_safety(
            intrinsic_mid=100.0, market_price=70.0, sector="Unknown Sector"
        )
        assert result["sector_threshold"] == pytest.approx(0.20, abs=0.001)


class TestMarginOfSafetyHasMarginTrue:
    """Test 5: has_margin=True when MoS >= sector threshold."""

    def test_has_margin_true(self) -> None:
        # Industrials threshold = 0.20, MoS = 0.30 >= 0.20
        result = compute_margin_of_safety(
            intrinsic_mid=100.0, market_price=70.0, sector="Industrials"
        )
        assert result["has_margin"] is True

    def test_has_margin_true_at_exact_threshold(self) -> None:
        # Industrials threshold = 0.20, MoS = exactly 0.20
        result = compute_margin_of_safety(
            intrinsic_mid=100.0, market_price=80.0, sector="Industrials"
        )
        assert result["margin_of_safety"] == pytest.approx(0.20, abs=0.001)
        assert result["has_margin"] is True


class TestMarginOfSafetyHasMarginFalse:
    """Test 6: has_margin=False when MoS < sector threshold."""

    def test_has_margin_false(self) -> None:
        # Industrials threshold = 0.20, MoS = 0.10 < 0.20
        result = compute_margin_of_safety(
            intrinsic_mid=100.0, market_price=90.0, sector="Industrials"
        )
        assert result["has_margin"] is False


class TestMarginOfSafetyNegative:
    """Test 7: Price > intrinsic returns negative MoS, has_margin=False."""

    def test_negative_mos_when_overpriced(self) -> None:
        result = compute_margin_of_safety(
            intrinsic_mid=100.0, market_price=120.0, sector="Industrials"
        )
        assert result["margin_of_safety"] == pytest.approx(-0.20, abs=0.001)
        assert result["has_margin"] is False
