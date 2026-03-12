"""Tests for CLI dashboard command (INTF-01).

Tests dashboard rendering with mocked repos:
  - Dashboard renders without error when no positions
  - Dashboard renders positions table with mock positions
"""
from __future__ import annotations

from datetime import date
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

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


_POS_REPO = "src.portfolio.infrastructure.sqlite_position_repo.SqlitePositionRepository"
_PORT_REPO = "src.portfolio.infrastructure.sqlite_portfolio_repo.SqlitePortfolioRepository"


class TestDashboardCommand:
    """Dashboard CLI command tests."""

    @patch(_PORT_REPO)
    @patch(_POS_REPO)
    def test_dashboard_no_positions(self, mock_pos_cls, mock_port_cls) -> None:
        """Dashboard with no positions shows empty message."""
        mock_pos_inst = MagicMock()
        mock_pos_inst.find_all_open.return_value = []
        mock_pos_cls.return_value = mock_pos_inst

        mock_port_inst = MagicMock()
        mock_port_inst.find_by_id.return_value = _make_portfolio()
        mock_port_cls.return_value = mock_port_inst

        result = runner.invoke(app, ["dashboard"])
        assert result.exit_code == 0
        assert "No open positions" in result.output

    @patch(_PORT_REPO)
    @patch(_POS_REPO)
    def test_dashboard_renders_positions_table(self, mock_pos_cls, mock_port_cls) -> None:
        """Dashboard with positions renders a table with symbols."""
        positions = [
            _make_position("AAPL", 150.0, 20, "Technology"),
            _make_position("MSFT", 350.0, 10, "Technology"),
        ]
        mock_pos_inst = MagicMock()
        mock_pos_inst.find_all_open.return_value = positions
        mock_pos_cls.return_value = mock_pos_inst

        mock_port_inst = MagicMock()
        mock_port_inst.find_by_id.return_value = _make_portfolio(initial_value=100_000.0)
        mock_port_cls.return_value = mock_port_inst

        result = runner.invoke(app, ["dashboard"])
        assert result.exit_code == 0
        assert "AAPL" in result.output
        assert "MSFT" in result.output

    @patch(_PORT_REPO)
    @patch(_POS_REPO)
    def test_dashboard_shows_drawdown_level(self, mock_pos_cls, mock_port_cls) -> None:
        """Dashboard shows drawdown percentage and level."""
        mock_pos_inst = MagicMock()
        mock_pos_inst.find_all_open.return_value = []
        mock_pos_cls.return_value = mock_pos_inst

        mock_port_inst = MagicMock()
        mock_port_inst.find_by_id.return_value = _make_portfolio(drawdown=0.12, level="caution")
        mock_port_cls.return_value = mock_port_inst

        result = runner.invoke(app, ["dashboard"])
        assert result.exit_code == 0
        assert "12.0%" in result.output

    @patch(_PORT_REPO)
    @patch(_POS_REPO)
    def test_dashboard_no_portfolio_uses_defaults(self, mock_pos_cls, mock_port_cls) -> None:
        """Dashboard with no saved portfolio still renders."""
        mock_pos_inst = MagicMock()
        mock_pos_inst.find_all_open.return_value = []
        mock_pos_cls.return_value = mock_pos_inst

        mock_port_inst = MagicMock()
        mock_port_inst.find_by_id.return_value = None
        mock_port_cls.return_value = mock_port_inst

        result = runner.invoke(app, ["dashboard"])
        assert result.exit_code == 0
