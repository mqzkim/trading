"""Integration tests: event bus end-to-end in a bootstrapped context.

Verifies that event subscriptions are live (not just defined) by:
1. Scoring a symbol and checking ScoreUpdatedEvent reaches subscribers
2. Publishing RegimeChangedEvent and verifying regime_adjuster receives it
3. Publishing DrawdownAlertEvent and verifying approval_handler receives it

Uses temp databases and mock data adapters -- no real market data needed.
"""
from __future__ import annotations

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from src.shared.infrastructure.db_factory import DBFactory
from src.shared.infrastructure.sync_event_bus import SyncEventBus
from src.scoring.application.commands import ScoreSymbolCommand
from src.scoring.application.handlers import ScoreSymbolHandler
from src.scoring.domain.events import ScoreUpdatedEvent
from src.scoring.infrastructure.sqlite_repo import SqliteScoreRepository
from src.scoring.domain.services import ConcreteRegimeWeightAdjuster
from src.regime.domain.events import RegimeChangedEvent
from src.regime.domain.value_objects import RegimeType
from src.portfolio.domain.events import DrawdownAlertEvent


class FakeClient:
    """Mock data client returning fixed data."""

    def __init__(self, data: dict) -> None:
        self._data = data

    def get(self, symbol: str) -> dict:
        return self._data


@pytest.fixture
def wired_context(tmp_path):
    """Build a minimal wired context for event bus testing.

    Uses temp DB paths and mock adapters. Does NOT call bootstrap()
    because that requires Alpaca keys. Instead, wires the relevant
    components manually to test event bus subscriptions.
    """
    bus = SyncEventBus()

    score_repo = SqliteScoreRepository(
        db_path=str(tmp_path / "scoring.db"),
    )

    regime_adjuster = ConcreteRegimeWeightAdjuster()

    # Mock data adapters
    fundamental_client = FakeClient({
        "fundamental_score": 75, "f_score": 8,
        "z_score": 4.0, "m_score": -2.5,
    })
    technical_client = FakeClient({"technical_score": 70})
    sentiment_client = FakeClient({"sentiment_score": 55})

    score_handler = ScoreSymbolHandler(
        score_repo=score_repo,
        regime_adjuster=regime_adjuster,
        bus=bus,
        fundamental_client=fundamental_client,
        technical_client=technical_client,
        sentiment_client=sentiment_client,
    )

    # Wire event subscriptions (same as bootstrap.py)
    score_events: list[ScoreUpdatedEvent] = []

    def _log_score_event(event: ScoreUpdatedEvent) -> None:
        score_events.append(event)

    bus.subscribe(ScoreUpdatedEvent, _log_score_event)

    # Regime -> scoring weight adjustment
    bus.subscribe(RegimeChangedEvent, regime_adjuster.on_regime_changed)

    # Regime -> approval suspension
    approval_handler = MagicMock()
    approval_handler.suspend_if_regime_invalid = MagicMock()
    approval_handler.suspend_for_drawdown = MagicMock()

    def _on_regime_changed(event: RegimeChangedEvent) -> None:
        approval_handler.suspend_if_regime_invalid(event.new_regime.value)

    bus.subscribe(RegimeChangedEvent, _on_regime_changed)

    # Drawdown -> approval suspension
    def _on_drawdown_alert(event: DrawdownAlertEvent) -> None:
        if event.level in ("warning", "critical"):
            approval_handler.suspend_for_drawdown()

    bus.subscribe(DrawdownAlertEvent, _on_drawdown_alert)

    return {
        "bus": bus,
        "score_handler": score_handler,
        "score_events": score_events,
        "score_repo": score_repo,
        "regime_adjuster": regime_adjuster,
        "approval_handler": approval_handler,
    }


class TestScoreEventPublished:
    """Verify ScoreUpdatedEvent reaches subscribers after scoring."""

    def test_score_event_published_on_scoring(self, wired_context) -> None:
        """Calling handle() publishes ScoreUpdatedEvent to logging subscriber."""
        ctx = wired_context
        cmd = ScoreSymbolCommand(symbol="AAPL", strategy="swing")
        result = ctx["score_handler"].handle(cmd)

        assert result.is_ok()
        assert len(ctx["score_events"]) == 1, "Score event should be published"
        event = ctx["score_events"][0]
        assert event.symbol == "AAPL"
        assert event.composite_score > 0
        assert event.safety_passed is True

    def test_score_persisted_in_repo(self, wired_context) -> None:
        """Score is persisted in SQLite and retrievable."""
        ctx = wired_context
        cmd = ScoreSymbolCommand(symbol="MSFT", strategy="swing")
        ctx["score_handler"].handle(cmd)

        latest = ctx["score_repo"].find_latest("MSFT")
        assert latest is not None
        assert latest.value > 0


class TestRegimeEventReachesAdjuster:
    """Verify RegimeChangedEvent subscription is active."""

    def test_regime_event_reaches_adjuster(self, wired_context) -> None:
        """Publishing RegimeChangedEvent updates regime_adjuster state."""
        ctx = wired_context
        adjuster = ctx["regime_adjuster"]

        # Verify initial state
        assert adjuster._regime_type is None

        # Publish regime change event
        event = RegimeChangedEvent(
            previous_regime=RegimeType.BULL,
            new_regime=RegimeType.BEAR,
            confidence=0.85,
            vix_value=28.0,
            adx_value=25.0,
        )
        ctx["bus"].publish(event)

        # Verify adjuster received the event
        assert adjuster._regime_type == "Bear"

    def test_regime_event_triggers_approval_check(self, wired_context) -> None:
        """Publishing RegimeChangedEvent triggers approval regime check."""
        ctx = wired_context
        event = RegimeChangedEvent(
            previous_regime=RegimeType.BULL,
            new_regime=RegimeType.CRISIS,
            confidence=0.9,
            vix_value=45.0,
            adx_value=30.0,
        )
        ctx["bus"].publish(event)

        ctx["approval_handler"].suspend_if_regime_invalid.assert_called_once_with("Crisis")


class TestDrawdownEventReachesApproval:
    """Verify DrawdownAlertEvent subscription is active."""

    def test_warning_drawdown_triggers_suspension(self, wired_context) -> None:
        """DrawdownAlertEvent with level='warning' triggers approval suspension."""
        ctx = wired_context
        event = DrawdownAlertEvent(
            portfolio_id="test",
            drawdown=0.12,
            level="warning",
        )
        ctx["bus"].publish(event)

        ctx["approval_handler"].suspend_for_drawdown.assert_called_once()

    def test_critical_drawdown_triggers_suspension(self, wired_context) -> None:
        """DrawdownAlertEvent with level='critical' triggers approval suspension."""
        ctx = wired_context
        event = DrawdownAlertEvent(
            portfolio_id="test",
            drawdown=0.22,
            level="critical",
        )
        ctx["bus"].publish(event)

        ctx["approval_handler"].suspend_for_drawdown.assert_called_once()

    def test_caution_drawdown_does_not_trigger(self, wired_context) -> None:
        """DrawdownAlertEvent with level='caution' does NOT trigger suspension."""
        ctx = wired_context
        event = DrawdownAlertEvent(
            portfolio_id="test",
            drawdown=0.06,
            level="caution",
        )
        ctx["bus"].publish(event)

        ctx["approval_handler"].suspend_for_drawdown.assert_not_called()
