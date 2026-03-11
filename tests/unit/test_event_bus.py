"""Tests for async event bus."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from src.data_ingest.domain.events import DataIngestedEvent, QualityCheckFailedEvent
from src.shared.domain import DomainEvent
from src.shared.infrastructure.event_bus import AsyncEventBus


class TestAsyncEventBus:
    @pytest.fixture()
    def bus(self) -> AsyncEventBus:
        return AsyncEventBus()

    async def test_subscribe_and_publish(self, bus: AsyncEventBus) -> None:
        received: list[DomainEvent] = []

        def handler(event: DataIngestedEvent) -> None:
            received.append(event)

        bus.subscribe(DataIngestedEvent, handler)
        event = DataIngestedEvent(ticker="AAPL", ohlcv_rows=756, financial_quarters=12)
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].ticker == "AAPL"

    async def test_async_handler(self, bus: AsyncEventBus) -> None:
        received: list[DomainEvent] = []

        async def async_handler(event: DataIngestedEvent) -> None:
            received.append(event)

        bus.subscribe(DataIngestedEvent, async_handler)
        event = DataIngestedEvent(ticker="MSFT", ohlcv_rows=500, financial_quarters=8)
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].ticker == "MSFT"

    async def test_multiple_handlers(self, bus: AsyncEventBus) -> None:
        calls: list[str] = []

        def handler_a(event: DataIngestedEvent) -> None:
            calls.append("a")

        async def handler_b(event: DataIngestedEvent) -> None:
            calls.append("b")

        bus.subscribe(DataIngestedEvent, handler_a)
        bus.subscribe(DataIngestedEvent, handler_b)

        event = DataIngestedEvent(ticker="GOOG", ohlcv_rows=100, financial_quarters=4)
        await bus.publish(event)

        assert "a" in calls
        assert "b" in calls
        assert len(calls) == 2

    async def test_no_subscribers_does_not_raise(self, bus: AsyncEventBus) -> None:
        event = DataIngestedEvent(ticker="TSLA", ohlcv_rows=50, financial_quarters=2)
        # Should not raise
        await bus.publish(event)

    async def test_different_event_types(self, bus: AsyncEventBus) -> None:
        ingested: list[DomainEvent] = []
        failed: list[DomainEvent] = []

        def on_ingested(event: DataIngestedEvent) -> None:
            ingested.append(event)

        def on_failed(event: QualityCheckFailedEvent) -> None:
            failed.append(event)

        bus.subscribe(DataIngestedEvent, on_ingested)
        bus.subscribe(QualityCheckFailedEvent, on_failed)

        await bus.publish(
            DataIngestedEvent(ticker="AAPL", ohlcv_rows=756, financial_quarters=12)
        )
        await bus.publish(
            QualityCheckFailedEvent(ticker="BAD", failures=("Missing data",))
        )

        assert len(ingested) == 1
        assert len(failed) == 1
        assert ingested[0].ticker == "AAPL"
        assert failed[0].ticker == "BAD"

    async def test_handler_receives_correct_event_data(self, bus: AsyncEventBus) -> None:
        received: list[QualityCheckFailedEvent] = []

        def handler(event: QualityCheckFailedEvent) -> None:
            received.append(event)

        bus.subscribe(QualityCheckFailedEvent, handler)
        await bus.publish(
            QualityCheckFailedEvent(
                ticker="WARN", failures=("Missing 10%", "Stale 5 days")
            )
        )

        assert len(received) == 1
        assert received[0].failures == ("Missing 10%", "Stale 5 days")
