"""Execution Domain — Domain Events.

이벤트 타입은 기반 클래스 property(event_type)로 자동 결정됨.
컨텍스트 간 직접 import 금지 -- 이벤트 버스를 통해 발행/구독.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain import DomainEvent


@dataclass(frozen=True)
class TradePlanCreatedEvent(DomainEvent):
    """Trade plan 생성 완료."""

    symbol: str = ""
    direction: str = ""
    entry_price: float = 0.0
    quantity: int = 0


@dataclass(frozen=True)
class OrderExecutedEvent(DomainEvent):
    """주문 체결 완료."""

    order_id: str = ""
    symbol: str = ""
    quantity: int = 0
    filled_price: float = 0.0


@dataclass(frozen=True)
class OrderFailedEvent(DomainEvent):
    """주문 실패."""

    symbol: str = ""
    error_message: str = ""


@dataclass(frozen=True)
class StopHitAlertEvent(DomainEvent):
    """Stop-loss price hit alert."""

    symbol: str = ""
    current_price: float = 0.0
    stop_price: float = 0.0


@dataclass(frozen=True)
class TargetReachedAlertEvent(DomainEvent):
    """Take-profit target reached alert."""

    symbol: str = ""
    current_price: float = 0.0
    target_price: float = 0.0


@dataclass(frozen=True)
class CooldownTriggeredEvent(DomainEvent):
    """Drawdown cooldown triggered."""

    tier: int = 0
    reason: str = ""
    expires_at: str = ""


@dataclass(frozen=True)
class KillSwitchActivatedEvent(DomainEvent):
    """Emergency kill switch activated."""

    liquidate: bool = False
    reason: str = ""
