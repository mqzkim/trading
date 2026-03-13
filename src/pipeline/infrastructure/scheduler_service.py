"""Pipeline Infrastructure -- APScheduler Service.

Wraps BackgroundScheduler with SQLAlchemyJobStore for SQLite job persistence.
CronTrigger fires daily at configured time (default 16:30 ET, Mon-Fri).
Market calendar guard skips non-trading days.

Note: APScheduler's SQLAlchemy job store uses pickle internally for job
serialization. This is APScheduler's design choice and only serializes
our own registered functions (not untrusted data).
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Callable, Optional

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Module-level registry for scheduled functions.
# APScheduler SQLAlchemy job store serializes job targets -- instance methods
# that contain the scheduler as an attribute cannot be serialized.
# Instead, we register the pipeline function at module level.
_registered_pipeline_fn: Callable[[], Any] | None = None
_registered_calendar: Any = None


def _scheduled_pipeline_run() -> None:
    """Module-level function invoked by APScheduler.

    Checks market calendar, then calls the registered pipeline function.
    Cannot be an instance method because APScheduler serializes job targets.
    """
    if _registered_calendar is not None:
        today = date.today()
        if not _registered_calendar.is_trading_day(today):
            logger.info("Pipeline skipped: %s is not a trading day", today)
            return

    if _registered_pipeline_fn is None:
        logger.error("No pipeline function registered for scheduler")
        return

    logger.info("Scheduled pipeline run starting")
    try:
        _registered_pipeline_fn()
    except Exception:
        logger.error("Scheduled pipeline run failed", exc_info=True)


class SchedulerService:
    """APScheduler wrapper with SQLite job persistence and market calendar guard.

    Persists scheduled jobs in SQLite so schedule survives process restarts.
    Uses replace_existing=True to prevent duplicate jobs (Pitfall 1).
    Sets misfire_grace_time at scheduler level, not per-job (Pitfall 2).
    """

    JOB_ID = "daily_pipeline"

    def __init__(
        self,
        db_path: str,
        run_pipeline_fn: Callable[[], Any],
        calendar_service: Any = None,
        schedule_hour: int = 16,
        schedule_minute: int = 30,
    ) -> None:
        global _registered_pipeline_fn, _registered_calendar
        _registered_pipeline_fn = run_pipeline_fn
        _registered_calendar = calendar_service

        self._run_pipeline_fn = run_pipeline_fn
        self._calendar = calendar_service
        self._schedule_hour = schedule_hour
        self._schedule_minute = schedule_minute

        jobstores = {
            "default": SQLAlchemyJobStore(url=f"sqlite:///{db_path}"),
        }
        self._scheduler = BackgroundScheduler(
            jobstores=jobstores,
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 3600,
            },
            timezone="US/Eastern",
        )

    def start(self) -> None:
        """Add the daily pipeline job and start the scheduler."""
        self._scheduler.add_job(
            _scheduled_pipeline_run,
            CronTrigger(
                hour=self._schedule_hour,
                minute=self._schedule_minute,
                day_of_week="mon-fri",
                timezone="US/Eastern",
            ),
            id=self.JOB_ID,
            replace_existing=True,
            name="Daily Trading Pipeline",
        )
        self._scheduler.start()
        logger.info(
            "Scheduler started: daily pipeline at %02d:%02d ET Mon-Fri",
            self._schedule_hour,
            self._schedule_minute,
        )

    def stop(self) -> None:
        """Shut down the scheduler."""
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    def get_next_run_time(self) -> Optional[datetime]:
        """Return the next scheduled fire time, or None if no job scheduled."""
        job = self._scheduler.get_job(self.JOB_ID)
        if job is None:
            return None
        return job.next_run_time

    def _scheduled_run(self) -> None:
        """Direct invocation (non-APScheduler path) for testing and manual use.

        Checks calendar, then calls the pipeline function.
        """
        if self._calendar is not None:
            today = date.today()
            if not self._calendar.is_trading_day(today):
                logger.info("Pipeline skipped: %s is not a trading day", today)
                return

        logger.info("Scheduled pipeline run starting")
        try:
            self._run_pipeline_fn()
        except Exception:
            logger.error("Scheduled pipeline run failed", exc_info=True)
