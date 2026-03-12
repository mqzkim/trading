"""Execution Domain — Repository Interfaces.

인프라 구현체는 infrastructure/ 레이어에 위치.
도메인은 인터페이스(ABC)만 의존.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .value_objects import TradePlan, TradePlanStatus


class ITradePlanRepository(ABC):
    """Trade plan 저장소 인터페이스."""

    @abstractmethod
    def save(self, plan: TradePlan, status: TradePlanStatus) -> None: ...

    @abstractmethod
    def find_pending(self) -> List[dict]: ...

    @abstractmethod
    def find_by_symbol(self, symbol: str) -> Optional[dict]: ...

    @abstractmethod
    def update_status(self, symbol: str, new_status: TradePlanStatus) -> None: ...
