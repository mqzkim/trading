"""Regime 도메인 — Domain Events."""
from __future__ import annotations

from dataclasses import dataclass
from src.shared.domain import DomainEvent
from .value_objects import RegimeType


@dataclass(frozen=True, kw_only=True)
class RegimeChangedEvent(DomainEvent):
    """레짐 전환 이벤트.

    발행: RegimeDetectionService
    구독: Scoring 컨텍스트 (가중치 조정), Signals 컨텍스트
    """
    previous_regime: RegimeType
    new_regime: RegimeType
    confidence: float  # 0.0 - 1.0
    vix_value: float
    adx_value: float
