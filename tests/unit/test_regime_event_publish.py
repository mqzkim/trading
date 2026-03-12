"""Tests for EventBus publish on confirmed regime transition (REGIME-03).

Covers:
  9. Event is NOT published when confirmed_days < 3
  10. Event IS published when regime reaches confirmed_days=3 AND regime differs
  11. Event is NOT published when confirmed_days=3 but regime same as previous confirmed
  12. Published event has correct fields (previous_regime, new_regime, confidence, vix_value, adx_value)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest

from src.regime.application.commands import DetectRegimeCommand
from src.regime.application.handlers import DetectRegimeHandler
from src.regime.domain import (
    IRegimeRepository,
    MarketRegime,
    RegimeChangedEvent,
    RegimeType,
)
from src.shared.domain import Ok
from src.shared.infrastructure.sync_event_bus import SyncEventBus


class InMemoryRegimeRepo(IRegimeRepository):
    """Dict-backed in-memory repo for testing."""

    def __init__(self) -> None:
        self._store: list[MarketRegime] = []

    def save(self, regime: MarketRegime) -> None:
        self._store.append(regime)

    def find_latest(self) -> Optional[MarketRegime]:
        return self._store[-1] if self._store else None

    def find_by_date_range(
        self, start: datetime, end: datetime
    ) -> list[MarketRegime]:
        return [
            r
            for r in self._store
            if start <= r.detected_at <= end
        ]


def _bull_cmd() -> DetectRegimeCommand:
    return DetectRegimeCommand(
        vix=15.0,
        sp500_price=5000.0,
        sp500_ma200=4800.0,
        adx=30.0,
        yield_spread=0.5,
    )


def _bear_cmd() -> DetectRegimeCommand:
    return DetectRegimeCommand(
        vix=35.0,
        sp500_price=4200.0,
        sp500_ma200=4500.0,
        adx=28.0,
        yield_spread=-0.3,
    )


class TestEventNotPublishedBeforeConfirmation:
    """Test 9: Event is NOT published when confirmed_days < 3."""

    def test_no_event_on_day_1_and_day_2(self) -> None:
        repo = InMemoryRegimeRepo()
        bus = SyncEventBus()
        events_received: list[RegimeChangedEvent] = []
        bus.subscribe(RegimeChangedEvent, events_received.append)

        handler = DetectRegimeHandler(regime_repo=repo, bus=bus)

        # Day 1
        handler.handle(_bull_cmd())
        assert len(events_received) == 0

        # Day 2
        handler.handle(_bull_cmd())
        assert len(events_received) == 0


class TestEventPublishedOnConfirmedTransition:
    """Test 10: Event IS published when confirmed AND regime changed."""

    def test_event_published_on_confirmed_regime(self) -> None:
        repo = InMemoryRegimeRepo()
        bus = SyncEventBus()
        events_received: list[RegimeChangedEvent] = []
        bus.subscribe(RegimeChangedEvent, events_received.append)

        handler = DetectRegimeHandler(regime_repo=repo, bus=bus)

        # First regime: Bull x3 (confirmed)
        handler.handle(_bull_cmd())
        handler.handle(_bull_cmd())
        handler.handle(_bull_cmd())

        # First confirmed regime fires event (no previous confirmed)
        assert len(events_received) == 1
        assert events_received[0].new_regime == RegimeType.BULL


class TestNoEventOnSameConfirmedRegime:
    """Test 11: No event when confirmed_days=3 but same as previous confirmed."""

    def test_no_duplicate_event_for_same_regime(self) -> None:
        repo = InMemoryRegimeRepo()
        bus = SyncEventBus()
        events_received: list[RegimeChangedEvent] = []
        bus.subscribe(RegimeChangedEvent, events_received.append)

        handler = DetectRegimeHandler(regime_repo=repo, bus=bus)

        # Bull confirmed (3 days)
        handler.handle(_bull_cmd())
        handler.handle(_bull_cmd())
        handler.handle(_bull_cmd())
        assert len(events_received) == 1  # Initial confirmation event

        # Day 4, 5 of same Bull -- no new event
        handler.handle(_bull_cmd())
        handler.handle(_bull_cmd())
        assert len(events_received) == 1  # Still just 1


class TestEventFieldsCorrect:
    """Test 12: Published event has correct fields."""

    def test_event_fields_match_regime_data(self) -> None:
        repo = InMemoryRegimeRepo()
        bus = SyncEventBus()
        events_received: list[RegimeChangedEvent] = []
        bus.subscribe(RegimeChangedEvent, events_received.append)

        handler = DetectRegimeHandler(regime_repo=repo, bus=bus)

        # Confirm Bull first
        handler.handle(_bull_cmd())
        handler.handle(_bull_cmd())
        handler.handle(_bull_cmd())

        # Now transition to Bear
        handler.handle(_bear_cmd())
        handler.handle(_bear_cmd())
        handler.handle(_bear_cmd())

        # Should have 2 events: Bull confirmation + Bear transition
        assert len(events_received) == 2
        bear_event = events_received[1]

        assert bear_event.previous_regime == RegimeType.BULL
        assert bear_event.new_regime == RegimeType.BEAR
        assert bear_event.confidence > 0
        assert bear_event.vix_value == 35.0
        assert bear_event.adx_value == 28.0
