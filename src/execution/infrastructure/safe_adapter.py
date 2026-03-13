"""Execution Infrastructure -- SafeExecutionAdapter.

Decorator that wraps any IBrokerAdapter with:
- Cooldown enforcement (blocks orders during drawdown cooldown)
- Order status polling until terminal state (LIVE mode only)
- Bracket leg verification after fill (LIVE mode only)
"""
from __future__ import annotations

import logging
import time

from src.execution.domain.repositories import IBrokerAdapter, ICooldownRepository
from src.execution.domain.value_objects import (
    CooldownState,
    ExecutionMode,
    OrderResult,
    OrderSpec,
)

logger = logging.getLogger(__name__)

# Terminal order statuses -- polling stops when order reaches one of these
TERMINAL_STATUSES = {"filled", "canceled", "expired", "rejected", "replaced"}

# Active bracket leg statuses -- legs should be in one of these after fill
ACTIVE_LEG_STATUSES = {"new", "held", "accepted"}


class CooldownActiveError(Exception):
    """Raised when order submission is blocked by active cooldown."""

    def __init__(self, cooldown: CooldownState) -> None:
        self.cooldown = cooldown
        super().__init__(
            f"Cooldown active (tier {cooldown.current_tier}%, "
            f"expires {cooldown.expires_at.isoformat()}, "
            f"reason: {cooldown.reason})"
        )


class OrderTimeoutError(Exception):
    """Raised when order polling exceeds timeout."""

    def __init__(self, order_id: str, timeout: float) -> None:
        self.order_id = order_id
        self.timeout = timeout
        super().__init__(
            f"Order {order_id} did not reach terminal state within {timeout}s"
        )


class BracketLegError(Exception):
    """Bracket leg verification failure (logged as warning, not raised to caller)."""

    def __init__(self, order_id: str, message: str) -> None:
        self.order_id = order_id
        super().__init__(message)


class CircuitBreakerTrippedError(Exception):
    """Raised when circuit breaker is tripped after consecutive failures."""

    def __init__(self, failure_count: int) -> None:
        self.failure_count = failure_count
        super().__init__(
            f"Circuit breaker tripped after {failure_count} consecutive failures"
        )


class SafeExecutionAdapter(IBrokerAdapter):
    """Decorator wrapping any IBrokerAdapter with safety enforcement.

    - Checks cooldown before every order submission
    - Circuit breaker: trips after max_failures consecutive errors
    - In LIVE mode: polls order status until terminal, verifies bracket legs
    - In PAPER mode: passes through to inner adapter without polling
    """

    def __init__(
        self,
        inner: IBrokerAdapter,
        mode: ExecutionMode,
        cooldown_repo: ICooldownRepository,
        poll_interval: float = 2.0,
        poll_timeout: float = 60.0,
        max_failures: int = 3,
        notifier: object | None = None,
        kill_switch: object | None = None,
    ) -> None:
        self._inner = inner
        self._mode = mode
        self._cooldown_repo = cooldown_repo
        self._poll_interval = poll_interval
        self._poll_timeout = poll_timeout
        self._max_failures = max_failures
        self._notifier = notifier
        self._kill_switch = kill_switch
        self._consecutive_failures: int = 0
        self._circuit_tripped: bool = False

    def submit_order(self, spec: OrderSpec) -> OrderResult:
        """Submit order with cooldown check, circuit breaker, and optional polling.

        Raises CooldownActiveError if active cooldown exists.
        Raises CircuitBreakerTrippedError if circuit breaker is tripped.
        In LIVE mode, polls until terminal state and verifies bracket legs.
        In PAPER mode, passes through without polling.
        """
        # Check circuit breaker first
        if self._circuit_tripped:
            raise CircuitBreakerTrippedError(self._consecutive_failures)

        # Check cooldown before submission
        active_cooldown = self._cooldown_repo.get_active()
        if active_cooldown is not None:
            raise CooldownActiveError(active_cooldown)

        # Submit via inner adapter
        result = self._inner.submit_order(spec)

        # Track consecutive failures for circuit breaker
        if result.status == "error":
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures:
                self._trip_circuit_breaker()
        else:
            self._consecutive_failures = 0

        # LIVE mode: poll and verify
        if self._mode == ExecutionMode.LIVE and result.status != "error":
            result = self._poll_order_status(result.order_id)
            if result.status == "filled":
                self._verify_bracket_legs(result.order_id)

        return result

    def _trip_circuit_breaker(self) -> None:
        """Trip circuit breaker: block orders, call kill switch, notify."""
        self._circuit_tripped = True
        logger.error(
            "Circuit breaker tripped after %d consecutive failures",
            self._consecutive_failures,
        )

        if self._kill_switch is not None:
            try:
                self._kill_switch.execute(liquidate=False)
            except Exception:
                logger.exception("Kill switch failed during circuit breaker trip")

        if self._notifier is not None:
            try:
                self._notifier.notify(
                    f"Circuit breaker tripped: {self._consecutive_failures} "
                    f"consecutive order failures. All trading halted."
                )
            except Exception:
                logger.exception("Notifier failed during circuit breaker trip")

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker -- clears tripped state and failure counter."""
        self._consecutive_failures = 0
        self._circuit_tripped = False
        logger.info("Circuit breaker reset")

    def get_positions(self) -> list[dict]:
        """Delegate to inner adapter."""
        return self._inner.get_positions()

    def get_account(self) -> dict:
        """Delegate to inner adapter."""
        return self._inner.get_account()

    def _poll_order_status(self, order_id: str) -> OrderResult:
        """Poll order until terminal status or timeout.

        Uses inner adapter's _client.get_order_by_id().
        Raises OrderTimeoutError if timeout exceeded.
        """
        client = self._inner._client  # type: ignore[attr-defined]
        start = time.monotonic()

        while True:
            order = client.get_order_by_id(order_id)
            status = order.status.value if hasattr(order.status, "value") else str(order.status)

            if status in TERMINAL_STATUSES:
                filled_price = (
                    float(order.filled_avg_price)
                    if hasattr(order, "filled_avg_price") and order.filled_avg_price
                    else None
                )
                return OrderResult(
                    order_id=order_id,
                    status=status,
                    symbol="",  # not available from order object directly
                    quantity=0,
                    filled_price=filled_price,
                )

            elapsed = time.monotonic() - start
            if elapsed >= self._poll_timeout:
                raise OrderTimeoutError(order_id=order_id, timeout=self._poll_timeout)

            time.sleep(self._poll_interval)

    def _verify_bracket_legs(self, order_id: str) -> None:
        """Verify bracket order legs are active after fill.

        Checks that order has 2 legs with active statuses.
        Logs warning on unexpected status but does NOT raise.
        """
        try:
            client = self._inner._client  # type: ignore[attr-defined]
            order = client.get_order_by_id(order_id)

            # Check if this is a bracket order
            order_class = getattr(order, "order_class", None)
            if order_class is None:
                return  # Not a bracket order, skip
            order_class_str = str(order_class).lower()
            if "bracket" not in order_class_str:
                return  # Not a bracket order, skip

            # Verify legs
            legs = getattr(order, "legs", None)
            if not legs:
                logger.warning(
                    "Bracket order %s has no legs -- stop-loss/take-profit may not be active",
                    order_id,
                )
                return

            if len(legs) < 2:
                logger.warning(
                    "Bracket order %s has only %d leg(s), expected 2",
                    order_id,
                    len(legs),
                )

            for i, leg in enumerate(legs):
                leg_status = leg.status.value if hasattr(leg.status, "value") else str(leg.status)
                if leg_status not in ACTIVE_LEG_STATUSES:
                    logger.warning(
                        "Bracket order %s leg %d has unexpected status: %s",
                        order_id,
                        i,
                        leg_status,
                    )

        except Exception as e:
            logger.warning(
                "Failed to verify bracket legs for order %s: %s",
                order_id,
                e,
            )
