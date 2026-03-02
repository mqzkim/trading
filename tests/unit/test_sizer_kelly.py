"""Tests for position sizer."""
import pytest
from personal.sizer.kelly import (
    kelly_fraction, atr_position_size, validate_position,
    KELLY_FRACTION, MAX_POSITION_PCT, RISK_PER_TRADE_PCT
)


def test_kelly_fraction_basic():
    f = kelly_fraction(win_rate=0.55, avg_win=2.0, avg_loss=1.0)
    assert f > 0
    assert f <= MAX_POSITION_PCT  # capped


def test_kelly_never_exceeds_max():
    f = kelly_fraction(win_rate=0.90, avg_win=10.0, avg_loss=1.0)
    assert f <= MAX_POSITION_PCT


def test_kelly_zero_on_bad_inputs():
    assert kelly_fraction(0, 1, 1) == 0.0
    assert kelly_fraction(1, 1, 0) == 0.0


def test_atr_sizing_basic():
    result = atr_position_size(capital=100_000, entry_price=100, atr=2.0, atr_multiplier=3.0)
    assert result["shares"] > 0
    assert result["stop_price"] == pytest.approx(94.0, abs=0.1)
    assert result["risk_pct"] <= RISK_PER_TRADE_PCT * 100 + 0.1


def test_atr_stop_price_correct():
    r = atr_position_size(100_000, 150, 3.0, 2.5)
    expected_stop = 150 - 2.5 * 3.0
    assert r["stop_price"] == pytest.approx(expected_stop, abs=0.01)


def test_atr_position_pct_under_max():
    r = atr_position_size(100_000, 50, 1.0, 3.0)
    assert r["position_pct"] <= MAX_POSITION_PCT * 100 + 0.1


def test_atr_multiplier_clamped():
    r1 = atr_position_size(100_000, 100, 2.0, 1.0)   # below 2.5
    r2 = atr_position_size(100_000, 100, 2.0, 2.5)   # at minimum
    assert r1["atr_multiplier"] == r2["atr_multiplier"] == 2.5


def test_validate_position_pass():
    r = validate_position(5_000, 100_000)  # 5% position
    assert r["passed"] is True


def test_validate_position_fail_size():
    r = validate_position(9_000, 100_000)  # 9% > 8%
    assert r["passed"] is False
    assert len(r["violations"]) > 0


def test_validate_sector_limit():
    r = validate_position(5_000, 100_000, sector_exposure=0.22)  # 22+5=27% > 25%
    assert r["passed"] is False
