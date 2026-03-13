"""Unit tests for approval SQLite persistence."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.approval.domain.entities import StrategyApproval
from src.approval.domain.value_objects import DailyBudgetTracker, TradeReviewItem
from src.approval.infrastructure.sqlite_approval_repo import (
    SqliteApprovalRepository,
    SqliteBudgetRepository,
    SqliteReviewQueueRepository,
)


def _make_approval(
    *,
    approval_id: str = "appr-001",
    score_threshold: float = 70.0,
    allowed_regimes: list[str] | None = None,
    max_per_trade_pct: float = 8.0,
    expires_at: datetime | None = None,
    daily_budget_cap: float = 10000.0,
    is_active: bool = True,
    suspended_reasons: set[str] | None = None,
) -> StrategyApproval:
    return StrategyApproval(
        _id=approval_id,
        score_threshold=score_threshold,
        allowed_regimes=allowed_regimes or ["Bull", "Sideways"],
        max_per_trade_pct=max_per_trade_pct,
        expires_at=expires_at or (datetime.now(timezone.utc) + timedelta(days=30)),
        daily_budget_cap=daily_budget_cap,
        is_active=is_active,
        suspended_reasons=suspended_reasons or set(),
    )


class TestSqliteApprovalRepository:
    def setup_method(self) -> None:
        self.repo = SqliteApprovalRepository(db_path=":memory:")

    def test_save_and_get_active(self) -> None:
        approval = _make_approval()
        self.repo.save(approval)
        loaded = self.repo.get_active()
        assert loaded is not None
        assert loaded.id == "appr-001"
        assert loaded.score_threshold == 70.0
        assert loaded.allowed_regimes == ["Bull", "Sideways"]
        assert loaded.max_per_trade_pct == 8.0
        assert loaded.daily_budget_cap == 10000.0
        assert loaded.is_active is True

    def test_save_deactivates_previous_active(self) -> None:
        old = _make_approval(approval_id="appr-001")
        self.repo.save(old)
        new = _make_approval(approval_id="appr-002", score_threshold=80.0)
        self.repo.save(new)
        active = self.repo.get_active()
        assert active is not None
        assert active.id == "appr-002"
        # Old one should be deactivated
        old_loaded = self.repo.find_by_id("appr-001")
        assert old_loaded is not None
        assert old_loaded.is_active is False

    def test_get_active_returns_none_when_no_active(self) -> None:
        approval = _make_approval(is_active=False)
        self.repo.save(approval)
        assert self.repo.get_active() is None

    def test_find_by_id(self) -> None:
        approval = _make_approval()
        self.repo.save(approval)
        loaded = self.repo.find_by_id("appr-001")
        assert loaded is not None
        assert loaded.id == "appr-001"

    def test_find_by_id_returns_none_for_missing(self) -> None:
        assert self.repo.find_by_id("nonexistent") is None

    def test_suspended_reasons_json_roundtrip(self) -> None:
        approval = _make_approval(
            suspended_reasons={"regime_change", "drawdown_tier2"}
        )
        self.repo.save(approval)
        loaded = self.repo.get_active()
        assert loaded is not None
        assert loaded.suspended_reasons == {"regime_change", "drawdown_tier2"}

    def test_allowed_regimes_json_roundtrip(self) -> None:
        approval = _make_approval(
            allowed_regimes=["Bull", "Sideways", "Bear"]
        )
        self.repo.save(approval)
        loaded = self.repo.get_active()
        assert loaded is not None
        assert loaded.allowed_regimes == ["Bull", "Sideways", "Bear"]

    def test_save_updates_existing(self) -> None:
        approval = _make_approval()
        self.repo.save(approval)
        approval.suspend("regime_change")
        self.repo.save(approval)
        loaded = self.repo.get_active()
        assert loaded is not None
        assert "regime_change" in loaded.suspended_reasons


class TestSqliteBudgetRepository:
    def setup_method(self) -> None:
        self.repo = SqliteBudgetRepository(db_path=":memory:")

    def test_get_or_create_today_creates_new(self) -> None:
        tracker = self.repo.get_or_create_today(budget_cap=10000.0)
        assert tracker.budget_cap == 10000.0
        assert tracker.spent == 0.0
        assert tracker.trade_count == 0
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert tracker.date == today

    def test_get_or_create_today_returns_existing(self) -> None:
        tracker = self.repo.get_or_create_today(budget_cap=10000.0)
        tracker.record_spend(3000.0)
        self.repo.save(tracker)
        loaded = self.repo.get_or_create_today(budget_cap=10000.0)
        assert loaded.spent == 3000.0
        assert loaded.trade_count == 1

    def test_save_updates_spent(self) -> None:
        tracker = self.repo.get_or_create_today(budget_cap=10000.0)
        tracker.record_spend(5000.0)
        self.repo.save(tracker)
        loaded = self.repo.get_or_create_today(budget_cap=10000.0)
        assert loaded.spent == 5000.0
        assert loaded.trade_count == 1


class TestSqliteReviewQueueRepository:
    def setup_method(self) -> None:
        self.repo = SqliteReviewQueueRepository(db_path=":memory:")

    def test_add_and_list_pending(self) -> None:
        item = TradeReviewItem(
            symbol="AAPL",
            plan_json='{"entry": 150}',
            rejection_reason="Score too low",
            pipeline_run_id="run-001",
        )
        item_id = self.repo.add(item)
        assert item_id > 0
        pending = self.repo.list_pending()
        assert len(pending) == 1
        assert pending[0].symbol == "AAPL"
        assert pending[0].rejection_reason == "Score too low"

    def test_mark_reviewed_excludes_from_pending(self) -> None:
        item = TradeReviewItem(
            symbol="AAPL",
            plan_json='{"entry": 150}',
            rejection_reason="Score too low",
        )
        item_id = self.repo.add(item)
        self.repo.mark_reviewed(item_id, approved=True)
        pending = self.repo.list_pending()
        assert len(pending) == 0

    def test_expire_old(self) -> None:
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        item = TradeReviewItem(
            symbol="AAPL",
            plan_json='{"entry": 150}',
            rejection_reason="Score too low",
            created_at=old_time,
        )
        self.repo.add(item)
        recent = TradeReviewItem(
            symbol="MSFT",
            plan_json='{"entry": 300}',
            rejection_reason="Budget exceeded",
        )
        self.repo.add(recent)
        expired_count = self.repo.expire_old(hours=24)
        assert expired_count == 1
        pending = self.repo.list_pending()
        assert len(pending) == 1
        assert pending[0].symbol == "MSFT"

    def test_expired_items_excluded_from_pending(self) -> None:
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        item = TradeReviewItem(
            symbol="AAPL",
            plan_json='{"entry": 150}',
            rejection_reason="Score too low",
            created_at=old_time,
        )
        self.repo.add(item)
        self.repo.expire_old(hours=24)
        pending = self.repo.list_pending()
        assert len(pending) == 0

    def test_multiple_items_pending(self) -> None:
        for sym in ["AAPL", "MSFT", "GOOGL"]:
            item = TradeReviewItem(
                symbol=sym,
                plan_json=f'{{"symbol": "{sym}"}}',
                rejection_reason="Budget exceeded",
            )
            self.repo.add(item)
        pending = self.repo.list_pending()
        assert len(pending) == 3
