"""Portfolio 도메인 — Portfolio Aggregate.

불변 임계값 (절대 변경 금지):
  DRAWDOWN_CAUTION  = 0.10  (10%)
  DRAWDOWN_WARNING  = 0.15  (15%)
  DRAWDOWN_CRITICAL = 0.20  (20%)
  MAX_SINGLE_WEIGHT = 0.08  (8%)
  MAX_SECTOR_WEIGHT = 0.25  (25%)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from src.shared.domain import Entity

from .entities import Position
from .value_objects import DrawdownLevel

# 불변 임계값
DRAWDOWN_CAUTION: float = 0.10
DRAWDOWN_WARNING: float = 0.15
DRAWDOWN_CRITICAL: float = 0.20
MAX_SINGLE_WEIGHT: float = 0.08
MAX_SECTOR_WEIGHT: float = 0.25


@dataclass(eq=False)
class Portfolio(Entity[str]):
    """포트폴리오 집합체.

    id = portfolio_id (사용자별 고유 식별자).
    낙폭 방어 3단계 + 단일 종목/섹터 한도 강제.
    """

    portfolio_id: str = ""
    initial_value: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)
    peak_value: float = 0.0

    def __post_init__(self) -> None:
        if self.peak_value == 0.0:
            self.peak_value = self.initial_value

    @property
    def id(self) -> str:
        return self.portfolio_id

    @property
    def total_value(self) -> float:
        return sum(p.market_value for p in self.positions.values())

    @property
    def drawdown(self) -> float:
        """현재 낙폭 (0~1). peak_value를 갱신하며 계산.

        포지션이 없을 때는 initial_value를 현재 가치로 사용 (현금 보유 상태).
        """
        if self.peak_value == 0:
            return 0.0
        current = self.total_value_or_initial
        if current > self.peak_value:
            self.peak_value = current
        return (self.peak_value - current) / self.peak_value

    @property
    def drawdown_level(self) -> DrawdownLevel:
        dd = self.drawdown
        if dd >= DRAWDOWN_CRITICAL:
            return DrawdownLevel.CRITICAL
        if dd >= DRAWDOWN_WARNING:
            return DrawdownLevel.WARNING
        if dd >= DRAWDOWN_CAUTION:
            return DrawdownLevel.CAUTION
        return DrawdownLevel.NORMAL

    @property
    def total_value_or_initial(self) -> float:
        """포지션 기준 총 가치, 없으면 초기 자본."""
        tv = self.total_value
        return tv if tv > 0 else self.initial_value

    def sector_weight(self, sector: str) -> float:
        """특정 섹터의 총 비중 (0.0 ~ 1.0)."""
        total = self.total_value_or_initial
        if total <= 0:
            return 0.0
        return sum(
            p.market_value / total
            for p in self.positions.values()
            if p.sector == sector
        )

    def can_open_position(self, symbol: str, weight: float, *, sector: str = "unknown") -> bool:  # noqa: ARG002
        """신규 포지션 진입 가능 여부.

        낙폭이 CAUTION 이상이면 진입 차단.
        단일 종목 8% 초과 시 진입 차단.
        섹터 비중 + 신규 비중이 25% 초과 시 진입 차단.
        """
        if self.drawdown_level != DrawdownLevel.NORMAL:
            return False
        if weight > MAX_SINGLE_WEIGHT:
            return False
        if self.sector_weight(sector) + weight > MAX_SECTOR_WEIGHT:
            return False
        return True

    def add_position(self, position: Position) -> None:
        """포지션 추가. 낙폭 경보 및 PositionOpenedEvent 발행."""
        from .events import DrawdownAlertEvent, PositionOpenedEvent

        self.positions[position.symbol] = position

        dd_level = self.drawdown_level
        if dd_level != DrawdownLevel.NORMAL:
            self.add_domain_event(
                DrawdownAlertEvent(
                    portfolio_id=self.portfolio_id,
                    drawdown=self.drawdown,
                    level=dd_level.value,
                )
            )

        self.add_domain_event(
            PositionOpenedEvent(
                symbol=position.symbol,
                entry_price=position.entry_price,
                quantity=position.quantity,
            )
        )
