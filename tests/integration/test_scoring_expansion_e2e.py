"""E2E integration tests for Phase 27 scoring expansion.

Tests ScoreSymbolHandler end-to-end with mocked data clients.
Proves technical sub-scores, MACD ATR normalization, sentiment sub-scores,
SentimentUpdatedEvent publication, and composite renormalization for NONE confidence.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from src.scoring.application.handlers import ScoreSymbolHandler
from src.scoring.application.commands import ScoreSymbolCommand
from src.scoring.infrastructure.in_memory_repo import InMemoryScoreRepository
from src.scoring.domain.value_objects import SentimentConfidence
from src.scoring.domain.events import SentimentUpdatedEvent, ScoreUpdatedEvent
from src.shared.infrastructure.sync_event_bus import SyncEventBus


# -- Shared fixtures -----------------------------------------------------------


@pytest.fixture
def fundamental_client() -> MagicMock:
    """Mock fundamental data client returning safe, valid data."""
    client = MagicMock()
    client.get.return_value = {
        "fundamental_score": 65,
        "f_score": 7,
        "z_score": 3.5,    # safe (>1.81)
        "m_score": -2.1,   # clean (<-1.78)
        "g_score": None,
        "is_growth_stock": False,
    }
    return client


@pytest.fixture
def technical_client() -> MagicMock:
    """Mock technical data client returning raw indicator values."""
    client = MagicMock()
    client.get.return_value = {
        "technical_score": 70,
        "rsi": 55.0,
        "macd_histogram": 1.2,
        "close": 252.0,
        "ma50": 245.0,
        "ma200": 228.0,
        "adx": 28.0,
        "obv_change_pct": 5.0,
        "atr21": 3.5,
    }
    return client


@pytest.fixture
def sentiment_client() -> MagicMock:
    """Mock sentiment data client with MEDIUM confidence."""
    client = MagicMock()
    client.get.return_value = {
        "sentiment_score": 65,
        "news_score": 60.0,
        "insider_score": None,
        "institutional_score": 70.0,
        "analyst_score": 65.0,
        "confidence": SentimentConfidence.MEDIUM,
    }
    return client


@pytest.fixture
def repo() -> InMemoryScoreRepository:
    return InMemoryScoreRepository()


@pytest.fixture
def bus() -> SyncEventBus:
    return SyncEventBus()


@pytest.fixture
def handler(
    fundamental_client: MagicMock,
    technical_client: MagicMock,
    sentiment_client: MagicMock,
    repo: InMemoryScoreRepository,
    bus: SyncEventBus,
) -> ScoreSymbolHandler:
    return ScoreSymbolHandler(
        score_repo=repo,
        fundamental_client=fundamental_client,
        technical_client=technical_client,
        sentiment_client=sentiment_client,
        bus=bus,
    )


# -- Technical sub-scores ------------------------------------------------------


class TestHandlerProducesTechnicalSubScores:
    """ScoreSymbolHandler produces TechnicalScore with 5 real sub-scores."""

    def test_handler_produces_technical_sub_scores(
        self, handler: ScoreSymbolHandler
    ) -> None:
        """result dict has technical_sub_scores with 5 entries."""
        cmd = ScoreSymbolCommand(symbol="AAPL")
        result = handler.handle(cmd)
        assert result.is_ok(), f"Handler returned error: {result}"
        data = result.unwrap()
        assert "technical_sub_scores" in data, "technical_sub_scores missing from result"
        sub_scores = data["technical_sub_scores"]
        assert len(sub_scores) == 5, (
            f"Expected 5 technical sub-scores, got {len(sub_scores)}"
        )

    def test_sub_scores_have_correct_names(
        self, handler: ScoreSymbolHandler
    ) -> None:
        """The 5 sub-scores are named RSI, MACD, MA, ADX, OBV."""
        cmd = ScoreSymbolCommand(symbol="AAPL")
        result = handler.handle(cmd)
        data = result.unwrap()
        names = {s["name"] for s in data["technical_sub_scores"]}
        assert names == {"RSI", "MACD", "MA", "ADX", "OBV"}

    def test_sub_scores_each_have_value_and_explanation(
        self, handler: ScoreSymbolHandler
    ) -> None:
        """Each sub-score has value (0-100) and explanation string."""
        cmd = ScoreSymbolCommand(symbol="AAPL")
        result = handler.handle(cmd)
        data = result.unwrap()
        for sub in data["technical_sub_scores"]:
            assert "value" in sub
            assert "explanation" in sub
            assert 0 <= sub["value"] <= 100, f"Sub-score {sub['name']} out of range"
            assert isinstance(sub["explanation"], str)


# -- Sentiment sub-scores ------------------------------------------------------


class TestHandlerProducesSentimentSubScores:
    """ScoreSymbolHandler builds SentimentScore from real sub-components."""

    def test_handler_produces_sentiment_score(
        self, handler: ScoreSymbolHandler
    ) -> None:
        """result dict has sentiment_score field."""
        cmd = ScoreSymbolCommand(symbol="AAPL")
        result = handler.handle(cmd)
        data = result.unwrap()
        assert "sentiment_score" in data
        assert 0 <= data["sentiment_score"] <= 100

    def test_sentiment_score_from_adapter(
        self, handler: ScoreSymbolHandler
    ) -> None:
        """sentiment_score matches the mock adapter's sentiment_score value."""
        cmd = ScoreSymbolCommand(symbol="AAPL")
        result = handler.handle(cmd)
        data = result.unwrap()
        # Mock returns sentiment_score=65
        assert data["sentiment_score"] == 65


# -- MACD ATR normalization ----------------------------------------------------


class TestMACDUsesATRNormalization:
    """With atr21=3.5 and macd_histogram=1.2, MACD score is in reasonable range."""

    def test_macd_score_in_reasonable_range(
        self, handler: ScoreSymbolHandler
    ) -> None:
        """atr21=3.5, macd_histogram=1.2 → range [-7,+7] → _norm(1.2,-7,7) ≈ 58.6."""
        cmd = ScoreSymbolCommand(symbol="AAPL")
        result = handler.handle(cmd)
        data = result.unwrap()
        sub_scores = {s["name"]: s for s in data["technical_sub_scores"]}
        macd_score = sub_scores["MACD"]["value"]
        # (1.2+7)/14*100 = 8.2/14*100 ≈ 58.6
        assert 50 <= macd_score <= 70, (
            f"MACD score should be in [50,70] range with atr=3.5, hist=1.2. "
            f"Got {macd_score}"
        )

    def test_macd_not_saturated_with_moderate_histogram(
        self, handler: ScoreSymbolHandler
    ) -> None:
        """MACD must not be 100 when histogram is moderate (ATR fix working)."""
        cmd = ScoreSymbolCommand(symbol="AAPL")
        result = handler.handle(cmd)
        data = result.unwrap()
        sub_scores = {s["name"]: s for s in data["technical_sub_scores"]}
        macd_score = sub_scores["MACD"]["value"]
        assert macd_score < 95, (
            f"MACD should not saturate at 100 for moderate histogram. Got {macd_score}"
        )


# -- SentimentUpdatedEvent publication -----------------------------------------


class TestSentimentUpdatedEventPublished:
    """SentimentUpdatedEvent is published after scoring with correct fields."""

    def test_sentiment_updated_event_published(
        self,
        fundamental_client: MagicMock,
        technical_client: MagicMock,
        sentiment_client: MagicMock,
        repo: InMemoryScoreRepository,
    ) -> None:
        """After handle(), SentimentUpdatedEvent is published to bus."""
        bus = SyncEventBus()
        received_events: list[SentimentUpdatedEvent] = []
        bus.subscribe(SentimentUpdatedEvent, received_events.append)

        handler = ScoreSymbolHandler(
            score_repo=repo,
            fundamental_client=fundamental_client,
            technical_client=technical_client,
            sentiment_client=sentiment_client,
            bus=bus,
        )
        cmd = ScoreSymbolCommand(symbol="AAPL")
        handler.handle(cmd)

        assert len(received_events) == 1, (
            f"Expected 1 SentimentUpdatedEvent, got {len(received_events)}"
        )
        evt = received_events[0]
        assert evt.symbol == "AAPL"
        assert evt.sentiment_score == 65

    def test_sentiment_event_has_correct_confidence(
        self,
        fundamental_client: MagicMock,
        technical_client: MagicMock,
        sentiment_client: MagicMock,
        repo: InMemoryScoreRepository,
    ) -> None:
        """SentimentUpdatedEvent confidence matches adapter's confidence."""
        bus = SyncEventBus()
        received_events: list[SentimentUpdatedEvent] = []
        bus.subscribe(SentimentUpdatedEvent, received_events.append)

        handler = ScoreSymbolHandler(
            score_repo=repo,
            fundamental_client=fundamental_client,
            technical_client=technical_client,
            sentiment_client=sentiment_client,
            bus=bus,
        )
        handler.handle(ScoreSymbolCommand(symbol="AAPL"))

        evt = received_events[0]
        # Mock returns SentimentConfidence.MEDIUM → confidence.value = "MEDIUM"
        assert evt.confidence == "MEDIUM"


# -- ScoreUpdatedEvent (regression) --------------------------------------------


class TestScoreUpdatedEventStillPublished:
    """ScoreUpdatedEvent is still published after Phase 27 changes (regression check)."""

    def test_score_updated_event_still_published(
        self,
        fundamental_client: MagicMock,
        technical_client: MagicMock,
        sentiment_client: MagicMock,
        repo: InMemoryScoreRepository,
    ) -> None:
        bus = SyncEventBus()
        score_events: list[ScoreUpdatedEvent] = []
        bus.subscribe(ScoreUpdatedEvent, score_events.append)

        handler = ScoreSymbolHandler(
            score_repo=repo,
            fundamental_client=fundamental_client,
            technical_client=technical_client,
            sentiment_client=sentiment_client,
            bus=bus,
        )
        handler.handle(ScoreSymbolCommand(symbol="AAPL"))

        assert len(score_events) == 1, (
            f"Expected 1 ScoreUpdatedEvent, got {len(score_events)}"
        )
        evt = score_events[0]
        assert evt.symbol == "AAPL"
        assert evt.safety_passed is True


# -- Composite renormalization with NONE confidence ----------------------------


class TestCompositeNoneConfidenceRenormalizes:
    """When sentiment confidence=NONE, composite = 0.5*fundamental + 0.5*technical."""

    def test_none_confidence_renormalizes_composite(
        self,
        fundamental_client: MagicMock,
        technical_client: MagicMock,
        repo: InMemoryScoreRepository,
        bus: SyncEventBus,
    ) -> None:
        """With NONE confidence: swing 0.4/0.4/0.2 → 0.5/0.5."""
        # Mock sentiment client returning NONE confidence
        none_sentiment_client = MagicMock()
        none_sentiment_client.get.return_value = {
            "sentiment_score": 50,
            "news_score": None,
            "insider_score": None,
            "institutional_score": None,
            "analyst_score": None,
            "confidence": SentimentConfidence.NONE,
        }

        handler = ScoreSymbolHandler(
            score_repo=repo,
            fundamental_client=fundamental_client,
            technical_client=technical_client,
            sentiment_client=none_sentiment_client,
            bus=bus,
        )
        result = handler.handle(ScoreSymbolCommand(symbol="AAPL"))
        data = result.unwrap()

        fund_val = data["fundamental_score"]  # 65.0
        tech_val = data["technical_score"]    # computed from raw indicators

        # Composite = 0.5*fund + 0.5*tech (within 2.0 tolerance)
        expected = 0.5 * fund_val + 0.5 * tech_val
        composite = data["composite_score"]
        assert abs(composite - expected) < 2.0, (
            f"Expected composite ~{expected:.1f} (0.5*{fund_val}+0.5*{tech_val}), "
            f"got {composite}"
        )


# -- Safety gate ---------------------------------------------------------------


class TestSafetyGatePass:
    """Safety gate passes when Z>1.81 and M<-1.78."""

    def test_safety_gate_passes_with_valid_scores(
        self, handler: ScoreSymbolHandler
    ) -> None:
        """Z=3.5 (>1.81) and M=-2.1 (<-1.78) → safety_passed=True."""
        cmd = ScoreSymbolCommand(symbol="AAPL")
        result = handler.handle(cmd)
        data = result.unwrap()
        assert data["safety_passed"] is True
        assert data["z_score"] == 3.5
        assert data["m_score"] == -2.1

    def test_safety_gate_fails_with_low_z_score(
        self,
        technical_client: MagicMock,
        sentiment_client: MagicMock,
        repo: InMemoryScoreRepository,
        bus: SyncEventBus,
    ) -> None:
        """Z=1.5 (<1.81) → safety_passed=False, composite=0."""
        unsafe_fund = MagicMock()
        unsafe_fund.get.return_value = {
            "fundamental_score": 65,
            "f_score": 7,
            "z_score": 1.5,   # below threshold!
            "m_score": -2.1,
            "g_score": None,
            "is_growth_stock": False,
        }
        handler = ScoreSymbolHandler(
            score_repo=repo,
            fundamental_client=unsafe_fund,
            technical_client=technical_client,
            sentiment_client=sentiment_client,
            bus=bus,
        )
        result = handler.handle(ScoreSymbolCommand(symbol="UNSAFE"))
        data = result.unwrap()
        assert data["safety_passed"] is False
        assert data["composite_score"] == 0
