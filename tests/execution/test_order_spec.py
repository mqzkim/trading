"""Tests for OrderSpec VO — generalized order specification with optional stop/target."""
from __future__ import annotations

import pytest

from src.execution.domain.value_objects import BracketSpec, OrderSpec


class TestOrderSpecOptionalFields:
    """OrderSpec accepts None for stop_loss_price and take_profit_price."""

    def test_minimal_order_spec_valid(self):
        """OrderSpec with only symbol/quantity/entry_price/direction is valid."""
        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            direction="BUY",
        )
        assert spec.symbol == "AAPL"
        assert spec.stop_loss_price is None
        assert spec.take_profit_price is None

    def test_none_stop_loss_and_take_profit(self):
        """Explicit None values do not raise."""
        spec = OrderSpec(
            symbol="005930",
            quantity=5,
            entry_price=70000.0,
            direction="BUY",
            stop_loss_price=None,
            take_profit_price=None,
        )
        assert spec.stop_loss_price is None
        assert spec.take_profit_price is None

    def test_sell_direction_no_stop_loss_valid(self):
        """SELL orders without stop_loss_price are valid (no ValueError)."""
        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            direction="SELL",
        )
        assert spec.direction == "SELL"

    def test_buy_with_stop_loss_validates(self):
        """BUY with stop_loss_price must have stop < entry."""
        with pytest.raises(ValueError, match="stop_loss_price"):
            OrderSpec(
                symbol="AAPL",
                quantity=10,
                entry_price=150.0,
                direction="BUY",
                stop_loss_price=160.0,
                take_profit_price=170.0,
            )

    def test_buy_with_valid_bracket(self):
        """Full bracket still works."""
        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            direction="BUY",
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        assert spec.stop_loss_price == 140.0
        assert spec.take_profit_price == 170.0


class TestBracketSpecAlias:
    """BracketSpec is a backward-compatible alias for OrderSpec."""

    def test_bracket_spec_is_order_spec(self):
        spec = BracketSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            direction="BUY",
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        assert isinstance(spec, OrderSpec)
