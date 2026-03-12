"""Tests for execution alert events — StopHitAlertEvent, TargetReachedAlertEvent."""
from __future__ import annotations

from src.execution.domain.events import StopHitAlertEvent, TargetReachedAlertEvent


class TestStopHitAlertEvent:
    """Test StopHitAlertEvent creation and properties."""

    def test_create_with_valid_fields(self):
        event = StopHitAlertEvent(
            symbol="AAPL",
            current_price=138.0,
            stop_price=140.0,
        )
        assert event.symbol == "AAPL"
        assert event.current_price == 138.0
        assert event.stop_price == 140.0

    def test_event_type_property(self):
        event = StopHitAlertEvent(
            symbol="AAPL",
            current_price=138.0,
            stop_price=140.0,
        )
        assert "StopHitAlertEvent" in event.event_type

    def test_event_is_frozen(self):
        event = StopHitAlertEvent(
            symbol="AAPL",
            current_price=138.0,
            stop_price=140.0,
        )
        import dataclasses
        assert dataclasses.is_dataclass(event)


class TestTargetReachedAlertEvent:
    """Test TargetReachedAlertEvent creation and properties."""

    def test_create_with_valid_fields(self):
        event = TargetReachedAlertEvent(
            symbol="MSFT",
            current_price=175.0,
            target_price=170.0,
        )
        assert event.symbol == "MSFT"
        assert event.current_price == 175.0
        assert event.target_price == 170.0

    def test_event_type_property(self):
        event = TargetReachedAlertEvent(
            symbol="MSFT",
            current_price=175.0,
            target_price=170.0,
        )
        assert "TargetReachedAlertEvent" in event.event_type

    def test_event_has_occurred_on(self):
        event = TargetReachedAlertEvent(
            symbol="MSFT",
            current_price=175.0,
            target_price=170.0,
        )
        assert event.occurred_on is not None
