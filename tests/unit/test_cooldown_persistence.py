"""Tests for Phase 12-01 Task 2: SqliteCooldownRepository persistence.

Covers: save, get_active, deactivate, get_history, restart survival,
30-day expiry, force override, multiple active records.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.execution.domain.value_objects import CooldownState


@pytest.fixture
def db_path(tmp_path: object) -> str:
    """Return isolated SQLite DB path for testing."""
    return str(tmp_path / "test_cooldown.db")  # type: ignore[operator]


@pytest.fixture
def repo(db_path: str):
    """Create a fresh SqliteCooldownRepository instance."""
    from src.execution.infrastructure.sqlite_cooldown_repo import (
        SqliteCooldownRepository,
    )

    return SqliteCooldownRepository(db_path=db_path)


def _make_cooldown(
    *,
    days_ago: int = 0,
    duration_days: int = 30,
    tier: int = 20,
    reason: str = "drawdown",
    is_active: bool = True,
    force_overridden: bool = False,
) -> CooldownState:
    """Helper to create CooldownState with relative timestamps."""
    triggered = datetime.now(timezone.utc) - timedelta(days=days_ago)
    expires = triggered + timedelta(days=duration_days)
    return CooldownState(
        triggered_at=triggered,
        expires_at=expires,
        current_tier=tier,
        reason=reason,
        is_active=is_active,
        force_overridden=force_overridden,
    )


class TestSaveAndGetActive:
    """save() persists state, get_active() retrieves it."""

    def test_save_and_get_active(self, repo) -> None:
        cooldown = _make_cooldown()
        saved_id = repo.save(cooldown)
        assert saved_id > 0

        active = repo.get_active()
        assert active is not None
        assert active.current_tier == 20
        assert active.reason == "drawdown"
        assert active.is_active is True
        assert active.id == saved_id

    def test_save_returns_incrementing_ids(self, repo) -> None:
        id1 = repo.save(_make_cooldown(tier=10))
        id2 = repo.save(_make_cooldown(tier=15))
        assert id2 > id1


class TestSurvivesRestart:
    """Cooldown state survives process restart (new repo instance, same DB)."""

    def test_survives_restart(self, db_path: str) -> None:
        from src.execution.infrastructure.sqlite_cooldown_repo import (
            SqliteCooldownRepository,
        )

        repo1 = SqliteCooldownRepository(db_path=db_path)
        cooldown = _make_cooldown(tier=15, reason="kill_switch")
        repo1.save(cooldown)

        # Simulate restart: new repo instance on same DB
        repo2 = SqliteCooldownRepository(db_path=db_path)
        active = repo2.get_active()
        assert active is not None
        assert active.current_tier == 15
        assert active.reason == "kill_switch"


class TestExpiry:
    """30-day expiry calculated correctly."""

    def test_expiry_30_days(self, repo) -> None:
        """Expired cooldown should not be returned by get_active()."""
        expired = _make_cooldown(days_ago=31, duration_days=30)
        repo.save(expired)

        active = repo.get_active()
        assert active is None

    def test_not_expired_within_30_days(self, repo) -> None:
        """Active cooldown within 30 days should be returned."""
        recent = _make_cooldown(days_ago=5, duration_days=30)
        repo.save(recent)

        active = repo.get_active()
        assert active is not None


class TestDeactivate:
    """deactivate() marks cooldown as inactive."""

    def test_deactivate(self, repo) -> None:
        cooldown = _make_cooldown()
        saved_id = repo.save(cooldown)

        repo.deactivate(saved_id)

        active = repo.get_active()
        assert active is None

    def test_deactivate_only_target(self, repo) -> None:
        """Deactivating one cooldown doesn't affect others."""
        id1 = repo.save(_make_cooldown(tier=10))
        id2 = repo.save(_make_cooldown(tier=15))

        repo.deactivate(id1)

        active = repo.get_active()
        assert active is not None
        assert active.id == id2


class TestForceOverride:
    """Force override: deactivate existing + save new with force_overridden=True."""

    def test_force_override(self, repo) -> None:
        original_id = repo.save(_make_cooldown(tier=20))
        repo.deactivate(original_id)

        overridden = _make_cooldown(tier=20, force_overridden=True)
        new_id = repo.save(overridden)

        active = repo.get_active()
        assert active is not None
        assert active.force_overridden is True
        assert active.id == new_id


class TestGetHistory:
    """get_history() returns all records ordered by triggered_at desc."""

    def test_get_history(self, repo) -> None:
        repo.save(_make_cooldown(days_ago=10, tier=10))
        repo.save(_make_cooldown(days_ago=5, tier=15))
        repo.save(_make_cooldown(days_ago=1, tier=20))

        history = repo.get_history()
        assert len(history) == 3
        # Most recent first
        assert history[0].current_tier == 20
        assert history[1].current_tier == 15
        assert history[2].current_tier == 10

    def test_get_history_includes_deactivated(self, repo) -> None:
        saved_id = repo.save(_make_cooldown(tier=10))
        repo.deactivate(saved_id)
        repo.save(_make_cooldown(tier=15))

        history = repo.get_history()
        assert len(history) == 2


class TestMultipleActive:
    """Multiple active cooldowns: get_active() returns the most recent."""

    def test_multiple_active_returns_latest(self, repo) -> None:
        repo.save(_make_cooldown(days_ago=10, tier=10))
        repo.save(_make_cooldown(days_ago=1, tier=20))

        active = repo.get_active()
        assert active is not None
        assert active.current_tier == 20


class TestUTCHandling:
    """All datetimes stored and compared in UTC."""

    def test_utc_stored(self, repo) -> None:
        now = datetime.now(timezone.utc)
        cooldown = CooldownState(
            triggered_at=now,
            expires_at=now + timedelta(days=30),
            current_tier=20,
        )
        repo.save(cooldown)

        active = repo.get_active()
        assert active is not None
        assert active.triggered_at.tzinfo is not None
        assert active.expires_at.tzinfo is not None
