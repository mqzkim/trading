"""Approval Infrastructure -- SQLite Repositories.

Persists StrategyApproval, DailyBudgetTracker, and TradeReviewItem to SQLite.
Follows SqliteCooldownRepository pattern: CREATE TABLE IF NOT EXISTS, WAL mode, db_path constructor.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from src.approval.domain.entities import StrategyApproval
from src.approval.domain.repositories import (
    IApprovalRepository,
    IBudgetRepository,
    IReviewQueueRepository,
)
from src.approval.domain.value_objects import DailyBudgetTracker, TradeReviewItem


class SqliteApprovalRepository(IApprovalRepository):
    """SQLite persistence for strategy approvals.

    Enforces single active approval rule: saving a new active approval
    deactivates all previous ones.
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS strategy_approvals (
            approval_id         TEXT PRIMARY KEY,
            score_threshold     REAL NOT NULL,
            allowed_regimes     TEXT NOT NULL,
            max_per_trade_pct   REAL NOT NULL,
            expires_at          TEXT NOT NULL,
            daily_budget_cap    REAL NOT NULL,
            created_at          TEXT NOT NULL,
            is_active           INTEGER NOT NULL DEFAULT 1,
            suspended_reasons   TEXT NOT NULL DEFAULT '[]'
        );
    """

    def __init__(self, db_path: str = "data/portfolio.db") -> None:
        self._db_path = db_path
        self._memory_conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._db_path == ":memory:":
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(":memory:")
            return self._memory_conn
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        if self._db_path != ":memory:":
            dir_part = os.path.dirname(self._db_path)
            if dir_part:
                os.makedirs(dir_part, exist_ok=True)
        conn = self._get_conn()
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(self._CREATE_TABLE)
        if self._db_path != ":memory:":
            conn.close()

    def save(self, approval: StrategyApproval) -> None:
        """Persist approval. Deactivates previous active approvals if this one is active."""
        with self._get_conn() as conn:
            if approval.is_active:
                conn.execute(
                    "UPDATE strategy_approvals SET is_active = 0 WHERE is_active = 1 AND approval_id != ?",
                    (approval.id,),
                )
            conn.execute(
                """
                INSERT OR REPLACE INTO strategy_approvals
                    (approval_id, score_threshold, allowed_regimes, max_per_trade_pct,
                     expires_at, daily_budget_cap, created_at, is_active, suspended_reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval.id,
                    approval.score_threshold,
                    json.dumps(approval.allowed_regimes),
                    approval.max_per_trade_pct,
                    approval.expires_at.isoformat(),
                    approval.daily_budget_cap,
                    approval.created_at.isoformat(),
                    1 if approval.is_active else 0,
                    json.dumps(sorted(approval.suspended_reasons)),
                ),
            )

    def get_active(self) -> Optional[StrategyApproval]:
        """Return the currently active approval, or None."""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM strategy_approvals WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1",
            ).fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def find_by_id(self, approval_id: str) -> Optional[StrategyApproval]:
        """Find approval by ID."""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM strategy_approvals WHERE approval_id = ?",
                (approval_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> StrategyApproval:
        """Convert SQLite row to StrategyApproval entity."""
        return StrategyApproval(
            _id=row["approval_id"],
            score_threshold=row["score_threshold"],
            allowed_regimes=json.loads(row["allowed_regimes"]),
            max_per_trade_pct=row["max_per_trade_pct"],
            expires_at=datetime.fromisoformat(row["expires_at"]).replace(
                tzinfo=timezone.utc
            ),
            daily_budget_cap=row["daily_budget_cap"],
            created_at=datetime.fromisoformat(row["created_at"]).replace(
                tzinfo=timezone.utc
            ),
            is_active=bool(row["is_active"]),
            suspended_reasons=set(json.loads(row["suspended_reasons"])),
        )


class SqliteBudgetRepository(IBudgetRepository):
    """SQLite persistence for daily budget tracking."""

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS daily_budget (
            date_key            TEXT PRIMARY KEY,
            budget_cap          REAL NOT NULL,
            spent               REAL NOT NULL DEFAULT 0.0,
            trade_count         INTEGER NOT NULL DEFAULT 0,
            updated_at          TEXT NOT NULL
        );
    """

    def __init__(self, db_path: str = "data/portfolio.db") -> None:
        self._db_path = db_path
        self._memory_conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._db_path == ":memory:":
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(":memory:")
            return self._memory_conn
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        if self._db_path != ":memory:":
            dir_part = os.path.dirname(self._db_path)
            if dir_part:
                os.makedirs(dir_part, exist_ok=True)
        conn = self._get_conn()
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(self._CREATE_TABLE)
        if self._db_path != ":memory:":
            conn.close()

    def get_or_create_today(self, budget_cap: float) -> DailyBudgetTracker:
        """Return today's budget tracker, creating with spent=0 if not exists."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM daily_budget WHERE date_key = ?",
                (today,),
            ).fetchone()
            if row is not None:
                return DailyBudgetTracker(
                    budget_cap=row["budget_cap"],
                    date=row["date_key"],
                    spent=row["spent"],
                    trade_count=row["trade_count"],
                )
            # Create new entry
            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO daily_budget (date_key, budget_cap, spent, trade_count, updated_at)
                VALUES (?, ?, 0.0, 0, ?)
                """,
                (today, budget_cap, now_iso),
            )
            return DailyBudgetTracker(
                budget_cap=budget_cap,
                date=today,
                spent=0.0,
                trade_count=0,
            )

    def save(self, tracker: DailyBudgetTracker) -> None:
        """Update the daily budget tracker."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE daily_budget
                SET spent = ?, trade_count = ?, updated_at = ?
                WHERE date_key = ?
                """,
                (tracker.spent, tracker.trade_count, now_iso, tracker.date),
            )


class SqliteReviewQueueRepository(IReviewQueueRepository):
    """SQLite persistence for trade review queue."""

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS trade_review_queue (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol              TEXT NOT NULL,
            plan_json           TEXT NOT NULL,
            rejection_reason    TEXT NOT NULL,
            pipeline_run_id     TEXT,
            created_at          TEXT NOT NULL,
            reviewed            INTEGER NOT NULL DEFAULT 0,
            expired             INTEGER NOT NULL DEFAULT 0
        );
    """

    def __init__(self, db_path: str = "data/portfolio.db") -> None:
        self._db_path = db_path
        self._memory_conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._db_path == ":memory:":
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(":memory:")
            return self._memory_conn
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        if self._db_path != ":memory:":
            dir_part = os.path.dirname(self._db_path)
            if dir_part:
                os.makedirs(dir_part, exist_ok=True)
        conn = self._get_conn()
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(self._CREATE_TABLE)
        if self._db_path != ":memory:":
            conn.close()

    def add(self, item: TradeReviewItem) -> int:
        """Insert a review item. Returns assigned ID."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO trade_review_queue
                    (symbol, plan_json, rejection_reason, pipeline_run_id, created_at, reviewed, expired)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.symbol,
                    item.plan_json,
                    item.rejection_reason,
                    item.pipeline_run_id,
                    item.created_at.isoformat(),
                    1 if item.reviewed else 0,
                    1 if item.expired else 0,
                ),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def list_pending(self) -> List[TradeReviewItem]:
        """Return non-reviewed, non-expired items."""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM trade_review_queue WHERE reviewed = 0 AND expired = 0 ORDER BY created_at ASC",
            ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def mark_reviewed(self, item_id: int, approved: bool) -> None:
        """Mark item as reviewed."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE trade_review_queue SET reviewed = 1 WHERE id = ?",
                (item_id,),
            )

    def expire_old(self, hours: int = 24) -> int:
        """Mark items older than hours as expired. Returns count expired."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                UPDATE trade_review_queue
                SET expired = 1
                WHERE reviewed = 0 AND expired = 0 AND created_at < ?
                """,
                (cutoff,),
            )
            return cursor.rowcount

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> TradeReviewItem:
        """Convert SQLite row to TradeReviewItem."""
        return TradeReviewItem(
            symbol=row["symbol"],
            plan_json=row["plan_json"],
            rejection_reason=row["rejection_reason"],
            pipeline_run_id=row["pipeline_run_id"],
            created_at=datetime.fromisoformat(row["created_at"]).replace(
                tzinfo=timezone.utc
            ),
            reviewed=bool(row["reviewed"]),
            expired=bool(row["expired"]),
            id=row["id"],
        )
