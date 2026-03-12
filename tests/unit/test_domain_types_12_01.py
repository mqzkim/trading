"""Tests for Phase 12-01 Task 1: Domain types, settings, and repository interface.

Covers: ExecutionMode enum, CooldownState VO, ICooldownRepository ABC, Settings extension.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


class TestExecutionMode:
    """ExecutionMode enum tests."""

    def test_paper_value(self) -> None:
        from src.execution.domain.value_objects import ExecutionMode

        assert ExecutionMode.PAPER.value == "paper"

    def test_live_value(self) -> None:
        from src.execution.domain.value_objects import ExecutionMode

        assert ExecutionMode.LIVE.value == "live"

    def test_exactly_two_members(self) -> None:
        from src.execution.domain.value_objects import ExecutionMode

        assert len(ExecutionMode) == 2


class TestCooldownState:
    """CooldownState value object tests."""

    def test_create_cooldown_state(self) -> None:
        from src.execution.domain.value_objects import CooldownState

        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=30)
        state = CooldownState(
            triggered_at=now,
            expires_at=expires,
            current_tier=20,
        )
        assert state.triggered_at == now
        assert state.expires_at == expires
        assert state.current_tier == 20
        assert state.re_entry_pct == 0
        assert state.reason == "drawdown"
        assert state.is_active is True
        assert state.force_overridden is False
        assert state.id is None

    def test_is_expired_returns_true_when_past(self) -> None:
        from src.execution.domain.value_objects import CooldownState

        past = datetime.now(timezone.utc) - timedelta(days=31)
        expired_at = past + timedelta(days=30)
        state = CooldownState(
            triggered_at=past,
            expires_at=expired_at,
            current_tier=20,
        )
        assert state.is_expired() is True

    def test_is_expired_returns_false_when_future(self) -> None:
        from src.execution.domain.value_objects import CooldownState

        now = datetime.now(timezone.utc)
        future = now + timedelta(days=30)
        state = CooldownState(
            triggered_at=now,
            expires_at=future,
            current_tier=20,
        )
        assert state.is_expired() is False

    def test_re_entry_allowed_pct(self) -> None:
        from src.execution.domain.value_objects import CooldownState

        now = datetime.now(timezone.utc)
        state = CooldownState(
            triggered_at=now,
            expires_at=now + timedelta(days=30),
            current_tier=15,
            re_entry_pct=50,
        )
        assert state.re_entry_allowed_pct() == 50

    def test_frozen_dataclass(self) -> None:
        from src.execution.domain.value_objects import CooldownState

        now = datetime.now(timezone.utc)
        state = CooldownState(
            triggered_at=now,
            expires_at=now + timedelta(days=30),
            current_tier=20,
        )
        with pytest.raises(AttributeError):
            state.current_tier = 10  # type: ignore[misc]

    def test_kill_switch_reason(self) -> None:
        from src.execution.domain.value_objects import CooldownState

        now = datetime.now(timezone.utc)
        state = CooldownState(
            triggered_at=now,
            expires_at=now + timedelta(days=30),
            current_tier=20,
            reason="kill_switch",
        )
        assert state.reason == "kill_switch"


class TestICooldownRepository:
    """ICooldownRepository ABC interface tests."""

    def test_is_abstract(self) -> None:
        from src.execution.domain.repositories import ICooldownRepository

        with pytest.raises(TypeError):
            ICooldownRepository()  # type: ignore[abstract]

    def test_has_save_method(self) -> None:
        from src.execution.domain.repositories import ICooldownRepository

        assert hasattr(ICooldownRepository, "save")

    def test_has_get_active_method(self) -> None:
        from src.execution.domain.repositories import ICooldownRepository

        assert hasattr(ICooldownRepository, "get_active")

    def test_has_deactivate_method(self) -> None:
        from src.execution.domain.repositories import ICooldownRepository

        assert hasattr(ICooldownRepository, "deactivate")

    def test_has_get_history_method(self) -> None:
        from src.execution.domain.repositories import ICooldownRepository

        assert hasattr(ICooldownRepository, "get_history")


class TestSettingsExtension:
    """Settings extension for EXECUTION_MODE and separate Alpaca keys."""

    def test_execution_mode_defaults_paper(self) -> None:
        from src.settings import Settings

        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )
        assert s.EXECUTION_MODE == "paper"

    def test_has_paper_key_fields(self) -> None:
        from src.settings import Settings

        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )
        assert s.ALPACA_PAPER_KEY is None
        assert s.ALPACA_PAPER_SECRET is None

    def test_has_live_key_fields(self) -> None:
        from src.settings import Settings

        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )
        assert s.ALPACA_LIVE_KEY is None
        assert s.ALPACA_LIVE_SECRET is None

    def test_backward_compat_keys_still_exist(self) -> None:
        from src.settings import Settings

        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )
        assert s.ALPACA_API_KEY is None
        assert s.ALPACA_SECRET_KEY is None


class TestDomainEvents:
    """Domain event tests for CooldownTriggeredEvent and KillSwitchActivatedEvent."""

    def test_cooldown_triggered_event(self) -> None:
        from src.execution.domain.events import CooldownTriggeredEvent

        event = CooldownTriggeredEvent(
            tier=20,
            reason="drawdown",
            expires_at="2026-04-12T00:00:00Z",
        )
        assert event.tier == 20
        assert event.reason == "drawdown"
        assert event.expires_at == "2026-04-12T00:00:00Z"

    def test_kill_switch_activated_event(self) -> None:
        from src.execution.domain.events import KillSwitchActivatedEvent

        event = KillSwitchActivatedEvent(
            liquidate=True,
            reason="manual kill",
        )
        assert event.liquidate is True
        assert event.reason == "manual kill"
