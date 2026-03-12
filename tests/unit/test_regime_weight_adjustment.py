"""Tests for ConcreteRegimeWeightAdjuster and regime-based scoring weight shifts (REGIME-04)."""
from __future__ import annotations

import pytest
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
