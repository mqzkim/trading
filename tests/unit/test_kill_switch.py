"""Unit tests for kill switch service logic.

Tests the kill switch functionality that cancels orders, liquidates positions,
and triggers cooldown. Covers SAFE-06.

NOTE: Tests the kill switch logic in a service function, not through typer CLI.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from src.execution.domain.value_objects import CooldownState
from src.execution.infrastructure.kill_switch import KillSwitchService
from src.execution.infrastructure.sqlite_cooldown_repo import SqliteCooldownRepository


class MockBrokerClient:
    """Mock Alpaca-like broker client with cancel/close methods."""

    def __init__(self) -> None:
        self.cancel_called = False
        self.close_all_called = False
        self.cancel_orders_count = 3  # simulate 3 orders canceled

    def cancel_orders(self) -> list:
        self.cancel_called = True
        return [{"id": f"order-{i}"} for i in range(self.cancel_orders_count)]

    def close_all_positions(self, cancel_orders: bool = True) -> list:  # noqa: ARG002
        self.close_all_called = True
        return [{"id": "pos-1"}, {"id": "pos-2"}]


class MockBrokerAdapterWithClient:
    """Mock broker adapter that has a _client attribute."""

    def __init__(self) -> None:
        self._client = MockBrokerClient()

    def submit_order(self, spec):  # noqa: ARG002
        return None

    def get_positions(self) -> list[dict]:
        return []

    def get_account(self) -> dict:
        return {}


class TestKillSwitchCancel:
    """Tests for kill switch order cancellation."""

    def test_cancel_all_orders(self, tmp_path: object) -> None:
        """Kill without --liquidate calls cancel_orders but NOT close_all_positions."""
        adapter = MockBrokerAdapterWithClient()
        cooldown_repo = SqliteCooldownRepository(
            db_path=os.path.join(str(tmp_path), "test.db")
        )
        service = KillSwitchService(adapter, cooldown_repo)

        result = service.execute(liquidate=False)

        assert adapter._client.cancel_called is True
        assert adapter._client.close_all_called is False
        assert result["orders_canceled"] == 3
        assert result["positions_closed"] == 0

    def test_liquidate(self, tmp_path: object) -> None:
        """Kill with liquidate=True calls both cancel_orders and close_all_positions."""
        adapter = MockBrokerAdapterWithClient()
        cooldown_repo = SqliteCooldownRepository(
            db_path=os.path.join(str(tmp_path), "test.db")
        )
        service = KillSwitchService(adapter, cooldown_repo)

        result = service.execute(liquidate=True)

        assert adapter._client.cancel_called is True
        assert adapter._client.close_all_called is True
        assert result["orders_canceled"] == 3
        assert result["positions_closed"] == 2


class TestKillSwitchCooldown:
    """Tests for kill switch cooldown triggering."""

    def test_kill_triggers_cooldown(self, tmp_path: object) -> None:
        """After kill, cooldown_repo.get_active() returns CooldownState with reason='kill_switch'."""
        adapter = MockBrokerAdapterWithClient()
        cooldown_repo = SqliteCooldownRepository(
            db_path=os.path.join(str(tmp_path), "test.db")
        )
        service = KillSwitchService(adapter, cooldown_repo)

        service.execute(liquidate=False)

        cooldown = cooldown_repo.get_active()
        assert cooldown is not None
        assert cooldown.reason == "kill_switch"
        assert cooldown.current_tier == 20

    def test_cooldown_30_day_expiry(self, tmp_path: object) -> None:
        """Cooldown expires_at is approximately 30 days after triggered_at."""
        adapter = MockBrokerAdapterWithClient()
        cooldown_repo = SqliteCooldownRepository(
            db_path=os.path.join(str(tmp_path), "test.db")
        )
        service = KillSwitchService(adapter, cooldown_repo)

        service.execute(liquidate=False)

        cooldown = cooldown_repo.get_active()
        assert cooldown is not None
        delta = cooldown.expires_at - cooldown.triggered_at
        # Should be approximately 30 days (allow 1 second tolerance)
        assert timedelta(days=29, hours=23) < delta < timedelta(days=30, seconds=2)


class TestKillSwitchMockMode:
    """Tests for kill switch in mock mode (no _client)."""

    def test_kill_in_mock_mode(self, tmp_path: object) -> None:
        """Kill in mock mode (no _client) logs warning and still creates cooldown."""

        class MockAdapterNoClient:
            """Adapter without a _client -- simulates mock/paper mode."""

            def submit_order(self, spec):  # noqa: ARG002
                return None

            def get_positions(self) -> list[dict]:
                return []

            def get_account(self) -> dict:
                return {}

        adapter = MockAdapterNoClient()
        cooldown_repo = SqliteCooldownRepository(
            db_path=os.path.join(str(tmp_path), "test.db")
        )
        service = KillSwitchService(adapter, cooldown_repo)

        result = service.execute(liquidate=False)

        # Should still succeed and create cooldown even without _client
        assert result["orders_canceled"] == 0
        assert result["positions_closed"] == 0
        cooldown = cooldown_repo.get_active()
        assert cooldown is not None
        assert cooldown.reason == "kill_switch"
