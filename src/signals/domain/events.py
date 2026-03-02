"""Signals 도메인 — Domain Events."""
from __future__ import annotations

from dataclasses import dataclass
from src.shared.domain import DomainEvent
from .value_objects import SignalDirection


@dataclass(frozen=True)
class SignalGeneratedEvent(DomainEvent):
    """매매 시그널 생성 이벤트.

    발행: TradeSignal aggregate
    구독: Portfolio 컨텍스트 (포지션 크기 결정)
    """
    symbol: str
    direction: str              # SignalDirection.value
    strength: float
    consensus_count: int
    composite_score: float
    strategy: str
