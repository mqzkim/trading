"""Execution Domain — Public API.

DDD 규칙: 레이어 간 cross-import는 이 __init__.py를 통해서만.
"""
from .value_objects import BracketSpec, OrderResult, TradePlan, TradePlanStatus
from .events import OrderExecutedEvent, OrderFailedEvent, TradePlanCreatedEvent
from .services import TradePlanService
from .repositories import ITradePlanRepository

__all__ = [
    "TradePlan",
    "TradePlanStatus",
    "BracketSpec",
    "OrderResult",
    "TradePlanCreatedEvent",
    "OrderExecutedEvent",
    "OrderFailedEvent",
    "TradePlanService",
    "ITradePlanRepository",
]
