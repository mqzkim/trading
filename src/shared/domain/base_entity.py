"""Base Entity — DDD Entity 기반 클래스."""
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Generic, TypeVar
from .domain_event import DomainEvent

TId = TypeVar("TId")


@dataclass(eq=False)
class Entity(ABC, Generic[TId]):
    """
    식별자(ID)를 가진 도메인 객체.
    ID가 동일하면 같은 객체로 판단.

    규칙:
    - 비즈니스 행위(메서드)를 포함해야 한다 (Anemic Model 금지)
    - 상태 변경은 도메인 메서드를 통해서만 수행
    """

    _domain_events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    @property
    def id(self) -> TId:
        raise NotImplementedError

    def add_domain_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def pull_domain_events(self) -> list[DomainEvent]:
        """이벤트를 꺼내고 큐를 비운다."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
