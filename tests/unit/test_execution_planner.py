"""Tests for execution planner."""
import pytest
from personal.execution.planner import plan_entry, plan_exit


def test_entry_approved():
    result = plan_entry(
        symbol="AAPL",
        entry_price=150.0,
        atr=3.0,
        capital=100_000,
        peak_value=100_000,
        current_value=100_000,
    )
    assert result["status"] == "APPROVED"
    assert result["shares"] > 0
    assert result["stop_price"] < 150.0


def test_entry_rejected_on_drawdown():
    result = plan_entry(
        symbol="AAPL",
        entry_price=150.0,
        atr=3.0,
        capital=100_000,
        peak_value=100_000,
        current_value=79_000,  # 21% drawdown
    )
    assert result["status"] == "REJECTED"
    assert len(result["violations"]) > 0


def test_entry_limit_order_price():
    result = plan_entry("MSFT", 300, 5.0, 200_000, 200_000, 200_000, order_type="LIMIT")
    assert result["status"] == "APPROVED"
    assert result["limit_price"] < result["entry_price"]


def test_exit_stop_triggered():
    result = plan_exit("AAPL", current_price=140, stop_price=145, shares=50)
    assert result["triggered"] is True
    assert result["action"] == "SELL"


def test_exit_stop_not_triggered():
    result = plan_exit("AAPL", current_price=160, stop_price=145, shares=50)
    assert result["triggered"] is False


def test_risk_pct_within_limit():
    result = plan_entry("TSLA", 200, 4.0, 100_000, 100_000, 100_000)
    if result["status"] == "APPROVED":
        assert result["risk_pct"] <= 1.1  # 1% + small tolerance
