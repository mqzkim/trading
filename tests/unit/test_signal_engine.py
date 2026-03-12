"""Tests for signal generation engine with reasoning traces (SIGN-01).

Tests CoreSignalAdapter wrapping core/signals/ evaluators, and
GenerateSignalHandler producing BUY/HOLD/SELL with reasoning traces.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from src.signals.infrastructure.core_signal_adapter import CoreSignalAdapter
from src.signals.infrastructure.in_memory_repo import InMemorySignalRepository
from src.signals.application.commands import GenerateSignalCommand
from src.signals.application.handlers import GenerateSignalHandler


# ── CoreSignalAdapter unit tests ─────────────────────────────────


class TestCoreSignalAdapter:
    """Tests that CoreSignalAdapter correctly wraps core/signals/ evaluators."""

    def setup_method(self) -> None:
        self.adapter = CoreSignalAdapter()

    def test_evaluate_canslim_returns_required_keys(self) -> None:
        result = self.adapter.evaluate_canslim(
            eps_growth_qoq=30.0,
            eps_cagr_3y=28.0,
            near_52w_high=True,
            volume_ratio=1.5,
            relative_strength=85,
            institutional_increase=True,
            market_uptrend=True,
        )
        assert "signal" in result
        assert "score" in result
        assert "score_max" in result
        assert result["score_max"] == 7

    def test_evaluate_all_calls_four_evaluators(self) -> None:
        symbol_data = {
            # CAN SLIM inputs
            "eps_growth_qoq": 30.0,
            "eps_cagr_3y": 28.0,
            "near_52w_high": True,
            "volume_ratio": 1.5,
            "relative_strength": 85,
            "institutional_increase": True,
            "market_uptrend": True,
            # Magic Formula inputs
            "earnings_yield": 0.12,
            "return_on_capital": 0.25,
            "ey_percentile": 80.0,
            "roc_percentile": 75.0,
            # Dual Momentum inputs
            "return_12m": 0.15,
            "return_12m_benchmark": 0.10,
            "tbill_rate": 0.04,
            # Trend Following inputs
            "above_ma50": True,
            "above_ma200": True,
            "adx": 30.0,
            "at_20d_high": True,
        }
        results = self.adapter.evaluate_all(symbol_data)
        assert len(results) == 4
        for r in results:
            assert "signal" in r
            assert "score" in r
            assert "score_max" in r


# ── GenerateSignalHandler with CoreSignalAdapter tests ───────────


def _make_adapter_mock(
    canslim_signal: str = "BUY",
    canslim_score: int = 6,
    magic_signal: str = "BUY",
    magic_score: float = 80.0,
    dual_signal: str = "BUY",
    dual_score: int = 2,
    trend_signal: str = "HOLD",
    trend_score: int = 1,
) -> CoreSignalAdapter:
    """Create a mock CoreSignalAdapter returning controlled results."""
    adapter = MagicMock(spec=CoreSignalAdapter)
    adapter.evaluate_all.return_value = [
        {"signal": canslim_signal, "score": canslim_score, "score_max": 7, "methodology": "CAN SLIM"},
        {"signal": magic_signal, "score": magic_score, "score_max": 100, "methodology": "Magic Formula"},
        {"signal": dual_signal, "score": dual_score, "score_max": 2, "methodology": "Dual Momentum"},
        {"signal": trend_signal, "score": trend_score, "score_max": 3, "methodology": "Trend Following"},
    ]
    return adapter


class TestGenerateSignalHandlerWithAdapter:
    """Tests signal generation using CoreSignalAdapter for methodology evaluation."""

    def setup_method(self) -> None:
        self.repo = InMemorySignalRepository()

    def test_buy_when_3_of_4_agree_buy_and_composite_ge_60_and_safety_passed(self) -> None:
        adapter = _make_adapter_mock(
            canslim_signal="BUY", magic_signal="BUY", dual_signal="BUY", trend_signal="HOLD",
        )
        handler = GenerateSignalHandler(
            signal_repo=self.repo,
            signal_adapter=adapter,
        )
        cmd = GenerateSignalCommand(
            symbol="AAPL",
            composite_score=75.0,
            safety_passed=True,
            symbol_data={"some": "data"},
        )
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        assert data["direction"] == "BUY"

    def test_sell_when_composite_below_30(self) -> None:
        adapter = _make_adapter_mock(
            canslim_signal="HOLD", magic_signal="HOLD", dual_signal="HOLD", trend_signal="HOLD",
        )
        handler = GenerateSignalHandler(
            signal_repo=self.repo,
            signal_adapter=adapter,
        )
        cmd = GenerateSignalCommand(
            symbol="AAPL",
            composite_score=25.0,
            safety_passed=True,
            symbol_data={"some": "data"},
        )
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        assert data["direction"] == "SELL"

    def test_hold_when_safety_not_passed(self) -> None:
        adapter = _make_adapter_mock(
            canslim_signal="BUY", magic_signal="BUY", dual_signal="BUY", trend_signal="BUY",
        )
        handler = GenerateSignalHandler(
            signal_repo=self.repo,
            signal_adapter=adapter,
        )
        cmd = GenerateSignalCommand(
            symbol="AAPL",
            composite_score=80.0,
            safety_passed=False,
            symbol_data={"some": "data"},
        )
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        assert data["direction"] == "HOLD"

    def test_result_includes_reasoning_trace(self) -> None:
        adapter = _make_adapter_mock()
        handler = GenerateSignalHandler(
            signal_repo=self.repo,
            signal_adapter=adapter,
        )
        cmd = GenerateSignalCommand(
            symbol="AAPL",
            composite_score=75.0,
            safety_passed=True,
            margin_of_safety=0.15,
            symbol_data={"some": "data"},
        )
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        assert "reasoning_trace" in data
        trace = data["reasoning_trace"]
        assert isinstance(trace, str)
        assert len(trace) > 0

    def test_reasoning_trace_contains_required_data_points(self) -> None:
        adapter = _make_adapter_mock()
        handler = GenerateSignalHandler(
            signal_repo=self.repo,
            signal_adapter=adapter,
        )
        cmd = GenerateSignalCommand(
            symbol="MSFT",
            composite_score=72.0,
            safety_passed=True,
            margin_of_safety=0.20,
            symbol_data={"some": "data"},
        )
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        trace = data["reasoning_trace"]

        # Must contain symbol
        assert "MSFT" in trace
        # Must contain direction
        assert data["direction"] in trace
        # Must contain composite score value
        assert "72.0" in trace or "72" in trace
        # Must contain at least one methodology name
        methodology_names = ["CAN SLIM", "Magic Formula", "Dual Momentum", "Trend Following"]
        found_methodologies = sum(1 for m in methodology_names if m in trace)
        assert found_methodologies >= 3, f"Expected at least 3 methodology citations, found {found_methodologies}"

    def test_reasoning_trace_cites_margin_of_safety(self) -> None:
        adapter = _make_adapter_mock()
        handler = GenerateSignalHandler(
            signal_repo=self.repo,
            signal_adapter=adapter,
        )
        cmd = GenerateSignalCommand(
            symbol="GOOG",
            composite_score=65.0,
            safety_passed=True,
            margin_of_safety=0.25,
            symbol_data={"some": "data"},
        )
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        trace = data["reasoning_trace"]
        # Must cite margin of safety
        assert "25.0%" in trace or "25%" in trace or "0.25" in trace

    def test_reasoning_trace_cites_safety_gate_status(self) -> None:
        adapter = _make_adapter_mock()
        handler = GenerateSignalHandler(
            signal_repo=self.repo,
            signal_adapter=adapter,
        )
        cmd = GenerateSignalCommand(
            symbol="TSLA",
            composite_score=70.0,
            safety_passed=True,
            symbol_data={"some": "data"},
        )
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        trace = data["reasoning_trace"]
        assert "PASS" in trace or "pass" in trace.lower()
