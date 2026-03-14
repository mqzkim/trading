"""Unit tests for PriceAdapter and dashboard position current_price/target_price.

Verifies:
1. PriceAdapter.get_latest_price returns positive float from DataClient
2. PriceAdapter.get_latest_price returns None on failure
3. Dashboard _get_positions uses PriceAdapter for current_price with fallback
4. Dashboard _get_positions reads take_profit_price as target_price
5. P&L calculated correctly with real current_price
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from unittest.mock import MagicMock

import pytest

from src.dashboard.infrastructure.price_adapter import PriceAdapter


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeATRStop:
    stop_price: float = 150.0


@dataclass
class _FakePosition:
    id: str = "pos-1"
    symbol: str = "AAPL"
    entry_price: float = 150.0
    quantity: int = 10
    entry_date: date = field(default_factory=date.today)
    strategy: str = "swing"
    atr_stop: Optional[_FakeATRStop] = None
    sector: str = "Technology"
    status: str = "OPEN"


class _FakePositionRepo:
    def __init__(self, positions: list):
        self._positions = positions

    def find_all_open(self):
        return self._positions


class _FakeScoreVO:
    def __init__(self, value: float, risk_adjusted: float = 0.0, strategy: str = "swing"):
        self.value = value
        self.risk_adjusted = risk_adjusted
        self.strategy = strategy


class _FakeScoreRepo:
    def __init__(self, scores: dict):
        self._scores = scores

    def find_all_latest(self):
        return self._scores


class _FakeTradePlanRepo:
    def __init__(self, plans: dict):
        self._plans = plans

    def find_by_symbol(self, symbol: str):
        return self._plans.get(symbol)


# ---------------------------------------------------------------------------
# Test PriceAdapter
# ---------------------------------------------------------------------------

class TestPriceAdapter:
    def test_get_latest_price_returns_close(self):
        """PriceAdapter returns close price from DataClient.get_full()."""
        mock_client = MagicMock()
        mock_client.get_full.return_value = {
            "price": {"open": 174.0, "high": 176.0, "low": 173.5, "close": 175.50, "volume": 1000000}
        }
        adapter = PriceAdapter(data_client=mock_client)

        result = adapter.get_latest_price("AAPL")

        assert result == 175.50
        mock_client.get_full.assert_called_once_with("AAPL", days=5)

    def test_get_latest_price_returns_none_on_exception(self):
        """PriceAdapter returns None when DataClient raises an exception."""
        mock_client = MagicMock()
        mock_client.get_full.side_effect = ConnectionError("API timeout")
        adapter = PriceAdapter(data_client=mock_client)

        result = adapter.get_latest_price("INVALID")

        assert result is None

    def test_get_latest_price_returns_none_without_client(self):
        """PriceAdapter returns None when no DataClient is provided."""
        adapter = PriceAdapter(data_client=None)

        result = adapter.get_latest_price("AAPL")

        assert result is None

    def test_get_latest_prices_batch(self):
        """PriceAdapter.get_latest_prices returns dict of symbol->price."""
        mock_client = MagicMock()
        mock_client.get_full.side_effect = [
            {"price": {"close": 175.50}},
            ConnectionError("fail"),
            {"price": {"close": 420.00}},
        ]
        adapter = PriceAdapter(data_client=mock_client)

        result = adapter.get_latest_prices(["AAPL", "BAD", "MSFT"])

        assert result == {"AAPL": 175.50, "MSFT": 420.00}
        assert "BAD" not in result


# ---------------------------------------------------------------------------
# Test Dashboard positions with real current_price and target_price
# ---------------------------------------------------------------------------

class TestDashboardPositions:
    def _make_handler(self, positions, scores=None, price_adapter=None, trade_plan_repo=None):
        """Create OverviewQueryHandler with injected context."""
        from src.dashboard.application.queries import OverviewQueryHandler

        ctx = {
            "position_repo": _FakePositionRepo(positions),
            "score_repo": _FakeScoreRepo(scores or {}),
        }
        if price_adapter is not None:
            ctx["price_adapter"] = price_adapter
        if trade_plan_repo is not None:
            ctx["trade_plan_repo"] = trade_plan_repo
        return OverviewQueryHandler(ctx)

    def test_current_price_from_price_adapter(self):
        """Dashboard uses PriceAdapter for current_price when available."""
        mock_client = MagicMock()
        mock_client.get_full.return_value = {"price": {"close": 180.00}}
        price_adapter = PriceAdapter(data_client=mock_client)

        pos = _FakePosition(symbol="AAPL", entry_price=150.0, quantity=10)
        handler = self._make_handler([pos], price_adapter=price_adapter)

        positions = handler._get_positions()

        assert len(positions) == 1
        assert positions[0]["current_price"] == 180.00

    def test_current_price_fallback_to_entry_price(self):
        """Dashboard falls back to entry_price when PriceAdapter returns None."""
        mock_client = MagicMock()
        mock_client.get_full.side_effect = ConnectionError("network error")
        price_adapter = PriceAdapter(data_client=mock_client)

        pos = _FakePosition(symbol="AAPL", entry_price=150.0, quantity=10)
        handler = self._make_handler([pos], price_adapter=price_adapter)

        positions = handler._get_positions()

        assert len(positions) == 1
        assert positions[0]["current_price"] == 150.0  # fallback to entry_price

    def test_target_price_from_trade_plan(self):
        """Dashboard reads take_profit_price from trade_plan_repo as target_price."""
        trade_plan_repo = _FakeTradePlanRepo({
            "AAPL": {"take_profit_price": 200.0, "entry_price": 150.0, "composite_score": 75.0},
        })
        pos = _FakePosition(symbol="AAPL", entry_price=150.0, quantity=10)
        handler = self._make_handler([pos], trade_plan_repo=trade_plan_repo)

        positions = handler._get_positions()

        assert len(positions) == 1
        assert positions[0]["target_price"] == 200.0

    def test_target_price_zero_when_no_plan(self):
        """Dashboard target_price is 0.0 when no trade plan exists for symbol."""
        trade_plan_repo = _FakeTradePlanRepo({})
        pos = _FakePosition(symbol="AAPL", entry_price=150.0, quantity=10)
        handler = self._make_handler([pos], trade_plan_repo=trade_plan_repo)

        positions = handler._get_positions()

        assert len(positions) == 1
        assert positions[0]["target_price"] == 0.0

    def test_pnl_calculated_correctly(self):
        """P&L computed using real current_price vs entry_price."""
        mock_client = MagicMock()
        mock_client.get_full.return_value = {"price": {"close": 180.00}}
        price_adapter = PriceAdapter(data_client=mock_client)

        pos = _FakePosition(symbol="AAPL", entry_price=150.0, quantity=10)
        handler = self._make_handler([pos], price_adapter=price_adapter)

        positions = handler._get_positions()

        assert len(positions) == 1
        p = positions[0]
        # pnl_pct = (180 - 150) / 150 = 0.2
        assert abs(p["pnl_pct"] - 0.2) < 1e-6
        # pnl_dollar = (180 - 150) * 10 = 300
        assert abs(p["pnl_dollar"] - 300.0) < 1e-6
        # market_value = 180 * 10 = 1800
        assert abs(p["market_value"] - 1800.0) < 1e-6
