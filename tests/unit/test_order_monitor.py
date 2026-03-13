"""Tests for AlpacaOrderMonitor background thread.

Covers: track/remove orders, terminal state detection, stuck order cancellation,
stop event, WebSocket duplicate prevention.
"""
from __future__ import annotations

import time
import threading
from unittest.mock import MagicMock, patch

import pytest

from src.execution.infrastructure.order_monitor import AlpacaOrderMonitor
from src.execution.domain.events import OrderFilledEvent


class TestOrderMonitorTrack:
    """Test order tracking add/remove."""

    def test_monitor_tracks_order(self):
        """track(order_id) adds to tracked set."""
        monitor = AlpacaOrderMonitor(client=MagicMock(), poll_interval=1.0)
        monitor.track("order-1")
        assert "order-1" in monitor._tracked_orders

    def test_monitor_remove_filled_by_websocket(self):
        """remove_order(id) removes from tracked set (called by stream adapter)."""
        monitor = AlpacaOrderMonitor(client=MagicMock(), poll_interval=1.0)
        monitor.track("order-1")
        monitor.track("order-2")
        monitor.remove_order("order-1")
        assert "order-1" not in monitor._tracked_orders
        assert "order-2" in monitor._tracked_orders

    def test_remove_nonexistent_no_error(self):
        """remove_order for missing id does not raise."""
        monitor = AlpacaOrderMonitor(client=MagicMock(), poll_interval=1.0)
        monitor.remove_order("nonexistent")  # should not raise


class TestOrderMonitorPolling:
    """Test monitor polling loop."""

    def test_monitor_removes_on_terminal(self):
        """Polling detects 'filled' -> removes from tracked, publishes OrderFilledEvent."""
        client = MagicMock()
        bus = MagicMock()

        order_obj = MagicMock()
        order_obj.status = "filled"
        order_obj.filled_avg_price = "150.50"
        order_obj.filled_qty = "10"
        order_obj.symbol = "AAPL"
        client.get_order_by_id.return_value = order_obj

        monitor = AlpacaOrderMonitor(
            client=client, bus=bus, poll_interval=0.01,
        )
        monitor.track("order-1")
        monitor.start()

        # Wait for polling to process
        time.sleep(0.15)
        monitor.stop(timeout=2.0)

        assert "order-1" not in monitor._tracked_orders
        # Should have published OrderFilledEvent
        bus.publish.assert_called()
        event = bus.publish.call_args[0][0]
        assert isinstance(event, OrderFilledEvent)
        assert event.order_id == "order-1"

    def test_monitor_cancels_stuck(self):
        """Order tracked > STUCK_TIMEOUT -> auto-cancel + notifier alert."""
        client = MagicMock()
        notifier = MagicMock()

        order_obj = MagicMock()
        order_obj.status = "new"  # never fills
        client.get_order_by_id.return_value = order_obj

        monitor = AlpacaOrderMonitor(
            client=client, notifier=notifier, poll_interval=0.01,
            stuck_timeout=0.05,  # very short for test
        )
        monitor.track("order-stuck")

        # Backdate the tracked time so it appears stuck
        monitor._tracked_orders["order-stuck"] = time.monotonic() - 1.0

        monitor.start()
        time.sleep(0.15)
        monitor.stop(timeout=2.0)

        client.cancel_order_by_id.assert_called_with("order-stuck")
        notifier.notify.assert_called()

    def test_monitor_persists_when_empty(self):
        """All orders reach terminal -> monitor loop stays alive waiting for new orders."""
        client = MagicMock()

        order_obj = MagicMock()
        order_obj.status = "canceled"
        order_obj.filled_avg_price = None
        order_obj.filled_qty = None
        order_obj.symbol = "AAPL"
        client.get_order_by_id.return_value = order_obj

        monitor = AlpacaOrderMonitor(
            client=client, poll_interval=0.01,
        )
        monitor.track("order-1")
        monitor.start()

        # Wait for loop to process the order and reach empty state
        time.sleep(0.15)

        # Thread should still be alive (persistent loop)
        assert monitor._thread is not None
        assert monitor._thread.is_alive()

        # Clean shutdown
        monitor.stop(timeout=2.0)
        assert not monitor._thread.is_alive()

    def test_monitor_stop_event(self):
        """stop() sets event, thread joins."""
        client = MagicMock()

        # Order stays open so loop doesn't exit naturally
        order_obj = MagicMock()
        order_obj.status = "new"
        client.get_order_by_id.return_value = order_obj

        monitor = AlpacaOrderMonitor(
            client=client, poll_interval=0.01,
        )
        monitor.track("order-1")
        monitor.start()

        assert monitor._thread is not None
        assert monitor._thread.is_alive()

        monitor.stop(timeout=2.0)
        assert not monitor._thread.is_alive()
