"""Pipeline Domain -- Repository Interfaces.

Abstract base classes for pipeline persistence.
Implementations live in infrastructure/.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .entities import PipelineRun


class IPipelineRunRepository(ABC):
    """Repository interface for pipeline run persistence."""

    @abstractmethod
    def save(self, run: PipelineRun) -> None:
        """Persist or update a pipeline run."""

    @abstractmethod
    def get_recent(self, limit: int = 10) -> list[PipelineRun]:
        """Return the most recent N runs, ordered by started_at descending."""

    @abstractmethod
    def get_by_id(self, run_id: str) -> Optional[PipelineRun]:
        """Return a pipeline run by its ID, or None if not found."""
