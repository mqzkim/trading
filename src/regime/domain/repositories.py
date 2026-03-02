"""Regime 도메인 — Repository Interface (ABC).

구현은 infrastructure/ 레이어에서 담당.
domain/ 레이어는 인터페이스만 정의.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from .entities import MarketRegime


class IRegimeRepository(ABC):
    """레짐 데이터 영속성 인터페이스."""

    @abstractmethod
    def save(self, regime: MarketRegime) -> None:
        """레짐 결과 저장."""
        ...

    @abstractmethod
    def find_latest(self) -> Optional[MarketRegime]:
        """가장 최근 레짐 조회."""
        ...

    @abstractmethod
    def find_by_date_range(
        self,
        start: datetime,
        end: datetime,
    ) -> list[MarketRegime]:
        """기간별 레짐 이력 조회."""
        ...
