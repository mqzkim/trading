"""Tests for SafeExecutionAdapter order polling (SAFE-07) and bracket leg verification (SAFE-08)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from src.execution.domain.repositories import IBrokerAdapter, ICooldownRepository
from src.execution.domain.value_objects import (
    CooldownState,
    ExecutionMode,
    OrderResult,
    OrderSpec,
)
from src.execution.infrastructure.safe_adapter import (
    OrderTimeoutError,
    SafeExecutionAdapter,
)


# ── Test doubles ───────────────────────────────────────────────────────


class MockBrokerAdapter(IBrokerAdapter):
    """Controllable broker adapter for polling tests."""

    def __init__(self, order_result: Optional[OrderResult] = None) -> None:
        self._order_result = order_result or OrderResult(
            order_id="ORDER-001",
            status="filled",
            symbol="AAPL",
            quantity=10,
            filled_price=150.0,
        )
        self._client = MagicMock()

    def submit_order(self, spec: OrderSpec) -> OrderResult:
        return self._order_result

    def get_positions(self) -> list[dict]:
        return []

    def get_account(self) -> dict:
        return {"cash": 100000.0, "portfolio_value": 100000.0, "status": "ACTIVE"}


class InMemoryCooldownRepository(ICooldownRepository):
    """No-op cooldown repo for polling tests."""

    def save(self, state: CooldownState) -> int:
        return 1

    def get_active(self) -> Optional[CooldownState]:
        return None

    def deactivate(self, cooldown_id: int) -> None:
        pass

    def get_history(self) -> list[CooldownState]:
        return []


# ── Polling tests (SAFE-07) ───────────────────────────────────────────


class TestOrderPolling:
    """Order polling until terminal state."""

    def setup_method(self) -> None:
        self.inner = MockBrokerAdapter()
        self.cooldown_repo = InMemoryCooldownRepository()

    def test_poll_until_filled(self) -> None:
        """Order transitions new -> filled, poll returns final result."""
        adapter = SafeExecutionAdapter(
            inner=self.inner,
            mode=ExecutionMode.LIVE,
            cooldown_repo=self.cooldown_repo,
            poll_interval=0.01,
            poll_timeout=2.0,
        )

        # Mock _client.get_order_by_id to return status sequence: new -> filled
        mock_order_new = MagicMock()
        mock_order_new.status.value = "new"

        mock_order_filled = MagicMock()
        mock_order_filled.status.value = "filled"
        mock_order_filled.filled_avg_price = 150.5
        mock_order_filled.order_class = None

        self.inner._client.get_order_by_id.side_effect = [
            mock_order_new,
            mock_order_filled,
        ]

        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        result = adapter.submit_order(spec)
        assert result.status == "filled"
        assert result.filled_price == 150.5

    def test_poll_timeout(self) -> None:
        """Order stays 'new' past timeout, raises OrderTimeoutError."""
        adapter = SafeExecutionAdapter(
            inner=self.inner,
            mode=ExecutionMode.LIVE,
            cooldown_repo=self.cooldown_repo,
            poll_interval=0.01,
            poll_timeout=0.05,
        )

        mock_order_new = MagicMock()
        mock_order_new.status.value = "new"
        self.inner._client.get_order_by_id.return_value = mock_order_new

        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        with pytest.raises(OrderTimeoutError) as exc_info:
            adapter.submit_order(spec)
        assert exc_info.value.order_id == "ORDER-001"
        assert exc_info.value.timeout == 0.05


# ── Bracket leg verification tests (SAFE-08) ──────────────────────────


class TestBracketLegVerification:
    """Bracket leg verification after fill."""

    def setup_method(self) -> None:
        self.inner = MockBrokerAdapter()
        self.cooldown_repo = InMemoryCooldownRepository()

    def test_bracket_legs_verified(self) -> None:
        """Order with 2 active legs passes verification silently."""
        adapter = SafeExecutionAdapter(
            inner=self.inner,
            mode=ExecutionMode.LIVE,
            cooldown_repo=self.cooldown_repo,
            poll_interval=0.01,
            poll_timeout=2.0,
        )

        # Filled order with bracket legs
        mock_order = MagicMock()
        mock_order.status.value = "filled"
        mock_order.filled_avg_price = 150.5

        # Make order_class look like BRACKET
        mock_order.order_class = "bracket"

        leg1 = MagicMock()
        leg1.status.value = "new"
        leg2 = MagicMock()
        leg2.status.value = "held"
        mock_order.legs = [leg1, leg2]

        self.inner._client.get_order_by_id.return_value = mock_order

        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        result = adapter.submit_order(spec)
        assert result.status == "filled"

    def test_bracket_legs_missing(self, caplog: pytest.LogCaptureFixture) -> None:
        """Order with 0 legs logs warning."""
        adapter = SafeExecutionAdapter(
            inner=self.inner,
            mode=ExecutionMode.LIVE,
            cooldown_repo=self.cooldown_repo,
            poll_interval=0.01,
            poll_timeout=2.0,
        )

        mock_order = MagicMock()
        mock_order.status.value = "filled"
        mock_order.filled_avg_price = 150.5
        mock_order.order_class = "bracket"
        mock_order.legs = []

        self.inner._client.get_order_by_id.return_value = mock_order

        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        with caplog.at_level(logging.WARNING):
            result = adapter.submit_order(spec)
        assert result.status == "filled"
        assert any("bracket legs" in msg.lower() or "leg" in msg.lower() for msg in caplog.messages)

    def test_non_bracket_skips_verification(self) -> None:
        """Non-bracket order skips leg check entirely."""
        adapter = SafeExecutionAdapter(
            inner=self.inner,
            mode=ExecutionMode.LIVE,
            cooldown_repo=self.cooldown_repo,
            poll_interval=0.01,
            poll_timeout=2.0,
        )

        mock_order = MagicMock()
        mock_order.status.value = "filled"
        mock_order.filled_avg_price = 150.5
        mock_order.order_class = None
        mock_order.legs = None

        self.inner._client.get_order_by_id.return_value = mock_order

        spec = OrderSpec(
            symbol="AAPL",
            quantity=10,
            entry_price=150.0,
            stop_loss_price=140.0,
            take_profit_price=170.0,
        )
        result = adapter.submit_order(spec)
        assert result.status == "filled"
