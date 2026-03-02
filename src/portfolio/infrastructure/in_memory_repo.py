"""Portfolio Infrastructure — In-Memory Repositories (테스트 전용)."""
from __future__ import annotations

from typing import Dict, List, Optional

from src.portfolio.domain import IPortfolioRepository, IPositionRepository, Portfolio, Position


class InMemoryPositionRepository(IPositionRepository):
    """메모리 기반 포지션 저장소. 테스트 전용."""

    def __init__(self) -> None:
        self._store: Dict[str, Position] = {}

    def save(self, position: Position) -> None:
        self._store[position.symbol] = position

    def find_by_symbol(self, symbol: str) -> Optional[Position]:
        return self._store.get(symbol)

    def find_all_open(self) -> List[Position]:
        return list(self._store.values())

    def delete(self, symbol: str) -> None:
        self._store.pop(symbol, None)


class InMemoryPortfolioRepository(IPortfolioRepository):
    """메모리 기반 포트폴리오 저장소. 테스트 전용."""

    def __init__(self) -> None:
        self._store: Dict[str, Portfolio] = {}

    def save(self, portfolio: Portfolio) -> None:
        self._store[portfolio.portfolio_id] = portfolio

    def find_by_id(self, portfolio_id: str) -> Optional[Portfolio]:
        return self._store.get(portfolio_id)
