"""Unit tests for enhanced reasoning trace with regime context (SIGNAL-07).

Tests that _build_reasoning_trace includes regime name, strategy weight
percentages, and per-methodology weight annotations when regime_type is provided,
and omits them for backward compat when regime_type is None.
"""
from __future__ import annotations

import pytest
from src.signals.domain.value_objects import (
    SignalDirection,
    MethodologyType,
    MethodologyResult,
)
from src.signals.application.handlers import GenerateSignalHandler
from src.signals.domain.services import SIGNAL_STRATEGY_WEIGHTS, DEFAULT_SIGNAL_WEIGHTS


def _make_results() -> list[MethodologyResult]:
    """Helper to build 4 methodology results for reasoning trace tests."""
    return [
        MethodologyResult(methodology=MethodologyType.CAN_SLIM, direction=SignalDirection.BUY, score=75.0),
        MethodologyResult(methodology=MethodologyType.MAGIC_FORMULA, direction=SignalDirection.BUY, score=80.0),
        MethodologyResult(methodology=MethodologyType.DUAL_MOMENTUM, direction=SignalDirection.HOLD, score=55.0),
        MethodologyResult(methodology=MethodologyType.TREND_FOLLOWING, direction=SignalDirection.BUY, score=70.0),
    ]


class TestBuildReasoningTraceWithRegime:
    """Tests for _build_reasoning_trace with regime context."""

    def setup_method(self) -> None:
        """Create handler with minimal deps for trace building."""
        # We only need the handler to call _build_reasoning_trace
        # signal_repo is not used for trace building
        from unittest.mock import MagicMock
        self.handler = GenerateSignalHandler(signal_repo=MagicMock())

    def test_bull_regime_includes_regime_line(self) -> None:
        """Reasoning trace with regime_type='Bull' includes 'Regime: Bull' line."""
        results = _make_results()
        weights = SIGNAL_STRATEGY_WEIGHTS["Bull"]
        trace = self.handler._build_reasoning_trace(
            symbol="AAPL",
            direction="BUY",
            composite_score=72.0,
            margin_of_safety=0.15,
            methodology_results=results,
            safety_passed=True,
            regime_type="Bull",
            strategy_weights=weights,
        )
        assert "Regime: Bull" in trace

    def test_none_regime_omits_regime_line(self) -> None:
        """Reasoning trace with regime_type=None omits regime and weight lines."""
        results = _make_results()
        trace = self.handler._build_reasoning_trace(
            symbol="AAPL",
            direction="BUY",
            composite_score=72.0,
            margin_of_safety=0.15,
            methodology_results=results,
            safety_passed=True,
            regime_type=None,
            strategy_weights=None,
        )
        assert "Regime:" not in trace
        assert "Strategy Weights:" not in trace

    def test_bull_regime_shows_strategy_weight_percentages(self) -> None:
        """Reasoning trace shows per-strategy weight percentages for Bull regime."""
        results = _make_results()
        weights = SIGNAL_STRATEGY_WEIGHTS["Bull"]
        trace = self.handler._build_reasoning_trace(
            symbol="AAPL",
            direction="BUY",
            composite_score=72.0,
            margin_of_safety=0.15,
            methodology_results=results,
            safety_passed=True,
            regime_type="Bull",
            strategy_weights=weights,
        )
        # Bull weights: CAN_SLIM 20%, MAGIC_FORMULA 20%, DUAL_MOMENTUM 30%, TREND_FOLLOWING 30%
        assert "Strategy Weights:" in trace
        assert "20%" in trace
        assert "30%" in trace

    def test_per_strategy_weight_annotation_in_methodology_line(self) -> None:
        """Each methodology line shows its weight annotation when regime is set."""
        results = _make_results()
        weights = SIGNAL_STRATEGY_WEIGHTS["Bear"]
        trace = self.handler._build_reasoning_trace(
            symbol="AAPL",
            direction="BUY",
            composite_score=72.0,
            margin_of_safety=0.15,
            methodology_results=results,
            safety_passed=True,
            regime_type="Bear",
            strategy_weights=weights,
        )
        # Bear: CAN_SLIM 15%, MAGIC_FORMULA 35%, DUAL_MOMENTUM 25%, TREND_FOLLOWING 25%
        # Each methodology line should have "weight XX%"
        assert "weight 15%" in trace  # CAN SLIM
        assert "weight 35%" in trace  # Magic Formula
        assert "weight 25%" in trace  # Dual Momentum and Trend Following

    def test_no_weight_annotation_without_strategy_weights(self) -> None:
        """Methodology lines do not show weight annotations when strategy_weights is None."""
        results = _make_results()
        trace = self.handler._build_reasoning_trace(
            symbol="AAPL",
            direction="BUY",
            composite_score=72.0,
            margin_of_safety=0.15,
            methodology_results=results,
            safety_passed=True,
            regime_type=None,
            strategy_weights=None,
        )
        assert "weight" not in trace.lower() or "weight" not in trace
