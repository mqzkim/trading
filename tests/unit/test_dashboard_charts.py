"""Tests for Plotly chart JSON generation utilities."""
from __future__ import annotations

from src.dashboard.presentation.charts import (
    build_drawdown_gauge,
    build_equity_curve,
    build_sector_donut,
)


def test_build_drawdown_gauge_returns_valid_json():
    result = build_drawdown_gauge(12.0)
    assert "data" in result
    assert "layout" in result
    assert result["data"][0]["type"] == "indicator"


def test_build_equity_curve_returns_valid_json():
    dates = ["2026-01-01", "2026-01-02", "2026-01-03"]
    values = [100.0, 102.0, 101.5]
    regimes = [{"start": "2026-01-01", "end": "2026-01-03", "regime": "Bull"}]
    result = build_equity_curve(values=values, dates=dates, regime_periods=regimes)
    assert "data" in result
    assert "layout" in result


def test_build_sector_donut_returns_valid_json():
    sectors = {"Tech": 0.3, "Health": 0.2}
    result = build_sector_donut(sectors)
    assert "data" in result


def test_drawdown_gauge_range():
    result = build_drawdown_gauge(5.0)
    gauge = result["data"][0]["gauge"]
    axis_range = gauge["axis"]["range"]
    assert axis_range == [0, 20]


def test_equity_curve_empty_data():
    result = build_equity_curve(values=[], dates=[], regime_periods=[])
    assert "data" in result
    assert "layout" in result
