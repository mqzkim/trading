"""Execution Domain — Public API.

DDD 규칙: 레이어 간 cross-import는 이 __init__.py를 통해서만.
"""
from .value_objects import (
    BracketSpec,
    CooldownState,
    ExecutionMode,
    OrderResult,
    OrderSpec,
    TradePlan,
    TradePlanStatus,
)
from .events import (
    CooldownTriggeredEvent,
    KillSwitchActivatedEvent,
    OrderExecutedEvent,
    OrderFailedEvent,
    StopHitAlertEvent,
    TargetReachedAlertEvent,
    TradePlanCreatedEvent,
)
from .services import TradePlanService
from .repositories import IBrokerAdapter, ICooldownRepository, ITradePlanRepository

__all__ = [
    "TradePlan",
    "TradePlanStatus",
    "ExecutionMode",
    "CooldownState",
    "OrderSpec",
    "BracketSpec",
    "OrderResult",
    "TradePlanCreatedEvent",
    "OrderExecutedEvent",
    "OrderFailedEvent",
    "StopHitAlertEvent",
    "TargetReachedAlertEvent",
    "CooldownTriggeredEvent",
    "KillSwitchActivatedEvent",
    "TradePlanService",
    "ITradePlanRepository",
    "IBrokerAdapter",
    "ICooldownRepository",
]
