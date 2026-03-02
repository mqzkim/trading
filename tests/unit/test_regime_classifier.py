"""Unit tests for core/regime/classifier.py"""
import pytest
from core.regime.classifier import classify


def test_low_vol_bull():
    r = classify(vix=14, sp500_vs_200ma=1.08, adx=30, yield_curve_bps=50)
    assert r["regime"] == "Low-Vol Bull"
    assert r["confidence"] >= 0.65
    assert r["warning"] is None


def test_high_vol_bear():
    r = classify(vix=32, sp500_vs_200ma=0.92, adx=35, yield_curve_bps=-20)
    assert r["regime"] == "High-Vol Bear"
    assert "HIGH_VOL_BEAR" in r["warning"]


def test_high_vol_bull():
    r = classify(vix=22, sp500_vs_200ma=1.03, adx=28, yield_curve_bps=30)
    assert r["regime"] == "High-Vol Bull"


def test_low_vol_range():
    r = classify(vix=15, sp500_vs_200ma=0.99, adx=18, yield_curve_bps=20)
    assert r["regime"] == "Low-Vol Range"


def test_probabilities_sum_to_one():
    r = classify(vix=18, sp500_vs_200ma=1.05, adx=28, yield_curve_bps=40)
    total = sum(r["probabilities"].values())
    assert abs(total - 1.0) < 0.01


def test_inverted_curve_reduces_confidence():
    r_normal = classify(vix=14, sp500_vs_200ma=1.08, adx=30, yield_curve_bps=50)
    r_inverted = classify(vix=14, sp500_vs_200ma=1.08, adx=30, yield_curve_bps=-30)
    assert r_inverted["confidence"] <= r_normal["confidence"]


def test_all_regimes_covered():
    result = classify(vix=19, sp500_vs_200ma=0.97, adx=20, yield_curve_bps=10)
    assert result["regime"] in ["Low-Vol Bull", "High-Vol Bull", "Low-Vol Range",
                                 "High-Vol Bear", "Transition"]


def test_extreme_vix_warning():
    r = classify(vix=35, sp500_vs_200ma=0.85, adx=40, yield_curve_bps=-50)
    assert r["warning"] is not None
