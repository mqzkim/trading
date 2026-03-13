"""Pipeline Domain -- Entities.

PipelineRun: mutable entity tracking a single pipeline execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .value_objects import PipelineStatus, RunMode, StageResult


@dataclass
class PipelineRun:
    """A single pipeline execution run.

    Mutable entity -- status, finished_at, stages change during execution.
    """

    run_id: str
    started_at: datetime
    status: PipelineStatus
    mode: RunMode
    finished_at: Optional[datetime] = None
    stages: list[StageResult] = field(default_factory=list)
    halt_reason: Optional[str] = None
    error_message: Optional[str] = None
    next_scheduled: Optional[datetime] = None

    @property
    def symbols_total(self) -> int:
        """Max symbols_processed across all stages."""
        if not self.stages:
            return 0
        return max(s.symbols_processed for s in self.stages)

    @property
    def symbols_succeeded(self) -> int:
        """Symbols succeeded from the last non-skipped stage."""
        for stage in reversed(self.stages):
            if stage.status != "skipped":
                return stage.symbols_succeeded
        return 0

    @property
    def duration(self) -> Optional[timedelta]:
        """Duration between started_at and finished_at, or None if not finished."""
        if self.finished_at is None:
            return None
        return self.finished_at - self.started_at
