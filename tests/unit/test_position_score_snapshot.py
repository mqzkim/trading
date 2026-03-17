"""PERF-05: Score snapshot captured at trade entry time."""
from __future__ import annotations

from datetime import date

import pytest

try:
    from src.portfolio.domain.entities import Position
    from src.portfolio.domain.events import PositionClosedEvent, PositionOpenedEvent
    from src.portfolio.domain.value_objects import RiskTier

    _HAS_IMPL = True
except ImportError:
    _HAS_IMPL = False

pytestmark = pytest.mark.skipif(not _HAS_IMPL, reason="implementation pending")


def test_position_opened_event_has_score_snapshot():
    """PositionOpenedEvent with score_snapshot field holds all score fields."""
    snapshot = {
        "composite_score": 78.5,
        "technical_score": 82.0,
        "fundamental_score": 75.0,
        "sentiment_score": 70.0,
        "regime": "bull",
        "weights": {"fundamental": 0.4, "technical": 0.4, "sentiment": 0.2},
    }
    event = PositionOpenedEvent(
        symbol="AAPL",
        entry_price=150.0,
        quantity=10,
        score_snapshot=snapshot,
    )
    assert event.score_snapshot is not None
    assert event.score_snapshot["composite_score"] == 78.5
    assert event.score_snapshot["regime"] == "bull"


def test_position_close_emits_full_event():
    """Position.close(exit_price) emits PositionClosedEvent with all fields."""
    snapshot = {
        "composite_score": 78.5,
        "technical_score": 82.0,
        "fundamental_score": 75.0,
        "sentiment_score": 70.0,
        "regime": "bull",
        "weights": {"fundamental": 0.4, "technical": 0.4, "sentiment": 0.2},
    }
    pos = Position(
        symbol="AAPL",
        entry_price=150.0,
        quantity=10,
        entry_date=date(2025, 1, 10),
        strategy="swing",
        sector="technology",
        score_snapshot=snapshot,
    )
    result = pos.close(165.0)
    assert result["pnl"] == 150.0

    events = pos.pull_domain_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, PositionClosedEvent)
    assert event.entry_price == 150.0
    assert event.exit_price == 165.0
    assert event.quantity == 10
    assert event.strategy == "swing"
    assert event.sector == "technology"
    assert event.score_snapshot == snapshot
    assert event.pnl == 150.0


def test_score_snapshot_stored_on_position():
    """Position with score_snapshot attribute stores the snapshot until close."""
    snapshot = {"composite_score": 80.0}
    pos = Position(
        symbol="MSFT",
        entry_price=300.0,
        quantity=5,
        score_snapshot=snapshot,
    )
    assert pos.score_snapshot == snapshot
    pos.close(310.0)
    # Snapshot is still accessible on Position after close
    assert pos.score_snapshot == snapshot
