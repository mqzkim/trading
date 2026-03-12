"""Scoring 도메인 — Domain Events."""
from __future__ import annotations

from dataclasses import dataclass
from src.shared.domain import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ScoreUpdatedEvent(DomainEvent):
    """종목 스코어 업데이트 이벤트.

    발행: ScoringResult aggregate
    구독: Signals 컨텍스트
    """
    symbol: str
    composite_score: float
    risk_adjusted_score: float
    safety_passed: bool
    strategy: str
