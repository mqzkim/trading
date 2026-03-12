"""Tests for TakeProfitLevels VO (RISK-03)."""
from __future__ import annotations

import pytest

from src.portfolio.domain.value_objects import TakeProfitLevels


class TestTakeProfitLevels:
    """TakeProfitLevels VO tests."""

    def test_standard_levels(self) -> None:
        """entry=100, intrinsic=150 produces 3 levels at 50%/75%/100% of gap."""
        tp = TakeProfitLevels(entry_price=100.0, intrinsic_value=150.0)
        levels = tp.levels

        assert len(levels) == 3
        assert levels[0] == {"pct": 0.50, "price": 125.0, "action": "sell_25pct"}
        assert levels[1] == {"pct": 0.75, "price": 137.5, "action": "sell_25pct"}
        assert levels[2] == {"pct": 1.00, "price": 150.0, "action": "sell_remaining"}

    def test_no_upside_equal_prices(self) -> None:
        """entry == intrinsic returns empty levels list."""
        tp = TakeProfitLevels(entry_price=100.0, intrinsic_value=100.0)
        assert tp.levels == []
        assert tp.has_upside is False

    def test_no_upside_overvalued(self) -> None:
        """entry > intrinsic returns empty levels list."""
        tp = TakeProfitLevels(entry_price=150.0, intrinsic_value=100.0)
        assert tp.levels == []
        assert tp.has_upside is False

    def test_has_upside_true(self) -> None:
        """intrinsic > entry means has_upside is True."""
        tp = TakeProfitLevels(entry_price=80.0, intrinsic_value=120.0)
        assert tp.has_upside is True

    def test_small_gap(self) -> None:
        """Small gap still produces 3 levels with correct rounding."""
        tp = TakeProfitLevels(entry_price=99.0, intrinsic_value=100.0)
        levels = tp.levels

        assert len(levels) == 3
        # gap = 1.0
        assert levels[0]["price"] == 99.5   # 99 + 0.5*1
        assert levels[1]["price"] == 99.75  # 99 + 0.75*1
        assert levels[2]["price"] == 100.0  # 99 + 1.0*1

    def test_validates_entry_price_positive(self) -> None:
        """entry_price must be > 0."""
        with pytest.raises(ValueError):
            TakeProfitLevels(entry_price=0.0, intrinsic_value=100.0)

    def test_validates_entry_price_negative(self) -> None:
        """entry_price must be > 0."""
        with pytest.raises(ValueError):
            TakeProfitLevels(entry_price=-10.0, intrinsic_value=100.0)

    def test_validates_intrinsic_value_positive(self) -> None:
        """intrinsic_value must be > 0."""
        with pytest.raises(ValueError):
            TakeProfitLevels(entry_price=100.0, intrinsic_value=0.0)

    def test_validates_intrinsic_value_negative(self) -> None:
        """intrinsic_value must be > 0."""
        with pytest.raises(ValueError):
            TakeProfitLevels(entry_price=100.0, intrinsic_value=-50.0)

    def test_rounding_precision(self) -> None:
        """Prices rounded to 2 decimal places."""
        tp = TakeProfitLevels(entry_price=33.33, intrinsic_value=66.67)
        levels = tp.levels
        # gap = 33.34
        for level in levels:
            assert level["price"] == round(level["price"], 2)
