"""Pipeline Application -- Commands and Queries.

RunPipelineCommand: trigger a pipeline execution.
GetPipelineStatusQuery: query recent run history.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.pipeline.domain.value_objects import RunMode


@dataclass(frozen=True)
class RunPipelineCommand:
    """Command to trigger a pipeline execution."""

    dry_run: bool = False
    mode: RunMode = RunMode.MANUAL


@dataclass(frozen=True)
class GetPipelineStatusQuery:
    """Query for recent pipeline run history."""

    limit: int = 10
