"""Tests for Portfolio sector enforcement, drawdown defense, and CoreRiskAdapter (RISK-04, RISK-05)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.portfolio.domain.aggregates import Portfolio
from src.portfolio.domain.entities import Position
from src.portfolio.domain.services import PortfolioRiskService
from src.portfolio.infrastructure.core_risk_adapter import CoreRiskAdapter


class TestPortfolioSectorWeight:
    """Portfolio aggregate sector_weight() tests."""

    def _make_portfolio(self, positions: dict[str, Position]) -> Portfolio:
        """Helper to create portfolio with positions."""
        return Portfolio(
            portfolio_id="test",
            initial_value=100_000.0,
            positions=positions,
        )

    def test_sector_weight_single_position(self) -> None:
        """Single Technology position weight is correct."""
        positions = {
            "AAPL": Position(
                symbol="AAPL", entry_price=100.0, quantity=50, sector="Technology"
            ),
        }
        portfolio = self._make_portfolio(positions)
        # market_value = 5000, total = 5000
        assert portfolio.sector_weight("Technology") == pytest.approx(1.0)

    def test_sector_weight_multiple_sectors(self) -> None:
        """Technology weight sums only Technology positions."""
        positions = {
            "AAPL": Position(
                symbol="AAPL", entry_price=100.0, quantity=50, sector="Technology"
            ),
            "MSFT": Position(
                symbol="MSFT", entry_price=200.0, quantity=25, sector="Technology"
            ),
            "JNJ": Position(
                symbol="JNJ", entry_price=150.0, quantity=20, sector="Healthcare"
            ),
        }
        portfolio = self._make_portfolio(positions)
        # Tech = 5000 + 5000 = 10000
        # HC = 3000
        # Total = 13000
        assert portfolio.sector_weight("Technology") == pytest.approx(10000 / 13000)

    def test_sector_weight_empty_portfolio(self) -> None:
        """Empty portfolio returns 0 for any sector."""
        portfolio = self._make_portfolio({})
        assert portfolio.sector_weight("Technology") == pytest.approx(0.0)

    def test_sector_weight_nonexistent_sector(self) -> None:
        """Sector with no positions returns 0."""
        positions = {
            "AAPL": Position(
                symbol="AAPL", entry_price=100.0, quantity=50, sector="Technology"
            ),
        }
        portfolio = self._make_portfolio(positions)
        assert portfolio.sector_weight("Healthcare") == pytest.approx(0.0)


class TestPortfolioCanOpenWithSector:
    """Portfolio.can_open_position() with sector limit enforcement."""

    def test_rejects_when_sector_exceeds_25pct(self) -> None:
        """Rejects new position when sector weight would exceed 25%."""
        # 4 tech positions each at 6000 = 24k tech
        positions = {}
        for sym in ["AAPL", "MSFT", "GOOG", "META"]:
            positions[sym] = Position(
                symbol=sym, entry_price=100.0, quantity=60, sector="Technology"
            )
        # Add non-tech to bring total to 100k (need 76k other)
        positions["JNJ"] = Position(
            symbol="JNJ", entry_price=100.0, quantity=760, sector="Healthcare"
        )
        portfolio = Portfolio(
            portfolio_id="test",
            initial_value=100_000.0,
            positions=positions,
            peak_value=100_000.0,
        )
        # Tech = 24000/100000 = 24%, new 2% would be 26% > 25%
        assert portfolio.can_open_position("NVDA", 0.02, sector="Technology") is False

    def test_allows_when_sector_under_25pct(self) -> None:
        """Allows position when sector weight would stay under 25%."""
        positions = {
            "AAPL": Position(
                symbol="AAPL", entry_price=100.0, quantity=100, sector="Technology"
            ),
            "JNJ": Position(
                symbol="JNJ", entry_price=100.0, quantity=900, sector="Healthcare"
            ),
        }
        portfolio = Portfolio(
            portfolio_id="test",
            initial_value=100_000.0,
            positions=positions,
            peak_value=100_000.0,
        )
        # Tech = 10000/100000 = 10%, new 5% = 15% < 25%. Total=100k, no drawdown.
        assert portfolio.can_open_position("MSFT", 0.05, sector="Technology") is True

    def test_allows_different_sector(self) -> None:
        """Position in a different sector is allowed even if one sector is at 24%."""
        positions = {}
        for sym in ["AAPL", "MSFT", "GOOG", "META"]:
            positions[sym] = Position(
                symbol=sym, entry_price=100.0, quantity=60, sector="Technology"
            )
        # Add non-tech to bring total near 100k (4*6000 = 24k tech, need 76k other)
        positions["JNJ"] = Position(
            symbol="JNJ", entry_price=100.0, quantity=760, sector="Healthcare"
        )
        portfolio = Portfolio(
            portfolio_id="test",
            initial_value=100_000.0,
            positions=positions,
            peak_value=100_000.0,
        )
        # Healthcare at 76%, adding 5% to Utilities (a new sector) is fine
        assert portfolio.can_open_position("NEE", 0.05, sector="Utilities") is True

    def test_rejects_single_position_over_8pct(self) -> None:
        """Single position weight > 8% is still rejected (regardless of sector)."""
        # Need positions so drawdown is NORMAL
        positions = {
            "SPY": Position(
                symbol="SPY", entry_price=100.0, quantity=1000, sector="ETF"
            ),
        }
        portfolio = Portfolio(
            portfolio_id="test",
            initial_value=100_000.0,
            positions=positions,
            peak_value=100_000.0,
        )
        assert portfolio.can_open_position("AAPL", 0.10, sector="Technology") is False


class TestDrawdownDefenseTiers:
    """Drawdown defense at 10%/15%/20% tiers via domain service."""

    def setup_method(self) -> None:
        self.svc = PortfolioRiskService()

    def test_drawdown_10pct_caution(self) -> None:
        """10% drawdown returns CAUTION with can_open=False."""
        result = self.svc.assess_drawdown_defense(0.10)
        assert result["level"] == "caution"
        assert result["can_open"] is False
        assert result["reduce_pct"] == 0

    def test_drawdown_15pct_warning(self) -> None:
        """15% drawdown returns WARNING with reduce_pct=50."""
        result = self.svc.assess_drawdown_defense(0.15)
        assert result["level"] == "warning"
        assert result["can_open"] is False
        assert result["reduce_pct"] == 50

    def test_drawdown_20pct_critical(self) -> None:
        """20% drawdown returns CRITICAL with reduce_pct=100."""
        result = self.svc.assess_drawdown_defense(0.20)
        assert result["level"] == "critical"
        assert result["can_open"] is False
        assert result["reduce_pct"] == 100


class TestCoreRiskAdapter:
    """CoreRiskAdapter delegation to personal/ functions."""

    def setup_method(self) -> None:
        self.adapter = CoreRiskAdapter()

    @patch("src.portfolio.infrastructure.core_risk_adapter.kelly_fraction")
    def test_compute_kelly_delegates(self, mock_kelly: object) -> None:
        """compute_kelly() delegates to personal/sizer/kelly.kelly_fraction()."""
        mock_kelly.return_value = 0.05  # type: ignore[union-attr]
        result = self.adapter.compute_kelly(
            win_rate=0.55, avg_win=2.0, avg_loss=1.0
        )
        mock_kelly.assert_called_once_with(0.55, 2.0, 1.0)  # type: ignore[union-attr]
        assert result == 0.05

    @patch("src.portfolio.infrastructure.core_risk_adapter.atr_position_size")
    def test_compute_atr_stop_delegates(self, mock_atr: object) -> None:
        """compute_atr_stop() delegates to personal/sizer/kelly.atr_position_size()."""
        mock_atr.return_value = {"shares": 10, "stop_price": 95.0}  # type: ignore[union-attr]
        result = self.adapter.compute_atr_stop(
            capital=100_000.0, entry_price=100.0, atr=2.0, atr_multiplier=3.0
        )
        mock_atr.assert_called_once_with(100_000.0, 100.0, 2.0, 3.0)  # type: ignore[union-attr]
        assert result == {"shares": 10, "stop_price": 95.0}

    @patch("src.portfolio.infrastructure.core_risk_adapter.validate_position")
    def test_validate_position_delegates(self, mock_val: object) -> None:
        """validate_position() delegates to personal/sizer/kelly.validate_position()."""
        mock_val.return_value = {"passed": True, "violations": []}  # type: ignore[union-attr]
        result = self.adapter.validate_position(
            position_value=5000.0, capital=100_000.0, sector_exposure=0.10
        )
        mock_val.assert_called_once_with(5000.0, 100_000.0, 0.10)  # type: ignore[union-attr]
        assert result == {"passed": True, "violations": []}

    @patch("src.portfolio.infrastructure.core_risk_adapter.assess_drawdown")
    def test_assess_drawdown_delegates(self, mock_dd: object) -> None:
        """assess_drawdown() delegates to personal/risk/drawdown.assess_drawdown()."""
        mock_dd.return_value = {"level": 1, "action": "halt"}  # type: ignore[union-attr]
        result = self.adapter.assess_drawdown(
            peak_value=100_000.0, current_value=90_000.0
        )
        mock_dd.assert_called_once_with(100_000.0, 90_000.0, 0)  # type: ignore[union-attr]
        assert result == {"level": 1, "action": "halt"}
