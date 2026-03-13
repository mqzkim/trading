"""Tests for SqlitePipelineRunRepository -- persistence of pipeline runs."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from src.pipeline.domain.entities import PipelineRun
from src.pipeline.domain.value_objects import PipelineStatus, RunMode, StageResult
from src.pipeline.infrastructure.sqlite_pipeline_repo import SqlitePipelineRunRepository


@pytest.fixture
def repo(tmp_path: object) -> SqlitePipelineRunRepository:
    """Create a repo with a temporary database."""
    db_path = os.path.join(str(tmp_path), "test_pipeline.db")
    return SqlitePipelineRunRepository(db_path=db_path)


def _make_run(
    run_id: str = "run-1",
    status: PipelineStatus = PipelineStatus.COMPLETED,
    mode: RunMode = RunMode.AUTO,
    with_stages: bool = True,
) -> PipelineRun:
    now = datetime.now(timezone.utc)
    stages = []
    if with_stages:
        stages = [
            StageResult(
                stage_name="ingest",
                started_at=now,
                finished_at=now + timedelta(seconds=5),
                status="success",
                symbols_processed=10,
                symbols_succeeded=10,
                symbols_failed=0,
                succeeded_symbols=["AAPL", "MSFT"],
            ),
            StageResult(
                stage_name="score",
                started_at=now + timedelta(seconds=5),
                finished_at=now + timedelta(seconds=15),
                status="partial",
                symbols_processed=10,
                symbols_succeeded=8,
                symbols_failed=2,
                error_message="2 symbols failed scoring",
            ),
        ]
    return PipelineRun(
        run_id=run_id,
        started_at=now,
        finished_at=now + timedelta(minutes=2),
        status=status,
        mode=mode,
        stages=stages,
        halt_reason=None,
        error_message=None,
        next_scheduled=now + timedelta(hours=24),
    )


class TestSqlitePipelineRunRepository:
    def test_save_and_get_by_id(self, repo: SqlitePipelineRunRepository) -> None:
        run = _make_run()
        repo.save(run)
        retrieved = repo.get_by_id("run-1")
        assert retrieved is not None
        assert retrieved.run_id == "run-1"
        assert retrieved.status == PipelineStatus.COMPLETED
        assert retrieved.mode == RunMode.AUTO

    def test_save_preserves_stages(self, repo: SqlitePipelineRunRepository) -> None:
        run = _make_run()
        repo.save(run)
        retrieved = repo.get_by_id("run-1")
        assert retrieved is not None
        assert len(retrieved.stages) == 2
        assert retrieved.stages[0].stage_name == "ingest"
        assert retrieved.stages[0].symbols_processed == 10
        assert retrieved.stages[1].stage_name == "score"
        assert retrieved.stages[1].error_message == "2 symbols failed scoring"

    def test_save_preserves_succeeded_symbols(
        self, repo: SqlitePipelineRunRepository
    ) -> None:
        run = _make_run()
        repo.save(run)
        retrieved = repo.get_by_id("run-1")
        assert retrieved is not None
        assert retrieved.stages[0].succeeded_symbols == ["AAPL", "MSFT"]

    def test_get_by_id_not_found(self, repo: SqlitePipelineRunRepository) -> None:
        assert repo.get_by_id("nonexistent") is None

    def test_get_recent_ordering(self, repo: SqlitePipelineRunRepository) -> None:
        now = datetime.now(timezone.utc)
        for i in range(5):
            run = PipelineRun(
                run_id=f"run-{i}",
                started_at=now + timedelta(hours=i),
                status=PipelineStatus.COMPLETED,
                mode=RunMode.AUTO,
            )
            repo.save(run)
        recent = repo.get_recent(limit=3)
        assert len(recent) == 3
        # Most recent first
        assert recent[0].run_id == "run-4"
        assert recent[1].run_id == "run-3"
        assert recent[2].run_id == "run-2"

    def test_get_recent_default_limit(
        self, repo: SqlitePipelineRunRepository
    ) -> None:
        for i in range(15):
            run = PipelineRun(
                run_id=f"run-{i}",
                started_at=datetime.now(timezone.utc) + timedelta(hours=i),
                status=PipelineStatus.COMPLETED,
                mode=RunMode.AUTO,
            )
            repo.save(run)
        recent = repo.get_recent()
        assert len(recent) == 10  # default limit

    def test_save_update_existing(self, repo: SqlitePipelineRunRepository) -> None:
        run = _make_run(status=PipelineStatus.RUNNING, with_stages=False)
        repo.save(run)
        # Update status
        run.status = PipelineStatus.COMPLETED
        run.finished_at = datetime.now(timezone.utc)
        repo.save(run)
        retrieved = repo.get_by_id("run-1")
        assert retrieved is not None
        assert retrieved.status == PipelineStatus.COMPLETED

    def test_save_without_stages(self, repo: SqlitePipelineRunRepository) -> None:
        run = _make_run(with_stages=False)
        repo.save(run)
        retrieved = repo.get_by_id("run-1")
        assert retrieved is not None
        assert retrieved.stages == []

    def test_save_halted_run(self, repo: SqlitePipelineRunRepository) -> None:
        run = _make_run(status=PipelineStatus.HALTED)
        run.halt_reason = "Crisis regime detected"
        run.error_message = "Drawdown tier 2"
        repo.save(run)
        retrieved = repo.get_by_id("run-1")
        assert retrieved is not None
        assert retrieved.halt_reason == "Crisis regime detected"
        assert retrieved.error_message == "Drawdown tier 2"
