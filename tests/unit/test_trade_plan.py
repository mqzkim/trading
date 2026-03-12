"""Unit tests for execution domain: TradePlan, BracketSpec, OrderResult VOs and TradePlanService."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.execution.domain.value_objects import (
    BracketSpec,
    OrderResult,
    TradePlan,
    TradePlanStatus,
)
from src.execution.domain.events import (
    OrderExecutedEvent,
    OrderFailedEvent,
    TradePlanCreatedEvent,
)
from src.execution.domain.services import TradePlanService


# ── TradePlan VO ──────────────────────────────────────────────────────


class TestTradePlan:
    def test_create_valid_buy_plan(self):
        plan = TradePlan(
            symbol="AAPL",
            direction="BUY",
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
            quantity=10,
            position_value=1500.0,
            reasoning_trace="Strong fundamentals",
            composite_score=78.5,
            margin_of_safety=0.25,
            signal_direction="BUY",
        )
        assert plan.symbol == "AAPL"
        assert plan.direction == "BUY"
        assert plan.quantity == 10

    def test_rejects_zero_entry_price(self):
        with pytest.raises(ValueError, match="entry_price"):
            TradePlan(
                symbol="AAPL",
                direction="BUY",
                entry_price=0.0,
                stop_loss_price=140.0,
                take_profit_price=170.0,
                quantity=10,
                position_value=1500.0,
                reasoning_trace="test",
                composite_score=50.0,
                margin_of_safety=0.1,
                signal_direction="BUY",
            )

    def test_rejects_negative_entry_price(self):
        with pytest.raises(ValueError, match="entry_price"):
            TradePlan(
                symbol="AAPL",
                direction="BUY",
                entry_price=-10.0,
                stop_loss_price=140.0,
                take_profit_price=170.0,
                quantity=10,
                position_value=1500.0,
                reasoning_trace="test",
                composite_score=50.0,
                margin_of_safety=0.1,
                signal_direction="BUY",
            )

    def test_rejects_zero_quantity(self):
        with pytest.raises(ValueError, match="quantity"):
            TradePlan(
                symbol="AAPL",
                direction="BUY",
                entry_price=150.0,
                stop_loss_price=140.0,
                take_profit_price=170.0,
                quantity=0,
                position_value=1500.0,
                reasoning_trace="test",
                composite_score=50.0,
                margin_of_safety=0.1,
                signal_direction="BUY",
            )

    def test_rejects_stop_above_entry_for_buy(self):
        with pytest.raises(ValueError, match="stop_loss_price"):
            TradePlan(
                symbol="AAPL",
                direction="BUY",
                entry_price=150.0,
                stop_loss_price=160.0,
                take_profit_price=170.0,
                quantity=10,
                position_value=1500.0,
                reasoning_trace="test",
                composite_score=50.0,
                margin_of_safety=0.1,
                signal_direction="BUY",
            )

    def test_rejects_take_profit_below_entry_for_buy(self):
        with pytest.raises(ValueError, match="take_profit_price"):
            TradePlan(
                symbol="AAPL",
                direction="BUY",
                entry_price=150.0,
                stop_loss_price=140.0,
                take_profit_price=140.0,
                quantity=10,
                position_value=1500.0,
                reasoning_trace="test",
                composite_score=50.0,
                margin_of_safety=0.1,
                signal_direction="BUY",
            )


class TestTradePlanStatus:
    def test_all_statuses_exist(self):
        assert TradePlanStatus.PENDING.value == "PENDING"
        assert TradePlanStatus.APPROVED.value == "APPROVED"
        assert TradePlanStatus.REJECTED.value == "REJECTED"
        assert TradePlanStatus.MODIFIED.value == "MODIFIED"
        assert TradePlanStatus.EXECUTED.value == "EXECUTED"
        assert TradePlanStatus.FAILED.value == "FAILED"


# ── BracketSpec VO ────────────────────────────────────────────────────


class TestBracketSpec:
    def test_create_valid_bracket_spec(self):
        spec = BracketSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        assert spec.symbol == "AAPL"
        assert spec.quantity == 10

    def test_rejects_invalid_ordering(self):
        with pytest.raises(ValueError):
            BracketSpec(
                symbol="AAPL",
                quantity=10,
                entry_price=150.0,
                stop_loss_price=160.0,
                take_profit_price=170.0,
            )

    def test_rejects_zero_quantity(self):
        with pytest.raises(ValueError, match="quantity"):
            BracketSpec(
                symbol="AAPL",
                quantity=0,
                entry_price=150.0,
                stop_loss_price=140.0,
                take_profit_price=170.0,
            )


# ── OrderResult VO ────────────────────────────────────────────────────


class TestOrderResult:
    def test_create_filled_result(self):
        result = OrderResult(
            order_id="ORD-123",
            status="filled",
            symbol="AAPL",
            quantity=10,
            filled_price=150.25,
        )
        assert result.order_id == "ORD-123"
        assert result.filled_price == 150.25
        assert result.error_message is None

    def test_create_failed_result(self):
        result = OrderResult(
            order_id="ORD-456",
            status="failed",
            symbol="AAPL",
            quantity=10,
            error_message="Insufficient funds",
        )
        assert result.status == "failed"
        assert result.error_message == "Insufficient funds"


# ── Domain Events ─────────────────────────────────────────────────────


class TestDomainEvents:
    def test_trade_plan_created_event(self):
        event = TradePlanCreatedEvent(
            symbol="AAPL", direction="BUY", entry_price=150.0, quantity=10
        )
        assert event.symbol == "AAPL"
        assert event.occurred_on is not None

    def test_order_executed_event(self):
        event = OrderExecutedEvent(
            order_id="ORD-123", symbol="AAPL", quantity=10, filled_price=150.25
        )
        assert event.order_id == "ORD-123"

    def test_order_failed_event(self):
        event = OrderFailedEvent(symbol="AAPL", error_message="API timeout")
        assert event.error_message == "API timeout"


# ── TradePlanService ──────────────────────────────────────────────────


class TestTradePlanService:
    @patch("src.execution.domain.services.plan_entry")
    def test_generate_plan_approved(self, mock_planner):
        mock_planner.return_value = {
            "symbol": "AAPL",
            "status": "APPROVED",
            "order_type": "LIMIT",
            "entry_price": 150.0,
            "limit_price": 149.25,
            "shares": 10,
            "stop_price": 140.0,
            "stop_distance": 10.0,
            "position_value": 1500.0,
            "position_pct": 0.015,
            "risk_pct": 0.01,
            "atr_multiplier": 3.0,
            "drawdown_level": "normal",
        }

        service = TradePlanService()
        plan = service.generate_plan(
            symbol="AAPL",
            entry_price=150.0,
            atr=3.33,
            capital=100000.0,
            peak_value=100000.0,
            current_value=100000.0,
            intrinsic_value=200.0,
            composite_score=78.5,
            margin_of_safety=0.25,
            signal_direction="BUY",
            reasoning_trace="Strong buy signal",
        )

        assert plan is not None
        assert plan.symbol == "AAPL"
        assert plan.direction == "BUY"
        assert plan.entry_price == 150.0
        assert plan.quantity == 10
        assert plan.composite_score == 78.5
        assert plan.reasoning_trace == "Strong buy signal"

    @patch("src.execution.domain.services.plan_entry")
    def test_generate_plan_rejected_returns_none(self, mock_planner):
        mock_planner.return_value = {
            "symbol": "AAPL",
            "status": "REJECTED",
            "violations": ["drawdown_limit"],
            "drawdown_level": "critical",
        }

        service = TradePlanService()
        plan = service.generate_plan(
            symbol="AAPL",
            entry_price=150.0,
            atr=3.33,
            capital=100000.0,
            peak_value=100000.0,
            current_value=75000.0,
            intrinsic_value=200.0,
            composite_score=50.0,
            margin_of_safety=0.1,
            signal_direction="BUY",
            reasoning_trace="Rejected due to drawdown",
        )

        assert plan is None
