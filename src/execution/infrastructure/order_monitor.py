"""Execution Infrastructure -- AlpacaOrderMonitor.

Background thread that polls tracked orders until terminal state.
Cancels stuck orders (default 5 min) with notifier alert.
Publishes OrderFilledEvent for filled orders.
"""
from __future__ import annotations

import logging
import threading
import time

from src.execution.domain.events import OrderFilledEvent

logger = logging.getLogger(__name__)

# Terminal order statuses -- polling stops when order reaches one of these
TERMINAL_STATUSES = {"filled", "canceled", "expired", "rejected", "replaced"}

# Fill statuses that trigger OrderFilledEvent
FILL_STATUSES = {"filled", "partially_filled"}

# Default stuck timeout: 5 minutes
DEFAULT_STUCK_TIMEOUT = 300.0


class AlpacaOrderMonitor:
    """Background thread that tracks submitted orders until terminal state.

    - Polls each tracked order at poll_interval
    - Publishes OrderFilledEvent for fills
    - Auto-cancels stuck orders (5+ minutes) with notifier alert
    - Exits when all tracked orders reach terminal or stop() is called
    """

    def __init__(
        self,
        client: object,
        notifier: object | None = None,
        bus: object | None = None,
        poll_interval: float = 5.0,
        stuck_timeout: float = DEFAULT_STUCK_TIMEOUT,
    ) -> None:
        self._client = client
        self._notifier = notifier
        self._bus = bus
        self._poll_interval = poll_interval
        self._stuck_timeout = stuck_timeout
        self._tracked_orders: dict[str, float] = {}  # order_id -> first_seen monotonic time
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def track(self, order_id: str) -> None:
        """Add an order to the tracked set."""
        with self._lock:
            if order_id not in self._tracked_orders:
                self._tracked_orders[order_id] = time.monotonic()

    def remove_order(self, order_id: str) -> None:
        """Remove an order from tracking (called by WebSocket on fill to prevent duplicates)."""
        with self._lock:
            self._tracked_orders.pop(order_id, None)

    def start(self) -> None:
        """Start the monitor loop in a daemon thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._monitor_loop,
            name="order-monitor",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 30.0) -> None:
        """Signal the monitor to stop and wait for thread join."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _monitor_loop(self) -> None:
        """Main polling loop: check each tracked order, handle terminal/stuck."""
        while not self._stop_event.is_set():
            with self._lock:
                order_ids = list(self._tracked_orders.keys())

            if not order_ids:
                self._stop_event.wait(self._poll_interval)
                continue  # Wait for new orders instead of exiting

            for order_id in order_ids:
                if self._stop_event.is_set():
                    break

                try:
                    self._check_order(order_id)
                except Exception:
                    logger.exception("Error checking order %s", order_id)

            self._stop_event.wait(self._poll_interval)

    def _check_order(self, order_id: str) -> None:
        """Poll a single order: detect terminal state or stuck condition."""
        status = self._poll_status(order_id)

        if status in TERMINAL_STATUSES:
            # Get fill details for event
            if status == "filled":
                self._publish_fill_event(order_id)

            with self._lock:
                self._tracked_orders.pop(order_id, None)
            return

        # Check for stuck order
        with self._lock:
            first_seen = self._tracked_orders.get(order_id)

        if first_seen is not None:
            elapsed = time.monotonic() - first_seen
            if elapsed >= self._stuck_timeout:
                self._cancel_stuck(order_id)

    def _poll_status(self, order_id: str) -> str:
        """Get current order status from broker client."""
        order = self._client.get_order_by_id(order_id)
        status = order.status
        if hasattr(status, "value"):
            status = status.value
        return str(status).lower()

    def _publish_fill_event(self, order_id: str) -> None:
        """Publish OrderFilledEvent for a filled order."""
        if self._bus is None:
            return

        try:
            order = self._client.get_order_by_id(order_id)
            filled_price = (
                float(order.filled_avg_price)
                if hasattr(order, "filled_avg_price") and order.filled_avg_price
                else 0.0
            )
            quantity = (
                int(float(order.filled_qty))
                if hasattr(order, "filled_qty") and order.filled_qty
                else 0
            )
            symbol = getattr(order, "symbol", "")

            event = OrderFilledEvent(
                order_id=order_id,
                symbol=symbol,
                quantity=quantity,
                filled_price=filled_price,
            )
            self._bus.publish(event)
        except Exception:
            logger.exception("Failed to publish fill event for order %s", order_id)

    def _cancel_stuck(self, order_id: str) -> None:
        """Cancel a stuck order and notify."""
        try:
            self._client.cancel_order_by_id(order_id)
            logger.warning("Auto-canceled stuck order %s", order_id)
        except Exception:
            logger.exception("Failed to cancel stuck order %s", order_id)

        with self._lock:
            self._tracked_orders.pop(order_id, None)

        if self._notifier is not None:
            try:
                self._notifier.notify(
                    f"Stuck order auto-canceled: {order_id} "
                    f"(exceeded {self._stuck_timeout:.0f}s timeout)"
                )
            except Exception:
                logger.exception("Notifier failed for stuck order %s", order_id)
