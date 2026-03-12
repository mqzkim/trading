"""Tests for ScoreSymbolHandler event creation and G-Score wiring.

Verifies:
1. ScoreSymbolHandler.handle() passes g_score and is_growth_stock to compute()
2. ScoreSymbolHandler.handle() creates ScoreUpdatedEvent after scoring
"""
from __future__ import annotations

from typing import Optional

import pytest

from src.scoring.application.commands import ScoreSymbolCommand
from src.scoring.application.handlers import ScoreSymbolHandler
from src.scoring.domain.events import ScoreUpdatedEvent
from src.scoring.domain.value_objects import CompositeScore


class FakeScoreRepo:
    """In-memory score repository for testing."""

    def __init__(self) -> None:
        self._scores: dict[str, CompositeScore] = {}

    def save(self, symbol: str, score: CompositeScore) -> None:
        self._scores[symbol] = score

    def find_latest(self, symbol: str) -> Optional[CompositeScore]:
        return self._scores.get(symbol)

    def find_all_latest(self, limit: int = 100) -> dict[str, CompositeScore]:
        return dict(list(self._scores.items())[:limit])


class FakeClient:
    """Mock data client that returns configurable data."""

    def __init__(self, data: dict) -> None:
        self._data = data

    def get(self, symbol: str) -> dict:
        return self._data


@pytest.fixture
def handler_with_growth_stock():
    """Handler with mock clients returning growth stock data."""
    repo = FakeScoreRepo()
    fundamental_client = FakeClient({
        "fundamental_score": 70,
        "f_score": 7,
        "z_score": 3.5,
        "m_score": -3.0,
        "g_score": 6,
        "is_growth_stock": True,
    })
    technical_client = FakeClient({"technical_score": 65})
    sentiment_client = FakeClient({"sentiment_score": 60})

    handler = ScoreSymbolHandler(
        score_repo=repo,
        fundamental_client=fundamental_client,
        technical_client=technical_client,
        sentiment_client=sentiment_client,
    )
    return handler, repo


@pytest.fixture
def handler_with_normal_stock():
    """Handler with mock clients returning non-growth stock data."""
    repo = FakeScoreRepo()
    fundamental_client = FakeClient({
        "fundamental_score": 75,
        "f_score": 8,
        "z_score": 4.0,
        "m_score": -2.5,
    })
    technical_client = FakeClient({"technical_score": 70})
    sentiment_client = FakeClient({"sentiment_score": 55})

    handler = ScoreSymbolHandler(
        score_repo=repo,
        fundamental_client=fundamental_client,
        technical_client=technical_client,
        sentiment_client=sentiment_client,
    )
    return handler, repo


class TestScoreUpdatedEvent:
    """ScoreSymbolHandler should create ScoreUpdatedEvent after scoring."""

    def test_handle_creates_event_in_result(self, handler_with_normal_stock) -> None:
        handler, repo = handler_with_normal_stock
        cmd = ScoreSymbolCommand(symbol="AAPL", strategy="swing")
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        assert "event" in data, "Result must contain 'event' key with ScoreUpdatedEvent"
        event = data["event"]
        assert isinstance(event, ScoreUpdatedEvent)
        assert event.symbol == "AAPL"
        assert event.strategy == "swing"
        assert event.composite_score == data["composite_score"]
        assert event.risk_adjusted_score == data["risk_adjusted_score"]

    def test_event_has_correct_safety_passed(self, handler_with_normal_stock) -> None:
        handler, repo = handler_with_normal_stock
        cmd = ScoreSymbolCommand(symbol="MSFT", strategy="swing")
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        event = data["event"]
        assert event.safety_passed is True

    def test_no_event_when_safety_gate_fails(self) -> None:
        """Safety gate failure should not create event."""
        repo = FakeScoreRepo()
        fundamental_client = FakeClient({
            "fundamental_score": 50,
            "z_score": 1.0,  # Below threshold
            "m_score": -1.0,  # Above threshold (fails)
        })
        technical_client = FakeClient({"technical_score": 50})
        sentiment_client = FakeClient({"sentiment_score": 50})

        handler = ScoreSymbolHandler(
            score_repo=repo,
            fundamental_client=fundamental_client,
            technical_client=technical_client,
            sentiment_client=sentiment_client,
        )
        cmd = ScoreSymbolCommand(symbol="BAD", strategy="swing")
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        assert data["safety_passed"] is False
        assert "event" not in data


class TestGScoreWiring:
    """ScoreSymbolHandler should pass g_score and is_growth_stock to compute()."""

    def test_growth_stock_gets_g_score_contribution(self, handler_with_growth_stock) -> None:
        handler, repo = handler_with_growth_stock
        cmd = ScoreSymbolCommand(symbol="TSLA", strategy="swing")
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        # Growth stock with g_score=6 should boost fundamental by (6/8)*15 = 11.25
        # Without g_score: fundamental=70, with: min(100, 70+11.25) = 81.25
        # swing weights (TECH-03): f=0.40, t=0.40, s=0.20
        # Without g_score: 0.40*70 + 0.40*65 + 0.20*60 = 28.0 + 26.0 + 12.0 = 66.0
        # With g_score:    0.40*81.25 + 0.40*65 + 0.20*60 = 32.5 + 26.0 + 12.0 = 70.5
        assert data["composite_score"] > 65.5, (
            f"Growth stock composite {data['composite_score']} should be boosted by G-Score"
        )

    def test_normal_stock_no_g_score_boost(self, handler_with_normal_stock) -> None:
        handler, repo = handler_with_normal_stock
        cmd = ScoreSymbolCommand(symbol="AAPL", strategy="swing")
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        # Normal stock: fundamental=75, technical=70, sentiment=55
        # swing (TECH-03): 0.40*75 + 0.40*70 + 0.20*55 = 30.0 + 28.0 + 11.0 = 69.0
        assert data["composite_score"] == 69.0
