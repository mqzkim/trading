"""Tests for drawdown defense."""
import pytest
from personal.risk.drawdown import assess_drawdown, LEVEL_1_PCT, LEVEL_2_PCT, LEVEL_3_PCT


def test_normal_no_drawdown():
    r = assess_drawdown(100_000, 100_000)
    assert r["level"] == 0
    assert r["allow_new_entries"] is True


def test_level1_halt_entries():
    r = assess_drawdown(100_000, 89_000)  # 11% drawdown
    assert r["level"] == 1
    assert r["allow_new_entries"] is False
    assert r["reduce_pct"] == 0.0


def test_level2_reduce_50pct():
    r = assess_drawdown(100_000, 84_000)  # 16% drawdown
    assert r["level"] == 2
    assert r["reduce_pct"] == 0.5
    assert r["allow_new_entries"] is False


def test_level3_full_liquidation():
    r = assess_drawdown(100_000, 79_000)  # 21% drawdown
    assert r["level"] == 3
    assert r["reduce_pct"] == 1.0
    assert r["requires_cooldown"] is True


def test_cooldown_blocks_entries():
    r = assess_drawdown(100_000, 95_000, cooldown_days_remaining=15)
    assert r["level"] == 3
    assert r["in_cooldown"] is True
    assert r["allow_new_entries"] is False


def test_boundary_exactly_10pct():
    r = assess_drawdown(100_000, 90_000)  # exactly 10%
    assert r["level"] == 1


def test_boundary_exactly_15pct():
    r = assess_drawdown(100_000, 85_000)  # exactly 15%
    assert r["level"] == 2


def test_boundary_exactly_20pct():
    r = assess_drawdown(100_000, 80_000)  # exactly 20%
    assert r["level"] == 3
