"""Pipeline Domain -- Public API.

DDD rule: cross-layer imports use this __init__.py only.
"""
from .value_objects import PipelineStatus, RunMode, StageResult
from .entities import PipelineRun
from .events import PipelineCompletedEvent, PipelineHaltedEvent
from .repositories import IPipelineRunRepository
from .services import PipelineOrchestrator

__all__ = [
    "PipelineStatus",
    "RunMode",
    "StageResult",
    "PipelineRun",
    "PipelineCompletedEvent",
    "PipelineHaltedEvent",
    "IPipelineRunRepository",
    "PipelineOrchestrator",
]
