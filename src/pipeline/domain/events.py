"""Pipeline Domain -- Domain Events.

Events published when pipeline runs complete or halt.
Cross-context communication via event bus only.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain import DomainEvent


@dataclass(frozen=True)
class PipelineCompletedEvent(DomainEvent):
    """Pipeline run completed successfully."""

    run_id: str = ""
    duration_seconds: float = 0.0
    symbols_succeeded: int = 0
    mode: str = ""


@dataclass(frozen=True)
class PipelineHaltedEvent(DomainEvent):
    """Pipeline run halted due to safety conditions."""

    run_id: str = ""
    halt_reason: str = ""
    regime_type: str = ""
    drawdown_level: str = ""
