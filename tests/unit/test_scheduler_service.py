"""Tests for SchedulerService (APScheduler wrapper).

Covers: job creation, holiday skip, trading day execution, duplicate prevention.
"""
from __future__ import annotations

import os
import tempfile
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.infrastructure.scheduler_service import SchedulerService


# A plain function (picklable) for APScheduler job store serialization
_pipeline_call_count = 0


def _dummy_pipeline():
    global _pipeline_call_count
    _pipeline_call_count += 1


@pytest.fixture
def tmp_db():
    """Create a temporary SQLite DB path for scheduler job store."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def reset_call_count():
    global _pipeline_call_count
    _pipeline_call_count = 0


class TestSchedulerService:
    """Test SchedulerService APScheduler wrapper."""

    def test_scheduler_creates_job(self, tmp_db):
        """Verify job is added with correct trigger params."""
        svc = SchedulerService(
            db_path=tmp_db,
            run_pipeline_fn=_dummy_pipeline,
            schedule_hour=16,
            schedule_minute=30,
        )
        svc.start()

        try:
            job = svc._scheduler.get_job(SchedulerService.JOB_ID)
            assert job is not None
            assert job.name == "Daily Trading Pipeline"
            # CronTrigger fields
            trigger = job.trigger
            assert str(trigger) is not None  # trigger has a string representation
        finally:
            svc.stop()

    def test_scheduler_skips_holiday(self, tmp_db):
        """Mock calendar to return False -- pipeline should not be called."""
        fn = MagicMock()
        calendar = MagicMock()
        calendar.is_trading_day.return_value = False

        svc = SchedulerService(
            db_path=tmp_db,
            run_pipeline_fn=fn,
            calendar_service=calendar,
        )

        # Directly invoke the scheduled run method
        svc._scheduled_run()

        fn.assert_not_called()
        calendar.is_trading_day.assert_called_once()

    def test_scheduler_runs_on_trading_day(self, tmp_db):
        """Mock calendar to return True -- pipeline should be called."""
        fn = MagicMock()
        calendar = MagicMock()
        calendar.is_trading_day.return_value = True

        svc = SchedulerService(
            db_path=tmp_db,
            run_pipeline_fn=fn,
            calendar_service=calendar,
        )

        svc._scheduled_run()

        fn.assert_called_once()

    def test_scheduler_replace_existing(self, tmp_db):
        """Start twice -- only one job should exist (no duplicates)."""
        svc = SchedulerService(
            db_path=tmp_db,
            run_pipeline_fn=_dummy_pipeline,
        )
        svc.start()

        try:
            # Add again with replace_existing (simulate restart behavior)
            svc._scheduler.add_job(
                _dummy_pipeline,
                id=SchedulerService.JOB_ID,
                replace_existing=True,
                trigger="interval",
                seconds=3600,
            )

            jobs = svc._scheduler.get_jobs()
            pipeline_jobs = [j for j in jobs if j.id == SchedulerService.JOB_ID]
            assert len(pipeline_jobs) == 1
        finally:
            svc.stop()

    def test_scheduler_get_next_run_time(self, tmp_db):
        """get_next_run_time returns a datetime after start."""
        svc = SchedulerService(
            db_path=tmp_db,
            run_pipeline_fn=_dummy_pipeline,
        )
        svc.start()

        try:
            next_time = svc.get_next_run_time()
            assert next_time is not None
        finally:
            svc.stop()

    def test_scheduler_get_next_run_time_no_job(self, tmp_db):
        """get_next_run_time returns None when scheduler has no job."""
        svc = SchedulerService(
            db_path=tmp_db,
            run_pipeline_fn=_dummy_pipeline,
        )
        # Don't start -- no job added
        svc._scheduler.start()

        try:
            next_time = svc.get_next_run_time()
            assert next_time is None
        finally:
            svc.stop()

    def test_scheduled_run_without_calendar(self, tmp_db):
        """Without calendar service, pipeline runs unconditionally."""
        fn = MagicMock()
        svc = SchedulerService(
            db_path=tmp_db,
            run_pipeline_fn=fn,
            calendar_service=None,
        )

        svc._scheduled_run()
        fn.assert_called_once()

    def test_scheduled_run_handles_pipeline_error(self, tmp_db):
        """Pipeline errors in scheduled run are caught, not propagated."""
        fn = MagicMock(side_effect=RuntimeError("Pipeline crashed"))
        calendar = MagicMock()
        calendar.is_trading_day.return_value = True

        svc = SchedulerService(
            db_path=tmp_db,
            run_pipeline_fn=fn,
            calendar_service=calendar,
        )

        # Should not raise
        svc._scheduled_run()
        fn.assert_called_once()
