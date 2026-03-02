"""Signals 도메인 — Repository Interface (ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class ISignalRepository(ABC):
    """시그널 영속성 인터페이스."""

    @abstractmethod
    def save(self, symbol: str, direction: str, strength: float, metadata: dict) -> None: ...

    @abstractmethod
    def find_active(self, symbol: str) -> Optional[dict]: ...

    @abstractmethod
    def find_all_active(self) -> list[dict]: ...
