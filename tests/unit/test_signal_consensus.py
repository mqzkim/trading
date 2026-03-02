"""Unit tests for signal consensus."""
import pytest
from core.signals.consensus import compute_consensus


def _make(signal, score=1, score_max=1):
    return {"signal": signal, "score": score, "score_max": score_max}


def test_bullish_consensus():
    r = compute_consensus(_make("BUY"), _make("BUY"), _make("BUY"), _make("HOLD"))
    assert r["consensus"] == "BULLISH"
    assert r["agreement"] == 3


def test_bearish_consensus():
    r = compute_consensus(_make("SELL"), _make("SELL"), _make("SELL"), _make("HOLD"))
    assert r["consensus"] == "BEARISH"


def test_neutral_consensus():
    r = compute_consensus(_make("BUY"), _make("SELL"), _make("HOLD"), _make("HOLD"))
    assert r["consensus"] == "NEUTRAL"


def test_weighted_score_range():
    r = compute_consensus(_make("BUY", 7, 7), _make("BUY", 80, 100),
                          _make("BUY", 2, 2), _make("BUY", 3, 3))
    assert 0 <= r["weighted_score"] <= 1


def test_regime_weights_applied():
    buy4 = [_make("BUY", 1, 1)] * 4
    r_bull = compute_consensus(*buy4, regime="Low-Vol Bull")
    r_bear = compute_consensus(*buy4, regime="High-Vol Bear")
    assert r_bull["regime_context"] == "Low-Vol Bull"
    assert r_bear["regime_context"] == "High-Vol Bear"


def test_methods_keys():
    r = compute_consensus(_make("BUY"), _make("HOLD"), _make("SELL"), _make("BUY"))
    assert set(r["methods"].keys()) == {"canslim", "magic_formula", "dual_momentum", "trend_following"}
