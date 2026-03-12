"""Unit tests for regime-weighted signal fusion (SIGNAL-06).

Tests that SignalFusionService.fuse() applies per-strategy weights
depending on regime_type, and that GenerateSignalCommand accepts
regime_type field.
"""
from __future__ import annotations

import pytest
from src.signals.domain.value_objects import (
    SignalDirection,
    MethodologyType,
    MethodologyResult,
    SignalStrength,
)
from src.signals.domain.services import (
    SignalFusionService,
    SIGNAL_STRATEGY_WEIGHTS,
    DEFAULT_SIGNAL_WEIGHTS,
)
from src.signals.application.commands import GenerateSignalCommand


def _make_results(
    cs_dir: SignalDirection = SignalDirection.BUY,
    cs_score: float = 80.0,
    mf_dir: SignalDirection = SignalDirection.BUY,
    mf_score: float = 80.0,
    dm_dir: SignalDirection = SignalDirection.BUY,
    dm_score: float = 80.0,
    tf_dir: SignalDirection = SignalDirection.BUY,
    tf_score: float = 80.0,
) -> list[MethodologyResult]:
    """Helper to build 4 methodology results."""
    return [
        MethodologyResult(methodology=MethodologyType.CAN_SLIM, direction=cs_dir, score=cs_score),
        MethodologyResult(methodology=MethodologyType.MAGIC_FORMULA, direction=mf_dir, score=mf_score),
        MethodologyResult(methodology=MethodologyType.DUAL_MOMENTUM, direction=dm_dir, score=dm_score),
        MethodologyResult(methodology=MethodologyType.TREND_FOLLOWING, direction=tf_dir, score=tf_score),
    ]


class TestRegimeWeightedFusion:
    """Tests that regime_type changes strength computation via weighted averaging."""

    def setup_method(self) -> None:
        self.svc = SignalFusionService()

    def test_bull_regime_boosts_momentum_strategies(self) -> None:
        """Bull: DM+TF combined 60% weight."""
        results = _make_results(
            cs_score=50.0, mf_score=50.0,
            dm_score=90.0, tf_score=90.0,
        )
        _, strength_bull = self.svc.fuse(
            results=results, composite_score=70.0,
            safety_passed=True, regime_type="Bull",
        )
        _, strength_none = self.svc.fuse(
            results=results, composite_score=70.0,
            safety_passed=True, regime_type=None,
        )
        # Bull weights momentum higher -> strength differs from equal weighting
        # When momentum scores higher than quality, bull regime should give higher strength
        assert strength_bull.value > strength_none.value

    def test_bear_regime_boosts_quality_strategies(self) -> None:
        """Bear: MF gets 35% weight."""
        results = _make_results(
            cs_score=50.0, mf_score=90.0,
            dm_score=50.0, tf_score=50.0,
        )
        _, strength_bear = self.svc.fuse(
            results=results, composite_score=70.0,
            safety_passed=True, regime_type="Bear",
        )
        _, strength_none = self.svc.fuse(
            results=results, composite_score=70.0,
            safety_passed=True, regime_type=None,
        )
        # Bear weights MF higher -> when MF scores high, bear gives higher strength
        assert strength_bear.value > strength_none.value

    def test_sideways_regime_boosts_magic_formula(self) -> None:
        """Sideways: MF 35%, DM only 15%."""
        results = _make_results(
            cs_score=70.0, mf_score=90.0,
            dm_score=40.0, tf_score=70.0,
        )
        _, strength_sideways = self.svc.fuse(
            results=results, composite_score=70.0,
            safety_passed=True, regime_type="Sideways",
        )
        _, strength_none = self.svc.fuse(
            results=results, composite_score=70.0,
            safety_passed=True, regime_type=None,
        )
        # Sideways gives MF more weight, DM less weight
        # With MF scoring high and DM scoring low, sideways should boost strength
        assert strength_sideways.value > strength_none.value

    def test_crisis_regime_boosts_magic_formula_most(self) -> None:
        """Crisis: MF gets 40% weight (max quality)."""
        results = _make_results(
            cs_score=30.0, mf_score=95.0,
            dm_score=50.0, tf_score=50.0,
        )
        _, strength_crisis = self.svc.fuse(
            results=results, composite_score=70.0,
            safety_passed=True, regime_type="Crisis",
        )
        _, strength_none = self.svc.fuse(
            results=results, composite_score=70.0,
            safety_passed=True, regime_type=None,
        )
        # Crisis gives MF 40%, with MF scoring 95 this should be higher
        assert strength_crisis.value > strength_none.value

    def test_none_regime_uses_equal_weights(self) -> None:
        """None regime_type uses equal 25% weights (backward compat)."""
        results = _make_results(
            cs_score=60.0, mf_score=70.0,
            dm_score=80.0, tf_score=90.0,
        )
        _, strength = self.svc.fuse(
            results=results, composite_score=70.0,
            safety_passed=True, regime_type=None,
        )
        # Equal weights: avg of matching = (60+70+80+90)/4 = 75
        # strength = 75*0.6 + 70*0.4 = 45+28 = 73.0
        assert strength.value == 73.0

    def test_consensus_logic_unchanged_by_regime(self) -> None:
        """Regime only affects strength, not direction consensus."""
        # 3/4 BUY with composite >= 60 -> BUY regardless of regime
        results_buy = _make_results(
            cs_dir=SignalDirection.BUY, mf_dir=SignalDirection.BUY,
            dm_dir=SignalDirection.BUY, tf_dir=SignalDirection.HOLD,
        )
        for regime in ["Bull", "Bear", "Sideways", "Crisis", None]:
            direction, _ = self.svc.fuse(
                results=results_buy, composite_score=70.0,
                safety_passed=True, regime_type=regime,
            )
            assert direction == SignalDirection.BUY, f"Failed for regime {regime}"

        # 3/4 SELL -> SELL regardless of regime
        results_sell = _make_results(
            cs_dir=SignalDirection.SELL, mf_dir=SignalDirection.SELL,
            dm_dir=SignalDirection.SELL, tf_dir=SignalDirection.HOLD,
        )
        for regime in ["Bull", "Bear", "Sideways", "Crisis", None]:
            direction, _ = self.svc.fuse(
                results=results_sell, composite_score=70.0,
                safety_passed=True, regime_type=regime,
            )
            assert direction == SignalDirection.SELL, f"Failed for regime {regime}"


class TestGenerateSignalCommandRegimeType:
    """Tests that GenerateSignalCommand accepts regime_type field."""

    def test_default_regime_type_is_none(self) -> None:
        cmd = GenerateSignalCommand(symbol="AAPL")
        assert cmd.regime_type is None

    def test_accepts_regime_type_string(self) -> None:
        cmd = GenerateSignalCommand(symbol="AAPL", regime_type="Bull")
        assert cmd.regime_type == "Bull"

    def test_accepts_all_regime_types(self) -> None:
        for regime in ["Bull", "Bear", "Sideways", "Crisis"]:
            cmd = GenerateSignalCommand(symbol="AAPL", regime_type=regime)
            assert cmd.regime_type == regime


class TestSignalStrategyWeightsDict:
    """Tests the SIGNAL_STRATEGY_WEIGHTS constant structure."""

    def test_all_four_regimes_present(self) -> None:
        assert set(SIGNAL_STRATEGY_WEIGHTS.keys()) == {"Bull", "Bear", "Sideways", "Crisis"}

    def test_all_four_methodologies_in_each_regime(self) -> None:
        expected_keys = {"CAN_SLIM", "MAGIC_FORMULA", "DUAL_MOMENTUM", "TREND_FOLLOWING"}
        for regime, weights in SIGNAL_STRATEGY_WEIGHTS.items():
            assert set(weights.keys()) == expected_keys, f"Missing keys for {regime}"

    def test_weights_sum_to_one_per_regime(self) -> None:
        for regime, weights in SIGNAL_STRATEGY_WEIGHTS.items():
            total = sum(weights.values())
            assert abs(total - 1.0) < 1e-9, f"Weights for {regime} sum to {total}"

    def test_default_weights_sum_to_one(self) -> None:
        total = sum(DEFAULT_SIGNAL_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_bull_momentum_combined_60_percent(self) -> None:
        bull = SIGNAL_STRATEGY_WEIGHTS["Bull"]
        momentum = bull["DUAL_MOMENTUM"] + bull["TREND_FOLLOWING"]
        assert abs(momentum - 0.60) < 1e-9

    def test_bear_quality_combined_50_percent(self) -> None:
        bear = SIGNAL_STRATEGY_WEIGHTS["Bear"]
        quality = bear["CAN_SLIM"] + bear["MAGIC_FORMULA"]
        assert abs(quality - 0.50) < 1e-9
