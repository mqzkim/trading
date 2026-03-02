"""Unit tests for core/scoring/composite.py"""
import pytest
from core.scoring.composite import compute_composite, score_symbol, WEIGHTS


def test_composite_equal_weights():
    result = compute_composite(80, 70, 60, strategy="swing")
    w = WEIGHTS["swing"]
    expected = w["fundamental"] * 80 + w["technical"] * 70 + w["sentiment"] * 60
    assert abs(result["composite_score"] - expected) < 0.1


def test_composite_clamped_to_100():
    result = compute_composite(100, 100, 100)
    assert result["composite_score"] <= 100


def test_composite_clamped_to_0():
    result = compute_composite(0, 0, 0)
    assert result["composite_score"] >= 0


def test_risk_adjusted_lower():
    result = compute_composite(80, 70, 60, tail_risk_penalty=10)
    assert result["risk_adjusted_score"] < result["composite_score"]


def test_score_symbol_safety_fail():
    fundamental_fail = {
        "safety_passed": False,
        "z_score": 0.5,
        "m_score": -1.0,
        "fundamental_score": 0,
    }
    result = score_symbol("TEST", fundamental_fail, {"technical_score": 80}, {"sentiment_score": 70})
    assert result["composite_score"] == 0
    assert result["safety_passed"] is False


def test_score_symbol_safety_pass():
    fundamental_pass = {
        "safety_passed": True,
        "z_score": 3.0,
        "m_score": -2.5,
        "fundamental_score": 75,
        "f_score": 7,
    }
    result = score_symbol("AAPL", fundamental_pass, {"technical_score": 80}, {"sentiment_score": 65})
    assert result["safety_passed"] is True
    assert result["composite_score"] > 0
    assert result["symbol"] == "AAPL"


def test_strategy_weights():
    r_swing = compute_composite(80, 60, 50, strategy="swing")
    r_position = compute_composite(80, 60, 50, strategy="position")
    # Position gives more weight to fundamental (80), so position score should be higher
    assert r_position["composite_score"] > r_swing["composite_score"]
