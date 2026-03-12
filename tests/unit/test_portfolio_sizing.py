"""Tests for PortfolioManagerHandler with take-profit and sector checks (RISK-01 through RISK-05)."""
from __future__ import annotations

from src.portfolio.application.commands import OpenPositionCommand
from src.portfolio.application.handlers import PortfolioManagerHandler
from src.portfolio.domain.aggregates import Portfolio
from src.portfolio.domain.entities import Position
from src.portfolio.infrastructure import (
    InMemoryPortfolioRepository,
    InMemoryPositionRepository,
)
from src.shared.domain import Err, Ok


class TestHandlerOpenPositionFlow:
    """Full open_position flow: Kelly -> sector check -> ATR stop -> take-profit."""

    def _make_handler(
        self,
        portfolio: Portfolio | None = None,
        initial_value: float = 100_000.0,
    ) -> PortfolioManagerHandler:
        port_repo = InMemoryPortfolioRepository()
        pos_repo = InMemoryPositionRepository()
        if portfolio is not None:
            port_repo.save(portfolio)
        return PortfolioManagerHandler(port_repo, pos_repo, initial_value)

    def test_full_flow_with_take_profit(self) -> None:
        """Kelly sizing -> position created -> take_profit_levels in result."""
        handler = self._make_handler()
        cmd = OpenPositionCommand(
            symbol="AAPL",
            entry_price=100.0,
            portfolio_id="p1",
            sector="Technology",
            win_rate=0.50,
            win_loss_ratio=2.0,  # Kelly=0.50-0.50/2.0=0.25, frac=0.0625 < 8%
            atr=2.0,
            atr_multiplier=2.5,
            intrinsic_value=150.0,
        )
        result = handler.open_position(cmd)
        assert isinstance(result, Ok)
        data = result.value
        assert data["symbol"] == "AAPL"
        assert data["shares"] > 0
        assert data["stop_price"] is not None
        # Take-profit levels present
        assert "take_profit_levels" in data
        levels = data["take_profit_levels"]
        assert len(levels) == 3
        assert levels[0]["price"] == 125.0
        assert levels[1]["price"] == 137.5
        assert levels[2]["price"] == 150.0

    def test_no_take_profit_when_intrinsic_none(self) -> None:
        """take_profit_levels absent when intrinsic_value is None."""
        handler = self._make_handler()
        cmd = OpenPositionCommand(
            symbol="AAPL",
            entry_price=100.0,
            portfolio_id="p1",
            win_rate=0.50,
            win_loss_ratio=2.0,
            intrinsic_value=None,
        )
        result = handler.open_position(cmd)
        assert isinstance(result, Ok)
        assert "take_profit_levels" not in result.value

    def test_sector_limit_blocks_position(self) -> None:
        """Sector='Technology' at 24% blocks new 2% Technology position."""
        # Pre-populate portfolio with 24% Technology
        positions = {}
        for sym in ["AAPL", "MSFT", "GOOG", "META"]:
            positions[sym] = Position(
                symbol=sym, entry_price=100.0, quantity=60, sector="Technology"
            )
        # Fill rest with non-tech to reach 100k
        positions["JNJ"] = Position(
            symbol="JNJ", entry_price=100.0, quantity=760, sector="Healthcare"
        )
        portfolio = Portfolio(
            portfolio_id="p1",
            initial_value=100_000.0,
            positions=positions,
            peak_value=100_000.0,
        )
        handler = self._make_handler(portfolio=portfolio)

        cmd = OpenPositionCommand(
            symbol="NVDA",
            entry_price=100.0,
            portfolio_id="p1",
            sector="Technology",
            win_rate=0.55,
            win_loss_ratio=2.0,
        )
        result = handler.open_position(cmd)
        assert isinstance(result, Err)

    def test_kelly_zero_shares_returns_err(self) -> None:
        """Kelly produces 0 shares when win_loss_ratio <= 0 -> Err."""
        handler = self._make_handler()
        cmd = OpenPositionCommand(
            symbol="AAPL",
            entry_price=100.0,
            portfolio_id="p1",
            win_rate=0.55,
            win_loss_ratio=0.0,  # -> kelly = 0
        )
        result = handler.open_position(cmd)
        assert isinstance(result, Err)

    def test_atr_stop_in_result(self) -> None:
        """ATR stop is included in result when atr provided."""
        handler = self._make_handler()
        cmd = OpenPositionCommand(
            symbol="AAPL",
            entry_price=100.0,
            portfolio_id="p1",
            win_rate=0.50,
            win_loss_ratio=2.0,
            atr=3.0,
            atr_multiplier=2.5,
        )
        result = handler.open_position(cmd)
        assert isinstance(result, Ok)
        # stop_price = 100 - (3.0 * 2.5) = 92.5
        assert result.value["stop_price"] == 92.5

    def test_kelly_sizing_fractional_kelly(self) -> None:
        """Kelly sizing uses 1/4 fractional Kelly."""
        handler = self._make_handler(initial_value=100_000.0)
        cmd = OpenPositionCommand(
            symbol="AAPL",
            entry_price=100.0,
            portfolio_id="p1",
            win_rate=0.50,
            win_loss_ratio=2.0,
        )
        result = handler.open_position(cmd)
        assert isinstance(result, Ok)
        # Full Kelly = 0.50 - 0.50/2.0 = 0.25
        # Fractional Kelly = 0.25 * 0.25 = 0.0625
        # shares = int(100000*0.0625/100) = 62
        assert result.value["shares"] == 62
        assert result.value["kelly"] == 0.0625
