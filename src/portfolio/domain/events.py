"""Portfolio 도메인 — Domain Events.

이벤트 타입은 기반 클래스 property(event_type)로 자동 결정됨.
컨텍스트 간 직접 import 금지 — 이벤트 버스를 통해 발행/구독.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain import DomainEvent


@dataclass(frozen=True)
class PositionOpenedEvent(DomainEvent):
    """포지션 진입 완료."""

    symbol: str = ""
    entry_price: float = 0.0
    quantity: int = 0


@dataclass(frozen=True)
class PositionClosedEvent(DomainEvent):
    """포지션 청산 완료."""

    symbol: str = ""
    pnl: float = 0.0
    pnl_pct: float = 0.0


@dataclass(frozen=True)
class DrawdownAlertEvent(DomainEvent):
    """낙폭 경보 발생."""

    portfolio_id: str = ""
    drawdown: float = 0.0
    level: str = ""  # "caution" | "warning" | "critical"
