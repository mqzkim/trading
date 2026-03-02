"""Portfolio 도메인 — Repository Interfaces.

인프라 구현체는 infrastructure/ 레이어에 위치.
도메인은 인터페이스(ABC)만 의존.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .aggregates import Portfolio
from .entities import Position


class IPositionRepository(ABC):
    """포지션 저장소 인터페이스."""

    @abstractmethod
    def save(self, position: Position) -> None: ...

    @abstractmethod
    def find_by_symbol(self, symbol: str) -> Optional[Position]: ...

    @abstractmethod
    def find_all_open(self) -> List[Position]: ...

    @abstractmethod
    def delete(self, symbol: str) -> None: ...


class IPortfolioRepository(ABC):
    """포트폴리오 저장소 인터페이스."""

    @abstractmethod
    def save(self, portfolio: Portfolio) -> None: ...

    @abstractmethod
    def find_by_id(self, portfolio_id: str) -> Optional[Portfolio]: ...
