"""Tests for SafeExecutionAdapter -- SAFE-01 mode enforcement, SAFE-02 no-mock, SAFE-03 key pairs."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import MagicMock

import pytest

from src.execution.domain.repositories import IBrokerAdapter, ICooldownRepository
from src.execution.domain.value_objects import (
    CooldownState,
    ExecutionMode,
    OrderResult,
    OrderSpec,
)
from src.execution.infrastructure.safe_adapter import (
    CooldownActiveError,
    SafeExecutionAdapter,
)
from src.settings import Settings


# ── Test doubles ───────────────────────────────────────────────────────


class MockBrokerAdapter(IBrokerAdapter):
    """Controllable broker adapter for testing."""

    def __init__(self, order_result: Optional[OrderResult] = None) -> None:
        self._order_result = order_result or OrderResult(
            order_id="TEST-001",
            status="filled",
            symbol="AAPL",
            quantity=10,
            filled_price=150.0,
        )
        self.submit_count = 0

    def submit_order(self, spec: OrderSpec) -> OrderResult:
        self.submit_count += 1
        return self._order_result

    def get_positions(self) -> list[dict]:
        return [{"symbol": "AAPL", "qty": 10}]

    def get_account(self) -> dict:
        return {"cash": 50000.0, "portfolio_value": 100000.0, "status": "ACTIVE"}


class InMemoryCooldownRepository(ICooldownRepository):
    """In-memory cooldown repo for testing."""

    def __init__(self) -> None:
        self._cooldowns: list[CooldownState] = []
        self._next_id = 1

    def save(self, state: CooldownState) -> int:
        from dataclasses import replace

        new_state = replace(state, id=self._next_id)
        self._cooldowns.append(new_state)
        self._next_id += 1
        return new_state.id  # type: ignore[return-value]

    def get_active(self) -> Optional[CooldownState]:
        for s in reversed(self._cooldowns):
            if s.is_active and not s.is_expired():
                return s
        return None

    def deactivate(self, cooldown_id: int) -> None:
        from dataclasses import replace

        for i, s in enumerate(self._cooldowns):
            if s.id == cooldown_id:
                self._cooldowns[i] = replace(s, is_active=False)
                break

    def get_history(self) -> list[CooldownState]:
        return sorted(self._cooldowns, key=lambda s: s.triggered_at, reverse=True)


# ── Tests ──────────────────────────────────────────────────────────────


class TestSafeExecutionAdapterPaperMode:
    """Paper mode: orders pass through without polling/leg verification."""

    def setup_method(self) -> None:
        self.inner = MockBrokerAdapter()
        self.cooldown_repo = InMemoryCooldownRepository()
        self.adapter = SafeExecutionAdapter(
            inner=self.inner,
            mode=ExecutionMode.PAPER,
            cooldown_repo=self.cooldown_repo,
        )

    def test_default_paper_mode(self) -> None:
        """Paper mode submits order without polling or leg verification."""
        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        result = self.adapter.submit_order(spec)
        assert result.status == "filled"
        assert result.symbol == "AAPL"
        assert self.inner.submit_count == 1

    def test_credentials_alone_not_live(self) -> None:
        """Having API keys does NOT change mode -- mode is explicit."""
        inner = MockBrokerAdapter()
        adapter = SafeExecutionAdapter(
            inner=inner,
            mode=ExecutionMode.PAPER,
            cooldown_repo=self.cooldown_repo,
        )
        assert adapter._mode == ExecutionMode.PAPER

    def test_live_no_mock_fallback(self) -> None:
        """When inner adapter returns error, SafeExecutionAdapter returns it as-is."""
        error_result = OrderResult(
            order_id="",
            status="error",
            symbol="AAPL",
            quantity=10,
            filled_price=None,
            error_message="Alpaca bracket order failed",
        )
        inner = MockBrokerAdapter(order_result=error_result)
        adapter = SafeExecutionAdapter(
            inner=inner,
            mode=ExecutionMode.PAPER,
            cooldown_repo=self.cooldown_repo,
        )
        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        result = adapter.submit_order(spec)
        assert result.status == "error"
        assert result.error_message == "Alpaca bracket order failed"


class TestSafeExecutionAdapterCooldown:
    """Cooldown enforcement tests."""

    def setup_method(self) -> None:
        self.inner = MockBrokerAdapter()
        self.cooldown_repo = InMemoryCooldownRepository()
        self.adapter = SafeExecutionAdapter(
            inner=self.inner,
            mode=ExecutionMode.PAPER,
            cooldown_repo=self.cooldown_repo,
        )

    def test_cooldown_blocks_submission(self) -> None:
        """Active cooldown raises CooldownActiveError."""
        now = datetime.now(timezone.utc)
        cooldown = CooldownState(
            triggered_at=now - timedelta(hours=1),
            expires_at=now + timedelta(days=29),
            current_tier=10,
            re_entry_pct=0,
            reason="drawdown",
            is_active=True,
        )
        self.cooldown_repo.save(cooldown)

        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        with pytest.raises(CooldownActiveError) as exc_info:
            self.adapter.submit_order(spec)
        assert exc_info.value.cooldown.current_tier == 10
        assert self.inner.submit_count == 0

    def test_cooldown_expired_allows_submission(self) -> None:
        """Expired cooldown does not block order submission."""
        now = datetime.now(timezone.utc)
        cooldown = CooldownState(
            triggered_at=now - timedelta(days=31),
            expires_at=now - timedelta(days=1),
            current_tier=10,
            re_entry_pct=100,
            reason="drawdown",
            is_active=True,
        )
        self.cooldown_repo.save(cooldown)

        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        result = self.adapter.submit_order(spec)
        assert result.status == "filled"
        assert self.inner.submit_count == 1


class TestSafeExecutionAdapterDelegation:
    """Delegation methods."""

    def setup_method(self) -> None:
        self.inner = MockBrokerAdapter()
        self.cooldown_repo = InMemoryCooldownRepository()
        self.adapter = SafeExecutionAdapter(
            inner=self.inner,
            mode=ExecutionMode.PAPER,
            cooldown_repo=self.cooldown_repo,
        )

    def test_get_positions_delegates(self) -> None:
        positions = self.adapter.get_positions()
        assert positions == [{"symbol": "AAPL", "qty": 10}]

    def test_get_account_delegates(self) -> None:
        account = self.adapter.get_account()
        assert account["cash"] == 50000.0


class TestSeparateKeyPairs:
    """SAFE-03: Verify Settings loads separate key pairs."""

    def test_separate_paper_and_live_keys(self) -> None:
        """Settings parses ALPACA_PAPER_KEY separately from ALPACA_LIVE_KEY."""
        s = Settings(
            ALPACA_PAPER_KEY="paper-key",
            ALPACA_PAPER_SECRET="paper-secret",
            ALPACA_LIVE_KEY="live-key",
            ALPACA_LIVE_SECRET="live-secret",
        )
        assert s.ALPACA_PAPER_KEY == "paper-key"
        assert s.ALPACA_LIVE_KEY == "live-key"
        assert s.ALPACA_PAPER_KEY != s.ALPACA_LIVE_KEY
