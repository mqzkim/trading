"""Domain Event — 바운디드 컨텍스트 간 통신 기반."""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DomainEvent(ABC):
    """
    도메인에서 발생한 사건. 불변.

    규칙:
    - 과거형 이름 사용: OrderPlacedEvent, RegimeChangedEvent
    - 컨텍스트 간 직접 import 금지 — 이벤트 버스를 통해 발행/구독
    - 이벤트 데이터는 원시 타입 또는 Value Object만 포함
    """

    occurred_on: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
        compare=False,
    )

    @property
    def event_type(self) -> str:
        return f"{self.__class__.__module__}.{self.__class__.__name__}"
