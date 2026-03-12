"""Tests for ConcreteRegimeWeightAdjuster and regime-based scoring weight shifts (REGIME-04)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from src.scoring.application.commands import ScoreSymbolCommand
from src.scoring.application.handlers import ScoreSymbolHandler
from src.scoring.domain.services import (
    ConcreteRegimeWeightAdjuster,
    NoOpRegimeAdjuster,
    CompositeScoringService,
)
from src.scoring.domain.value_objects import (
    STRATEGY_WEIGHTS,
    FundamentalScore,
    TechnicalScore,
    SentimentScore,
)
from src.scoring.infrastructure import InMemoryScoreRepository
from src.shared.infrastructure.sync_event_bus import SyncEventBus
from src.regime.domain.events import RegimeChangedEvent
from src.regime.domain.value_objects import RegimeType


class TestConcreteRegimeWeightAdjuster:
    """ConcreteRegimeWeightAdjuster returns regime-specific weight distributions."""

    def test_none_regime_returns_default_weights(self):
        """Test 1: regime_type=None returns default STRATEGY_WEIGHTS (same as NoOp)."""
        adjuster = ConcreteRegimeWeightAdjuster()
        result = adjuster.adjust_weights("swing", regime_type=None)
        assert result == STRATEGY_WEIGHTS["swing"]

    def test_bull_regime_weights(self):
        """Test 2: Bull regime boosts technical to 45%."""
        adjuster = ConcreteRegimeWeightAdjuster()
        result = adjuster.adjust_weights("swing", regime_type="Bull")
        assert result == {"fundamental": 0.35, "technical": 0.45, "sentiment": 0.20}

    def test_bear_regime_weights(self):
        """Test 3: Bear regime boosts fundamental to 55%."""
        adjuster = ConcreteRegimeWeightAdjuster()
        result = adjuster.adjust_weights("swing", regime_type="Bear")
        assert result == {"fundamental": 0.55, "technical": 0.25, "sentiment": 0.20}

    def test_crisis_regime_weights(self):
        """Test 4: Crisis regime maximum defensive (60% fundamental)."""
        adjuster = ConcreteRegimeWeightAdjuster()
        result = adjuster.adjust_weights("swing", regime_type="Crisis")
        assert result == {"fundamental": 0.60, "technical": 0.15, "sentiment": 0.25}

    def test_sideways_regime_weights(self):
        """Test 5: Sideways regime shifts toward fundamental (45%)."""
        adjuster = ConcreteRegimeWeightAdjuster()
        result = adjuster.adjust_weights("swing", regime_type="Sideways")
        assert result == {"fundamental": 0.45, "technical": 0.35, "sentiment": 0.20}

    def test_update_regime_caches_for_subsequent_calls(self):
        """Test 6: update_regime() caches regime for adjust_weights() without explicit regime_type."""
        adjuster = ConcreteRegimeWeightAdjuster()
        adjuster.update_regime("Bear")
        result = adjuster.adjust_weights("swing")
        assert result == {"fundamental": 0.55, "technical": 0.25, "sentiment": 0.20}


class TestCompositeScoringWithRegimeAdjuster:
    """CompositeScoringService produces different scores under different regimes."""

    def test_regime_adjuster_changes_composite_score(self):
        """Test 7: Bear regime produces different score than NoOp for same inputs."""
        fundamental = FundamentalScore(value=80.0)
        technical = TechnicalScore(value=60.0)
        sentiment = SentimentScore(value=50.0)

        noop = CompositeScoringService(regime_adjuster=NoOpRegimeAdjuster())
        noop_score = noop.compute(fundamental, technical, sentiment, strategy="swing")

        regime = CompositeScoringService(
            regime_adjuster=ConcreteRegimeWeightAdjuster(regime_type="Bear"),
        )
        regime_score = regime.compute(fundamental, technical, sentiment, strategy="swing")

        # Bear shifts weights toward fundamental (55%) vs swing default (40%)
        # With fundamental=80 > technical=60, Bear score should differ
        assert noop_score.value != regime_score.value


class TestEventBusRegimeSubscription:
    """EventBus subscription updates adjuster's cached regime."""

    def test_regime_changed_event_updates_adjuster(self):
        """Test 8: Publishing RegimeChangedEvent updates adjuster's cached regime."""
        bus = SyncEventBus()
        adjuster = ConcreteRegimeWeightAdjuster()

        bus.subscribe(RegimeChangedEvent, adjuster.on_regime_changed)

        event = RegimeChangedEvent(
            previous_regime=RegimeType.BULL,
            new_regime=RegimeType.BEAR,
            confidence=0.85,
            vix_value=28.0,
            adx_value=32.0,
        )
        bus.publish(event)

        # After event, adjuster should use Bear weights
        result = adjuster.adjust_weights("swing")
        assert result == {"fundamental": 0.55, "technical": 0.25, "sentiment": 0.20}


class TestScoreHandlerRegimeAdjusterWiring:
    """ScoreSymbolHandler accepts and forwards regime_adjuster to CompositeScoringService."""

    def _make_handler(self, regime_adjuster=None):
        """Create handler with mock data clients returning fixed values."""
        repo = InMemoryScoreRepository()
        fundamental_client = MagicMock()
        fundamental_client.get.return_value = {
            "fundamental_score": 80,
            "z_score": 3.0,
            "m_score": -2.5,
            "f_score": 7,
        }
        technical_client = MagicMock()
        technical_client.get.return_value = {"technical_score": 40}
        sentiment_client = MagicMock()
        sentiment_client.get.return_value = {"sentiment_score": 50}

        return ScoreSymbolHandler(
            score_repo=repo,
            fundamental_client=fundamental_client,
            technical_client=technical_client,
            sentiment_client=sentiment_client,
            regime_adjuster=regime_adjuster,
        )

    def test_score_handler_uses_injected_regime_adjuster(self):
        """Test 9: Bear regime adjuster produces different composite score than default NoOp.

        With fundamental=80, technical=40, sentiment=50:
        - NoOp (swing defaults 40/40/20): 80*0.4 + 40*0.4 + 50*0.2 = 32+16+10 = 58
        - Bear (55/25/20): 80*0.55 + 40*0.25 + 50*0.2 = 44+10+10 = 64
        """
        handler_noop = self._make_handler(regime_adjuster=None)
        handler_bear = self._make_handler(
            regime_adjuster=ConcreteRegimeWeightAdjuster("Bear"),
        )

        cmd = ScoreSymbolCommand(symbol="AAPL", strategy="swing")

        result_noop = handler_noop.handle(cmd)
        result_bear = handler_bear.handle(cmd)

        assert result_noop.value["composite_score"] != result_bear.value["composite_score"]

    def test_bootstrap_injects_regime_adjuster(self):
        """Test 10: bootstrap() wires ConcreteRegimeWeightAdjuster into ScoreSymbolHandler."""
        from src.bootstrap import bootstrap
        from src.shared.infrastructure.db_factory import DBFactory

        ctx = bootstrap(db_factory=DBFactory(data_dir=":memory:"))
        score_handler = ctx["score_handler"]
        adjuster = score_handler._composite._regime_adjuster
        assert isinstance(adjuster, ConcreteRegimeWeightAdjuster)
