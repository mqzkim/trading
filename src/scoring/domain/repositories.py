"""Scoring 도메인 — Repository Interface (ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .value_objects import Symbol, CompositeScore


class IScoreRepository(ABC):
    """스코어 영속성 인터페이스. 구현은 infrastructure/에서."""

    @abstractmethod
    def save(self, symbol: str, score: CompositeScore) -> None: ...

    @abstractmethod
    def find_latest(self, symbol: str) -> Optional[CompositeScore]: ...

    @abstractmethod
    def find_all_latest(self, limit: int = 100) -> dict[str, CompositeScore]: ...
