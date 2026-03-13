"""Pipeline Domain -- Value Objects.

PipelineStatus, RunMode enums and StageResult frozen dataclass.
No external dependencies -- pure domain types.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PipelineStatus(Enum):
    """Pipeline run lifecycle status."""

    RUNNING = "running"
    COMPLETED = "completed"
    HALTED = "halted"
    FAILED = "failed"


class RunMode(Enum):
    """Pipeline execution mode."""

    AUTO = "auto"
    MANUAL = "manual"
    DRY_RUN = "dry_run"


@dataclass(frozen=True)
class StageResult:
    """Result of a single pipeline stage execution.

    Immutable record capturing timing, symbol counts, and error info.
    """

    stage_name: str
    started_at: datetime
    finished_at: datetime
    status: str  # "success", "partial", "failed", "skipped"
    symbols_processed: int
    symbols_succeeded: int
    symbols_failed: int
    error_message: Optional[str] = None
    succeeded_symbols: list[str] = field(default_factory=list)
