"""Integration test: full pipeline smoke test."""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from core.orchestrator import run_full_pipeline, PipelineResult


def _mock_data(close: float = 150.0) -> dict:
    """Build a mock data dict matching DataClient.get_full output."""
    return {
        "price": {"close": close, "open": 149.0, "high": 152.0, "low": 148.0},
        "indicators": {
            "atr21": 3.5,
            "adx14": 22.0,
            "ma50": 145.0,
            "ma200": 140.0,
            "rsi14": 55.0,
            "macd_histogram": 0.5,
        },
        "fundamentals": {
            "highlights": {
                "roe": 0.18,
                "pe_ratio": 20.0,
                "current_ratio": 1.8,
            }
        },
    }


# --- Test 1: Pipeline smoke test ---


@patch("core.orchestrator.plan_entry", return_value={"status": "APPROVED"})
@patch(
    "core.orchestrator.validate_position",
    return_value={"passed": True, "violations": []},
)
@patch(
    "core.orchestrator.atr_position_size",
    return_value={"shares": 100, "position_value": 15000.0},
)
@patch(
    "core.orchestrator.check_entry_allowed",
    return_value={"allowed": True, "drawdown_level": 0, "reason": ""},
)
@patch(
    "core.orchestrator.score_symbol",
    return_value={
        "composite_score": 72.0,
        "risk_adjusted_score": 68.0,
        "safety_passed": True,
    },
)
@patch(
    "core.orchestrator.generate_signals",
    return_value={"consensus": "BULLISH", "agreement": 3},
)
@patch(
    "core.orchestrator.classify",
    return_value={"regime": "Low-Vol Bull", "confidence": 0.85, "warning": None},
)
@patch("core.orchestrator.get_yield_curve_slope", return_value=50.0)
@patch("core.orchestrator.get_sp500_vs_200ma", return_value=1.05)
@patch("core.orchestrator.get_vix", return_value=15.0)
@patch("core.orchestrator.DataClient")
def test_pipeline_smoke_test(
    mock_dc_cls,
    mock_vix,
    mock_sp500,
    mock_yc,
    mock_classify,
    mock_signals,
    mock_score,
    mock_entry_check,
    mock_sizing,
    mock_validate,
    mock_plan,
):
    mock_client = MagicMock()
    mock_client.get_full.return_value = _mock_data()
    mock_dc_cls.return_value = mock_client

    result = run_full_pipeline("AAPL", capital=100_000.0)

    assert isinstance(result, PipelineResult)
    assert result.symbol == "AAPL"
    assert result.error is None
    assert result.regime == "Low-Vol Bull"
    assert result.consensus == "BULLISH"
    assert result.composite_score == 72.0


# --- Test 2: Bullish scenario ---


@patch("core.orchestrator.plan_entry", return_value={"status": "APPROVED"})
@patch(
    "core.orchestrator.validate_position",
    return_value={"passed": True, "violations": []},
)
@patch(
    "core.orchestrator.atr_position_size",
    return_value={"shares": 50, "position_value": 7500.0},
)
@patch(
    "core.orchestrator.check_entry_allowed",
    return_value={"allowed": True, "drawdown_level": 0, "reason": ""},
)
@patch(
    "core.orchestrator.score_symbol",
    return_value={
        "composite_score": 80.0,
        "risk_adjusted_score": 76.0,
        "safety_passed": True,
    },
)
@patch(
    "core.orchestrator.generate_signals",
    return_value={"consensus": "BULLISH", "agreement": 4},
)
@patch(
    "core.orchestrator.classify",
    return_value={"regime": "Low-Vol Bull", "confidence": 0.90, "warning": None},
)
@patch("core.orchestrator.get_yield_curve_slope", return_value=60.0)
@patch("core.orchestrator.get_sp500_vs_200ma", return_value=1.08)
@patch("core.orchestrator.get_vix", return_value=12.0)
@patch("core.orchestrator.DataClient")
def test_pipeline_bullish_scenario(
    mock_dc_cls,
    mock_vix,
    mock_sp500,
    mock_yc,
    mock_classify,
    mock_signals,
    mock_score,
    mock_entry_check,
    mock_sizing,
    mock_validate,
    mock_plan,
):
    mock_client = MagicMock()
    mock_client.get_full.return_value = _mock_data(close=160.0)
    mock_dc_cls.return_value = mock_client

    result = run_full_pipeline("MSFT", capital=100_000.0)

    assert isinstance(result, PipelineResult)
    assert result.error is None
    assert result.consensus in ("BULLISH", "NEUTRAL")
    assert result.regime == "Low-Vol Bull"
    assert result.regime_confidence >= 0.8


# --- Test 3: Data error returns error result ---


@patch("core.orchestrator.DataClient")
def test_pipeline_data_error_returns_error_result(mock_dc_cls):
    mock_client = MagicMock()
    mock_client.get_full.side_effect = ConnectionError("API timeout")
    mock_dc_cls.return_value = mock_client

    result = run_full_pipeline("FAIL")

    assert isinstance(result, PipelineResult)
    assert result.error is not None
    assert "Data fetch failed" in result.error
    assert result.symbol == "FAIL"
    assert result.consensus == "NEUTRAL"
    assert result.position_shares == 0
