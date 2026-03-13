"""Tests for pipeline domain model -- PipelineRun entity, value objects, events, repository ABC."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.pipeline.domain.value_objects import PipelineStatus, RunMode, StageResult
from src.pipeline.domain.entities import PipelineRun
from src.pipeline.domain.events import PipelineCompletedEvent, PipelineHaltedEvent
from src.pipeline.domain.repositories import IPipelineRunRepository


# --- PipelineStatus ---


class TestPipelineStatus:
    def test_values(self) -> None:
        assert PipelineStatus.RUNNING.value == "running"
        assert PipelineStatus.COMPLETED.value == "completed"
        assert PipelineStatus.HALTED.value == "halted"
        assert PipelineStatus.FAILED.value == "failed"

    def test_all_members(self) -> None:
        assert len(PipelineStatus) == 4


# --- RunMode ---


class TestRunMode:
    def test_values(self) -> None:
        assert RunMode.AUTO.value == "auto"
        assert RunMode.MANUAL.value == "manual"
        assert RunMode.DRY_RUN.value == "dry_run"

    def test_all_members(self) -> None:
        assert len(RunMode) == 3


# --- StageResult ---


class TestStageResult:
    def test_creation(self) -> None:
        now = datetime.now(timezone.utc)
        sr = StageResult(
            stage_name="ingest",
            started_at=now,
            finished_at=now + timedelta(seconds=10),
            status="success",
            symbols_processed=5,
            symbols_succeeded=5,
            symbols_failed=0,
        )
        assert sr.stage_name == "ingest"
        assert sr.status == "success"
        assert sr.symbols_processed == 5
        assert sr.error_message is None
        assert sr.succeeded_symbols == []

    def test_frozen(self) -> None:
        now = datetime.now(timezone.utc)
        sr = StageResult(
            stage_name="ingest",
            started_at=now,
            finished_at=now,
            status="success",
            symbols_processed=0,
            symbols_succeeded=0,
            symbols_failed=0,
        )
        with pytest.raises(AttributeError):
            sr.stage_name = "other"  # type: ignore[misc]

    def test_succeeded_symbols_default(self) -> None:
        now = datetime.now(timezone.utc)
        sr = StageResult(
            stage_name="score",
            started_at=now,
            finished_at=now,
            status="success",
            symbols_processed=3,
            symbols_succeeded=3,
            symbols_failed=0,
            succeeded_symbols=["AAPL", "MSFT", "GOOG"],
        )
        assert sr.succeeded_symbols == ["AAPL", "MSFT", "GOOG"]


# --- PipelineRun entity ---


class TestPipelineRun:
    def _make_run(self) -> PipelineRun:
        now = datetime.now(timezone.utc)
        return PipelineRun(
            run_id="test-run-1",
            started_at=now,
            status=PipelineStatus.RUNNING,
            mode=RunMode.AUTO,
        )

    def test_creation(self) -> None:
        run = self._make_run()
        assert run.run_id == "test-run-1"
        assert run.status == PipelineStatus.RUNNING
        assert run.mode == RunMode.AUTO
        assert run.stages == []
        assert run.finished_at is None
        assert run.halt_reason is None
        assert run.error_message is None
        assert run.next_scheduled is None

    def test_mutable_status(self) -> None:
        run = self._make_run()
        run.status = PipelineStatus.COMPLETED
        assert run.status == PipelineStatus.COMPLETED

    def test_symbols_total_max_across_stages(self) -> None:
        now = datetime.now(timezone.utc)
        run = self._make_run()
        run.stages = [
            StageResult(
                stage_name="ingest",
                started_at=now,
                finished_at=now,
                status="success",
                symbols_processed=10,
                symbols_succeeded=10,
                symbols_failed=0,
            ),
            StageResult(
                stage_name="score",
                started_at=now,
                finished_at=now,
                status="success",
                symbols_processed=8,
                symbols_succeeded=8,
                symbols_failed=0,
            ),
        ]
        assert run.symbols_total == 10  # max across stages

    def test_symbols_succeeded_from_last_non_skipped(self) -> None:
        now = datetime.now(timezone.utc)
        run = self._make_run()
        run.stages = [
            StageResult(
                stage_name="ingest",
                started_at=now,
                finished_at=now,
                status="success",
                symbols_processed=10,
                symbols_succeeded=10,
                symbols_failed=0,
            ),
            StageResult(
                stage_name="score",
                started_at=now,
                finished_at=now,
                status="success",
                symbols_processed=8,
                symbols_succeeded=7,
                symbols_failed=1,
            ),
            StageResult(
                stage_name="execute",
                started_at=now,
                finished_at=now,
                status="skipped",
                symbols_processed=0,
                symbols_succeeded=0,
                symbols_failed=0,
            ),
        ]
        assert run.symbols_succeeded == 7  # from score (last non-skipped)

    def test_symbols_succeeded_empty_stages(self) -> None:
        run = self._make_run()
        assert run.symbols_succeeded == 0

    def test_duration_when_finished(self) -> None:
        now = datetime.now(timezone.utc)
        run = self._make_run()
        run.finished_at = now + timedelta(minutes=5)
        # started_at is close to now, duration is the diff
        duration = run.duration
        assert duration is not None
        assert duration >= timedelta(minutes=4)

    def test_duration_when_not_finished(self) -> None:
        run = self._make_run()
        assert run.duration is None


# --- Events ---


class TestPipelineEvents:
    def test_completed_event(self) -> None:
        evt = PipelineCompletedEvent(
            run_id="run-1",
            duration_seconds=120.5,
            symbols_succeeded=8,
            mode="auto",
        )
        assert evt.run_id == "run-1"
        assert evt.duration_seconds == 120.5
        assert evt.symbols_succeeded == 8
        assert evt.mode == "auto"
        assert evt.occurred_on is not None

    def test_halted_event(self) -> None:
        evt = PipelineHaltedEvent(
            run_id="run-2",
            halt_reason="drawdown tier 2",
            regime_type="Crisis",
            drawdown_level="warning",
        )
        assert evt.run_id == "run-2"
        assert evt.halt_reason == "drawdown tier 2"
        assert evt.regime_type == "Crisis"


# --- Repository ABC ---


class TestIPipelineRunRepository:
    def test_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            IPipelineRunRepository()  # type: ignore[abstract]

    def test_has_required_methods(self) -> None:
        assert hasattr(IPipelineRunRepository, "save")
        assert hasattr(IPipelineRunRepository, "get_recent")
        assert hasattr(IPipelineRunRepository, "get_by_id")


# --- Settings extensions ---


class TestSettingsExtensions:
    def test_slack_webhook_default(self) -> None:
        from src.settings import Settings

        s = Settings()
        assert s.SLACK_WEBHOOK_URL is None

    def test_pipeline_schedule_defaults(self) -> None:
        from src.settings import Settings

        s = Settings()
        assert s.PIPELINE_SCHEDULE_HOUR == 16
        assert s.PIPELINE_SCHEDULE_MINUTE == 30
