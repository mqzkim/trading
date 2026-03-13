"""Approval Domain -- Public API.

Exports:
- StrategyApproval entity
- ApprovalStatus, GateResult, DailyBudgetTracker, TradeReviewItem value objects
- ApprovalGateService domain service
- IApprovalRepository, IBudgetRepository, IReviewQueueRepository interfaces
- ApprovalCreatedEvent, ApprovalSuspendedEvent domain events
"""
from .entities import StrategyApproval
from .events import ApprovalCreatedEvent, ApprovalSuspendedEvent
from .repositories import IApprovalRepository, IBudgetRepository, IReviewQueueRepository
from .services import ApprovalGateService
from .value_objects import (
    ApprovalStatus,
    DailyBudgetTracker,
    GateResult,
    TradeReviewItem,
)

__all__ = [
    "StrategyApproval",
    "ApprovalStatus",
    "GateResult",
    "DailyBudgetTracker",
    "TradeReviewItem",
    "ApprovalGateService",
    "IApprovalRepository",
    "IBudgetRepository",
    "IReviewQueueRepository",
    "ApprovalCreatedEvent",
    "ApprovalSuspendedEvent",
]
