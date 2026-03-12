"""Tests for CLI dashboard command (INTF-01).

Tests dashboard rendering with mocked bootstrap context:
  - Dashboard renders without error when no positions
  - Dashboard renders positions table with mock positions
"""
from __future__ import annotations

from datetime import date
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

import cli.main
from cli.main import app


runner = CliRunner()


def _make_position(symbol: str, entry_price: float, quantity: int, sector: str = "Technology") -> MagicMock:
    """Create a mock Position with required attributes."""
    pos = MagicMock()
    pos.symbol = symbol
    pos.entry_price = entry_price
    pos.quantity = quantity
    pos.sector = sector
    pos.strategy = "swing"
    pos.market_value = entry_price * quantity
    pos.atr_stop = None
    return pos


def _make_portfolio(initial_value: float = 100_000.0, drawdown: float = 0.0, level: str = "normal") -> MagicMock:
    """Create a mock Portfolio aggregate."""
    from src.portfolio.domain.value_objects import DrawdownLevel

    portfolio = MagicMock()
    portfolio.initial_value = initial_value
    portfolio.total_value_or_initial = initial_value
    portfolio.drawdown = drawdown
    portfolio.drawdown_level = DrawdownLevel(level)
    return portfolio


def _setup_bootstrap_ctx(positions=None, portfolio=None):
    """Create a mock bootstrap context and inject it into cli.main._ctx_cache."""
    mock_portfolio_handler = MagicMock()
    mock_portfolio_handler._position_repo.find_all_open.return_value = positions or []
    mock_portfolio_handler._portfolio_repo.find_by_id.return_value = portfolio

    ctx = {
        "trade_plan_handler": MagicMock(),
        "portfolio_handler": mock_portfolio_handler,
        "bus": MagicMock(),
        "db_factory": MagicMock(),
        "score_handler": MagicMock(),
        "signal_handler": MagicMock(),
        "regime_handler": MagicMock(),
        "capital": 100_000.0,
        "market": "us",
    }
    cli.main._ctx_cache["us"] = ctx
    return ctx


def _teardown_ctx():
    """Reset cli.main._ctx_cache after test."""
    cli.main._ctx_cache.clear()


class TestDashboardCommand:
    """Dashboard CLI command tests."""

    def test_dashboard_no_positions(self) -> None:
        """Dashboard with no positions shows empty message."""
        _setup_bootstrap_ctx(positions=[], portfolio=_make_portfolio())
        try:
            result = runner.invoke(app, ["dashboard"])
            assert result.exit_code == 0
            assert "No open positions" in result.output
        finally:
            _teardown_ctx()

    def test_dashboard_renders_positions_table(self) -> None:
        """Dashboard with positions renders a table with symbols."""
        positions = [
            _make_position("AAPL", 150.0, 20, "Technology"),
            _make_position("MSFT", 350.0, 10, "Technology"),
        ]
        _setup_bootstrap_ctx(positions=positions, portfolio=_make_portfolio(initial_value=100_000.0))
        try:
            result = runner.invoke(app, ["dashboard"])
            assert result.exit_code == 0
            assert "AAPL" in result.output
            assert "MSFT" in result.output
        finally:
            _teardown_ctx()

    def test_dashboard_shows_drawdown_level(self) -> None:
        """Dashboard shows drawdown percentage and level."""
        _setup_bootstrap_ctx(positions=[], portfolio=_make_portfolio(drawdown=0.12, level="caution"))
        try:
            result = runner.invoke(app, ["dashboard"])
            assert result.exit_code == 0
            assert "12.0%" in result.output
        finally:
            _teardown_ctx()

    def test_dashboard_no_portfolio_uses_defaults(self) -> None:
        """Dashboard with no saved portfolio still renders."""
        _setup_bootstrap_ctx(positions=[], portfolio=None)
        try:
            result = runner.invoke(app, ["dashboard"])
            assert result.exit_code == 0
        finally:
            _teardown_ctx()
