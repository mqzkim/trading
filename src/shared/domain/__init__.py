"""Shared Domain — DDD 기반 클래스 공개 API."""
from .base_entity import Entity
from .base_value_object import ValueObject
from .domain_event import DomainEvent
from .result import Ok, Err, Result

__all__ = ["Entity", "ValueObject", "DomainEvent", "Ok", "Err", "Result"]
