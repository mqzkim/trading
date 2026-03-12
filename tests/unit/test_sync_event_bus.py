"""Tests for synchronous event bus."""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain import DomainEvent
from src.shared.infrastructure.sync_event_bus import SyncEventBus


@dataclass(frozen=True)
class _FakeEventA(DomainEvent):
    ticker: str


@dataclass(frozen=True)
class _FakeEventB(DomainEvent):
    code: str


class TestSyncEventBus:
    def test_subscribe_and_publish(self) -> None:
        bus = SyncEventBus()
        received: list[DomainEvent] = []

        def handler(event: _FakeEventA) -> None:
            received.append(event)

        bus.subscribe(_FakeEventA, handler)
        bus.publish(_FakeEventA(ticker="AAPL"))

        assert len(received) == 1
        assert received[0].ticker == "AAPL"  # type: ignore[attr-defined]

    def test_no_subscribers_does_not_raise(self) -> None:
        bus = SyncEventBus()
        # Publishing with no subscribers should not raise
        bus.publish(_FakeEventA(ticker="TSLA"))

    def test_multiple_handlers_same_event(self) -> None:
        bus = SyncEventBus()
        calls: list[str] = []

        def handler_a(event: _FakeEventA) -> None:
            calls.append("a")

        def handler_b(event: _FakeEventA) -> None:
            calls.append("b")

        bus.subscribe(_FakeEventA, handler_a)
        bus.subscribe(_FakeEventA, handler_b)
        bus.publish(_FakeEventA(ticker="GOOG"))

        assert "a" in calls
        assert "b" in calls
        assert len(calls) == 2

    def test_different_event_types_route_correctly(self) -> None:
        bus = SyncEventBus()
        a_events: list[DomainEvent] = []
        b_events: list[DomainEvent] = []

        bus.subscribe(_FakeEventA, lambda e: a_events.append(e))
        bus.subscribe(_FakeEventB, lambda e: b_events.append(e))

        bus.publish(_FakeEventA(ticker="AAPL"))
        bus.publish(_FakeEventB(code="ERR"))

        assert len(a_events) == 1
        assert len(b_events) == 1
        assert a_events[0].ticker == "AAPL"  # type: ignore[attr-defined]
        assert b_events[0].code == "ERR"  # type: ignore[attr-defined]

    def test_handler_receives_correct_event_data(self) -> None:
        bus = SyncEventBus()
        received: list[_FakeEventB] = []

        bus.subscribe(_FakeEventB, lambda e: received.append(e))
        bus.publish(_FakeEventB(code="X123"))

        assert len(received) == 1
        assert received[0].code == "X123"
