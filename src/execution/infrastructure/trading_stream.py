"""Execution Infrastructure -- TradingStreamAdapter.

WebSocket wrapper for Alpaca TradingStream. Publishes OrderFilledEvent
on fill/partial_fill and coordinates with AlpacaOrderMonitor to prevent
duplicate tracking.
"""
from __future__ import annotations

import logging
import threading

from alpaca.trading.stream import TradingStream

from src.execution.domain.events import OrderFilledEvent

logger = logging.getLogger(__name__)

# Events that represent a fill
FILL_EVENTS = {"fill", "partial_fill"}


class TradingStreamAdapter:
    """WebSocket wrapper for real-time trade updates.

    Subscribes to Alpaca TradingStream and publishes OrderFilledEvent
    for fill/partial_fill events. Coordinates with AlpacaOrderMonitor
    to remove filled orders from the polling set.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool,
        bus: object,
        monitor: object | None = None,
    ) -> None:
        self._bus = bus
        self._monitor = monitor
        self._stream = TradingStream(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
        )
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Subscribe to trade updates and run stream in daemon thread."""
        self._stream.subscribe_trade_updates(self._on_trade_update)
        self._thread = threading.Thread(
            target=self._stream.run,
            name="trading-stream",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the stream and wait for thread."""
        try:
            self._stream.stop()
        except Exception:
            logger.exception("Error stopping trading stream")

        if self._thread is not None:
            self._thread.join(timeout=10.0)

    async def _on_trade_update(self, data: object) -> None:
        """Handle trade update from WebSocket.

        On fill/partial_fill: publish OrderFilledEvent, remove from monitor.
        All other events are ignored.
        """
        event_type = getattr(data, "event", "")
        if hasattr(event_type, "value"):
            event_type = event_type.value
        event_type = str(event_type).lower()

        if event_type not in FILL_EVENTS:
            return

        order = getattr(data, "order", None)
        if order is None:
            return

        order_id = str(getattr(order, "id", ""))
        symbol = str(getattr(order, "symbol", ""))
        quantity = int(float(getattr(data, "qty", 0) or 0))
        filled_price = float(getattr(data, "price", 0) or 0)
        position_qty = float(getattr(data, "position_qty", 0) or 0)

        fill_event = OrderFilledEvent(
            order_id=order_id,
            symbol=symbol,
            quantity=quantity,
            filled_price=filled_price,
            position_qty=position_qty,
        )
        self._bus.publish(fill_event)

        # Remove from monitor to prevent duplicate processing
        if self._monitor is not None:
            self._monitor.remove_order(order_id)

        logger.info(
            "Trade update: %s %s qty=%d price=%.2f",
            event_type,
            symbol,
            quantity,
            filled_price,
        )
