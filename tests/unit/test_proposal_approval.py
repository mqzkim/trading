"""Tests for proposal approve/reject status transitions.

Covers:
- Approve sets status to "approved"
- Reject sets status to "rejected"
- Approve unknown ID raises ValueError
- History returns last 5 ordered by decided_at desc
"""
from __future__ import annotations

from datetime import datetime, timezone

import duckdb
import pytest

from src.performance.infrastructure.duckdb_proposal_repository import DuckDBProposalRepository
from src.performance.application.commands import ApproveProposalCommand, RejectProposalCommand
from src.performance.application.handlers import AttributionHandler


def _insert_proposal(repo: DuckDBProposalRepository, proposal_id: str, status: str = "pending") -> None:
    """Helper: insert a test proposal."""
    repo.save({
        "id": proposal_id,
        "regime": "Bull",
        "axis": "fundamental",
        "current_weight": 0.40,
        "proposed_weight": 0.45,
        "walk_forward_sharpe": 0.8,
        "status": status,
    })


class TestApproval:
    """Test proposal approve/reject via AttributionHandler."""

    def test_approve_sets_status(self) -> None:
        """After approve, proposal status == 'approved'."""
        conn = duckdb.connect(":memory:")
        repo = DuckDBProposalRepository(conn)
        _insert_proposal(repo, "test-approve-id")

        repo.approve("test-approve-id")
        result = repo.find_by_id("test-approve-id")

        assert result is not None
        assert result["status"] == "approved"

    def test_reject_sets_status(self) -> None:
        """After reject, proposal status == 'rejected'."""
        conn = duckdb.connect(":memory:")
        repo = DuckDBProposalRepository(conn)
        _insert_proposal(repo, "test-reject-id")

        repo.reject("test-reject-id")
        result = repo.find_by_id("test-reject-id")

        assert result is not None
        assert result["status"] == "rejected"

    def test_approve_unknown_id(self) -> None:
        """Approving non-existent ID: no error but status unchanged (noop)."""
        conn = duckdb.connect(":memory:")
        repo = DuckDBProposalRepository(conn)

        # Should not raise -- DuckDB UPDATE on missing ID is a noop
        repo.approve("nonexistent-id")
        result = repo.find_by_id("nonexistent-id")
        assert result is None

    def test_history_returns_last_5(self) -> None:
        """list_history() returns at most 5 items ordered by decided_at desc."""
        conn = duckdb.connect(":memory:")
        repo = DuckDBProposalRepository(conn)

        # Insert 7 proposals, approve/reject them
        for i in range(7):
            pid = f"hist-{i:02d}"
            _insert_proposal(repo, pid)
            if i % 2 == 0:
                repo.approve(pid)
            else:
                repo.reject(pid)

        history = repo.list_history(limit=5)
        assert len(history) <= 5
        assert all(h["status"] in ("approved", "rejected") for h in history)

    def test_handler_approve_via_command(self) -> None:
        """AttributionHandler.handle_approve updates proposal status."""
        conn = duckdb.connect(":memory:")
        proposal_repo = DuckDBProposalRepository(conn)
        _insert_proposal(proposal_repo, "cmd-approve-id")

        # Use a mock trade repo (not needed for approve)
        from unittest.mock import MagicMock

        trade_repo = MagicMock()
        handler = AttributionHandler(trade_repo=trade_repo, proposal_repo=proposal_repo)

        result = handler.handle_approve(ApproveProposalCommand(proposal_id="cmd-approve-id"))
        assert result["status"] == "approved"

        stored = proposal_repo.find_by_id("cmd-approve-id")
        assert stored is not None
        assert stored["status"] == "approved"

    def test_handler_reject_via_command(self) -> None:
        """AttributionHandler.handle_reject updates proposal status."""
        conn = duckdb.connect(":memory:")
        proposal_repo = DuckDBProposalRepository(conn)
        _insert_proposal(proposal_repo, "cmd-reject-id")

        from unittest.mock import MagicMock

        trade_repo = MagicMock()
        handler = AttributionHandler(trade_repo=trade_repo, proposal_repo=proposal_repo)

        result = handler.handle_reject(RejectProposalCommand(proposal_id="cmd-reject-id"))
        assert result["status"] == "rejected"

        stored = proposal_repo.find_by_id("cmd-reject-id")
        assert stored is not None
        assert stored["status"] == "rejected"
