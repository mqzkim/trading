"""Integration test for event bus wiring in bootstrap context.

Proves that:
1. SyncEventBus is wired in bootstrap()
2. Publishing ScoreUpdatedEvent reaches a registered handler
3. The logging handler wired in bootstrap receives events
4. No unexpected side effects from event wiring during scoring
"""
from __future__ import annotations

import tempfile

import pytest

from src.shared.infrastructure.db_factory import DBFactory
from src.scoring.domain.events import ScoreUpdatedEvent


class TestEventWiring:
    """Integration tests for event bus wiring via bootstrap()."""

    def test_bus_available_in_bootstrap_context(self):
        """bootstrap() returns a context with 'bus' key containing SyncEventBus."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_factory = DBFactory(data_dir=tmpdir)
            from src.bootstrap import bootstrap
            ctx = bootstrap(db_factory=db_factory)

            assert "bus" in ctx
            assert hasattr(ctx["bus"], "subscribe")
            assert hasattr(ctx["bus"], "publish")
            db_factory.close()

    def test_custom_handler_receives_published_event(self):
        """Publishing ScoreUpdatedEvent through the bus invokes registered handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_factory = DBFactory(data_dir=tmpdir)
            from src.bootstrap import bootstrap
            ctx = bootstrap(db_factory=db_factory)
            bus = ctx["bus"]

            received_events: list[ScoreUpdatedEvent] = []
            bus.subscribe(ScoreUpdatedEvent, lambda e: received_events.append(e))

            event = ScoreUpdatedEvent(
                symbol="AAPL",
                composite_score=72.5,
                risk_adjusted_score=70.0,
                safety_passed=True,
                strategy="swing",
            )
            bus.publish(event)

            assert len(received_events) == 1
            assert received_events[0].symbol == "AAPL"
            assert received_events[0].composite_score == 72.5
            db_factory.close()

    def test_bootstrap_wires_score_event_logging_handler(self):
        """bootstrap() wires a logging handler for ScoreUpdatedEvent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_factory = DBFactory(data_dir=tmpdir)
            from src.bootstrap import bootstrap
            ctx = bootstrap(db_factory=db_factory)
            bus = ctx["bus"]

            # The bootstrap should have wired at least one handler for ScoreUpdatedEvent
            event = ScoreUpdatedEvent(
                symbol="MSFT",
                composite_score=85.0,
                risk_adjusted_score=82.0,
                safety_passed=True,
                strategy="position",
            )

            # Publishing should not raise -- the wired handler should process it
            bus.publish(event)

            # Verify the event was tracked in the context's score_events list
            assert "score_events" in ctx
            assert len(ctx["score_events"]) == 1
            assert ctx["score_events"][0].symbol == "MSFT"
            db_factory.close()

    def test_multiple_events_all_received(self):
        """Multiple ScoreUpdatedEvents all reach the handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_factory = DBFactory(data_dir=tmpdir)
            from src.bootstrap import bootstrap
            ctx = bootstrap(db_factory=db_factory)
            bus = ctx["bus"]

            symbols = ["AAPL", "MSFT", "GOOGL"]
            for sym in symbols:
                event = ScoreUpdatedEvent(
                    symbol=sym,
                    composite_score=70.0,
                    risk_adjusted_score=68.0,
                    safety_passed=True,
                    strategy="swing",
                )
                bus.publish(event)

            assert len(ctx["score_events"]) == 3
            received_symbols = [e.symbol for e in ctx["score_events"]]
            assert received_symbols == ["AAPL", "MSFT", "GOOGL"]
            db_factory.close()

    def test_no_side_effects_from_wiring(self):
        """Event wiring does not cause side effects during normal operations.

        Specifically: publishing a ScoreUpdatedEvent should NOT trigger
        signal generation or portfolio changes (per RESEARCH pitfall 3).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_factory = DBFactory(data_dir=tmpdir)
            from src.bootstrap import bootstrap
            ctx = bootstrap(db_factory=db_factory)
            bus = ctx["bus"]

            event = ScoreUpdatedEvent(
                symbol="AAPL",
                composite_score=72.5,
                risk_adjusted_score=70.0,
                safety_passed=True,
                strategy="swing",
            )
            bus.publish(event)

            # Signal handler should NOT have been called
            # (cross-context subscriptions remain commented out)
            signal_handler = ctx["signal_handler"]
            assert not hasattr(signal_handler, "_last_event"), \
                "Signal handler should not receive score events in Phase 5"
            db_factory.close()
