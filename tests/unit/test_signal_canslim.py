"""Unit tests for CAN SLIM signal."""
import pytest
from core.signals.canslim import evaluate


def test_strong_buy_all_criteria():
    r = evaluate(
        eps_growth_qoq=35, eps_cagr_3y=30, near_52w_high=True,
        volume_ratio=1.8, relative_strength=85, institutional_increase=True,
        market_uptrend=True,
    )
    assert r["signal"] == "BUY"
    assert r["score"] == 7


def test_sell_poor_fundamentals():
    r = evaluate(
        eps_growth_qoq=5, eps_cagr_3y=3, near_52w_high=False,
        volume_ratio=0.8, relative_strength=30, institutional_increase=False,
        market_uptrend=False,
    )
    assert r["signal"] == "SELL"
    assert r["score"] <= 2


def test_none_values_handled():
    r = evaluate(eps_growth_qoq=None, eps_cagr_3y=None)
    assert r["signal"] in ("BUY", "HOLD", "SELL")
    assert 0 <= r["score"] <= 7


def test_market_uptrend_required():
    r_up = evaluate(eps_growth_qoq=30, eps_cagr_3y=28, near_52w_high=True,
                    volume_ratio=1.6, relative_strength=82, institutional_increase=True,
                    market_uptrend=True)
    r_down = evaluate(eps_growth_qoq=30, eps_cagr_3y=28, near_52w_high=True,
                      volume_ratio=1.6, relative_strength=82, institutional_increase=True,
                      market_uptrend=False)
    assert r_up["score"] > r_down["score"]
