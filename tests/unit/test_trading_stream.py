"""Tests for TradingStreamAdapter WebSocket wrapper.

Covers: fill event publishing, monitor coordination, non-fill event filtering.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from src.execution.infrastructure.trading_stream import TradingStreamAdapter
from src.execution.domain.events import OrderFilledEvent


class TestTradingStreamAdapter:
    """Test TradingStreamAdapter event handling."""

    def test_stream_publishes_fill_event(self):
        """On fill trade update -> publishes OrderFilledEvent to bus."""
        bus = MagicMock()

        with patch("src.execution.infrastructure.trading_stream.TradingStream"):
            adapter = TradingStreamAdapter(
                api_key="test-key",
                secret_key="test-secret",
                paper=True,
                bus=bus,
            )

        # Simulate a fill event
        data = MagicMock()
        data.event = "fill"
        data.order = MagicMock()
        data.order.id = "order-123"
        data.order.symbol = "AAPL"
        data.qty = "10"
        data.price = "150.50"
        data.position_qty = "20"

        import asyncio
        asyncio.run(adapter._on_trade_update(data))

        bus.publish.assert_called_once()
        event = bus.publish.call_args[0][0]
        assert isinstance(event, OrderFilledEvent)
        assert event.order_id == "order-123"
        assert event.symbol == "AAPL"
        assert event.quantity == 10
        assert event.filled_price == 150.50

    def test_stream_removes_from_monitor(self):
        """On fill -> calls monitor.remove_order(order_id) to prevent duplicate."""
        bus = MagicMock()
        monitor = MagicMock()

        with patch("src.execution.infrastructure.trading_stream.TradingStream"):
            adapter = TradingStreamAdapter(
                api_key="test-key",
                secret_key="test-secret",
                paper=True,
                bus=bus,
                monitor=monitor,
            )

        data = MagicMock()
        data.event = "fill"
        data.order = MagicMock()
        data.order.id = "order-456"
        data.order.symbol = "MSFT"
        data.qty = "5"
        data.price = "300.00"
        data.position_qty = "15"

        import asyncio
        asyncio.run(adapter._on_trade_update(data))

        monitor.remove_order.assert_called_once_with("order-456")

    def test_stream_ignores_non_fill(self):
        """On 'new' or 'accepted' event -> no OrderFilledEvent published."""
        bus = MagicMock()

        with patch("src.execution.infrastructure.trading_stream.TradingStream"):
            adapter = TradingStreamAdapter(
                api_key="test-key",
                secret_key="test-secret",
                paper=True,
                bus=bus,
            )

        for event_type in ("new", "accepted", "pending_new", "canceled"):
            data = MagicMock()
            data.event = event_type
            data.order = MagicMock()
            data.order.id = "order-789"

            import asyncio
            asyncio.run(adapter._on_trade_update(data))

        bus.publish.assert_not_called()

    def test_stream_handles_partial_fill(self):
        """On partial_fill -> publishes OrderFilledEvent."""
        bus = MagicMock()

        with patch("src.execution.infrastructure.trading_stream.TradingStream"):
            adapter = TradingStreamAdapter(
                api_key="test-key",
                secret_key="test-secret",
                paper=True,
                bus=bus,
            )

        data = MagicMock()
        data.event = "partial_fill"
        data.order = MagicMock()
        data.order.id = "order-partial"
        data.order.symbol = "TSLA"
        data.qty = "3"
        data.price = "250.00"
        data.position_qty = "3"

        import asyncio
        asyncio.run(adapter._on_trade_update(data))

        bus.publish.assert_called_once()
        event = bus.publish.call_args[0][0]
        assert isinstance(event, OrderFilledEvent)
