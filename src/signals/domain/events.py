"""Signals 도메인 — Domain Events."""
from __future__ import annotations

from dataclasses import dataclass, field
from src.shared.domain import DomainEvent


@dataclass(frozen=True)
class SignalGeneratedEvent(DomainEvent):
    """매매 시그널 생성 이벤트.

    발행: TradeSignal aggregate
    구독: Portfolio 컨텍스트 (포지션 크기 결정)

    참고: Python dataclass 상속 규칙상 default 필드(occurred_on)가
    부모에 있으므로 자식 필드에 기본값을 부여해 순서 충돌을 방지한다.
    """
    symbol: str = field(default="")
    direction: str = field(default="")          # SignalDirection.value
    strength: float = field(default=0.0)
    consensus_count: int = field(default=0)
    composite_score: float = field(default=0.0)
    strategy: str = field(default="")
