"""Circuit breaker tests for SafeExecutionAdapter.

Tests that 3 consecutive order failures trip the circuit breaker,
which calls KillSwitchService and notifier, and blocks further orders.
"""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from src.execution.domain.value_objects import ExecutionMode, OrderResult, OrderSpec
from src.execution.infrastructure.safe_adapter import (
    CircuitBreakerTrippedError,
    SafeExecutionAdapter,
)


def _make_adapter(
    *,
    inner: MagicMock | None = None,
    mode: ExecutionMode = ExecutionMode.PAPER,
    max_failures: int = 3,
    notifier: MagicMock | None = None,
    kill_switch: MagicMock | None = None,
) -> SafeExecutionAdapter:
    """Create SafeExecutionAdapter with mocked dependencies."""
    if inner is None:
        inner = MagicMock()
    cooldown_repo = MagicMock()
    cooldown_repo.get_active.return_value = None  # No active cooldown
    return SafeExecutionAdapter(
        inner=inner,
        mode=mode,
        cooldown_repo=cooldown_repo,
        max_failures=max_failures,
        notifier=notifier,
        kill_switch=kill_switch,
    )


def _error_result(symbol: str = "AAPL") -> OrderResult:
    return OrderResult(order_id="", status="error", symbol=symbol, quantity=0)


def _success_result(symbol: str = "AAPL") -> OrderResult:
    return OrderResult(
        order_id="ord-1", status="filled", symbol=symbol, quantity=10, filled_price=150.0
    )


def _spec() -> OrderSpec:
    return OrderSpec(
        symbol="AAPL",
        quantity=10,
        entry_price=150.0,
        direction="BUY",
    )


class TestCircuitBreakerTripsAfter3Failures:
    def test_trips_after_3_consecutive_failures(self):
        inner = MagicMock()
        inner.submit_order.return_value = _error_result()
        adapter = _make_adapter(inner=inner)

        # 3 failures
        for _ in range(3):
            adapter.submit_order(_spec())

        # 4th should raise
        with pytest.raises(CircuitBreakerTrippedError):
            adapter.submit_order(_spec())


class TestCircuitBreakerResetsOnSuccess:
    def test_resets_counter_on_success(self):
        inner = MagicMock()
        adapter = _make_adapter(inner=inner)

        # 2 failures
        inner.submit_order.return_value = _error_result()
        adapter.submit_order(_spec())
        adapter.submit_order(_spec())

        # 1 success resets counter
        inner.submit_order.return_value = _success_result()
        adapter.submit_order(_spec())

        # 3 more failures needed to trip
        inner.submit_order.return_value = _error_result()
        adapter.submit_order(_spec())
        adapter.submit_order(_spec())
        adapter.submit_order(_spec())

        # Now should trip
        with pytest.raises(CircuitBreakerTrippedError):
            adapter.submit_order(_spec())


class TestCircuitBreakerCallsKillSwitch:
    def test_calls_kill_switch_on_trip(self):
        inner = MagicMock()
        inner.submit_order.return_value = _error_result()
        kill_switch = MagicMock()
        adapter = _make_adapter(inner=inner, kill_switch=kill_switch)

        for _ in range(3):
            adapter.submit_order(_spec())

        kill_switch.execute.assert_called_once_with(liquidate=False)


class TestCircuitBreakerSendsNotification:
    def test_sends_notification_on_trip(self):
        inner = MagicMock()
        inner.submit_order.return_value = _error_result()
        notifier = MagicMock()
        adapter = _make_adapter(inner=inner, notifier=notifier)

        for _ in range(3):
            adapter.submit_order(_spec())

        notifier.notify.assert_called_once()
        msg = notifier.notify.call_args[0][0]
        assert "circuit breaker" in msg.lower()


class TestCircuitBreakerResetMethod:
    def test_reset_clears_tripped_state(self):
        inner = MagicMock()
        inner.submit_order.return_value = _error_result()
        adapter = _make_adapter(inner=inner)

        # Trip it
        for _ in range(3):
            adapter.submit_order(_spec())

        # Verify tripped
        with pytest.raises(CircuitBreakerTrippedError):
            adapter.submit_order(_spec())

        # Reset
        adapter.reset_circuit_breaker()

        # Should work again
        inner.submit_order.return_value = _success_result()
        result = adapter.submit_order(_spec())
        assert result.status == "filled"


class TestCircuitBreakerBlocksWhenTripped:
    def test_blocks_all_orders_when_tripped(self):
        inner = MagicMock()
        inner.submit_order.return_value = _error_result()
        adapter = _make_adapter(inner=inner)

        # Trip it
        for _ in range(3):
            adapter.submit_order(_spec())

        # Multiple attempts all blocked
        for _ in range(5):
            with pytest.raises(CircuitBreakerTrippedError):
                adapter.submit_order(_spec())

        # Inner adapter should NOT be called after trip
        assert inner.submit_order.call_count == 3
