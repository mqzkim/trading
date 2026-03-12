"""Unit tests for Alpaca adapter (mock mode) and SQLite trade plan repository."""
from __future__ import annotations

import os
import tempfile

import pytest

from src.execution.domain.value_objects import (
    BracketSpec,
    OrderResult,
    TradePlan,
    TradePlanStatus,
)
from src.execution.infrastructure.alpaca_adapter import AlpacaExecutionAdapter
from src.execution.infrastructure.sqlite_trade_plan_repo import SqliteTradePlanRepository


# ── AlpacaExecutionAdapter (mock mode) ────────────────────────────────


class TestAlpacaExecutionAdapterMock:
    def setup_method(self):
        self.adapter = AlpacaExecutionAdapter()  # No credentials -> mock mode

    def test_mock_mode_enabled(self):
        assert self.adapter._use_mock is True

    def test_submit_bracket_order_returns_order_result(self):
        spec = BracketSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        result = self.adapter.submit_bracket_order(spec)
        assert isinstance(result, OrderResult)
        assert result.symbol == "AAPL"
        assert result.quantity == 10
        assert result.status == "filled"
        assert result.filled_price == 150.0
        assert result.order_id.startswith("MOCK-AAPL-")

    def test_bracket_order_unique_ids(self):
        spec = BracketSpec(
            symbol="MSFT",
            quantity=5,
            entry_price=400.0,
            stop_loss_price=380.0,
            take_profit_price=430.0,
        )
        r1 = self.adapter.submit_bracket_order(spec)
        r2 = self.adapter.submit_bracket_order(spec)
        assert r1.order_id != r2.order_id

    def test_get_positions_returns_list(self):
        positions = self.adapter.get_positions()
        assert isinstance(positions, list)

    def test_get_account_returns_dict(self):
        account = self.adapter.get_account()
        assert isinstance(account, dict)
        assert "cash" in account
        assert "portfolio_value" in account
        assert "status" in account
        assert account["status"] == "ACTIVE"


# ── SqliteTradePlanRepository ─────────────────────────────────────────


class TestSqliteTradePlanRepository:
    def setup_method(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.repo = SqliteTradePlanRepository(db_path=self._tmp.name)

    def teardown_method(self):
        os.unlink(self._tmp.name)

    def _make_plan(self, symbol: str = "AAPL") -> TradePlan:
        return TradePlan(
            symbol=symbol,
            direction="BUY",
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
            quantity=10,
            position_value=1500.0,
            reasoning_trace="Test plan",
            composite_score=75.0,
            margin_of_safety=0.2,
            signal_direction="BUY",
        )

    def test_save_and_find_by_symbol(self):
        plan = self._make_plan("AAPL")
        self.repo.save(plan, TradePlanStatus.PENDING)
        found = self.repo.find_by_symbol("AAPL")
        assert found is not None
        assert found["symbol"] == "AAPL"
        assert found["status"] == "PENDING"
        assert found["entry_price"] == 150.0

    def test_find_by_symbol_not_found(self):
        found = self.repo.find_by_symbol("NONEXIST")
        assert found is None

    def test_find_pending(self):
        self.repo.save(self._make_plan("AAPL"), TradePlanStatus.PENDING)
        self.repo.save(self._make_plan("MSFT"), TradePlanStatus.PENDING)
        self.repo.save(self._make_plan("GOOG"), TradePlanStatus.APPROVED)
        pending = self.repo.find_pending()
        assert len(pending) == 2
        symbols = {p["symbol"] for p in pending}
        assert symbols == {"AAPL", "MSFT"}

    def test_update_status(self):
        self.repo.save(self._make_plan("AAPL"), TradePlanStatus.PENDING)
        self.repo.update_status("AAPL", TradePlanStatus.APPROVED)
        found = self.repo.find_by_symbol("AAPL")
        assert found is not None
        assert found["status"] == "APPROVED"

    def test_save_replaces_existing(self):
        self.repo.save(self._make_plan("AAPL"), TradePlanStatus.PENDING)
        new_plan = TradePlan(
            symbol="AAPL",
            direction="BUY",
            entry_price=155.0,
            stop_loss_price=145.0,
            take_profit_price=175.0,
            quantity=15,
            position_value=2325.0,
            reasoning_trace="Updated plan",
            composite_score=80.0,
            margin_of_safety=0.3,
            signal_direction="BUY",
        )
        self.repo.save(new_plan, TradePlanStatus.MODIFIED)
        found = self.repo.find_by_symbol("AAPL")
        assert found is not None
        assert found["entry_price"] == 155.0
        assert found["status"] == "MODIFIED"
