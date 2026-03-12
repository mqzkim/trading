"""Portfolio 도메인 — Value Objects."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.shared.domain import ValueObject


class RiskTier(Enum):
    LOW = "low"        # Z > 3.0, M < -2.5
    MEDIUM = "medium"  # 1.81 <= Z <= 3.0
    HIGH = "high"      # Z < 1.81 (Safety Gate 통과 후 경계)


class DrawdownLevel(Enum):
    NORMAL = "normal"      # 낙폭 < 10%
    CAUTION = "caution"    # 낙폭 10~15% -> 신규 진입 중단
    WARNING = "warning"    # 낙폭 15~20% -> 포지션 50% 축소
    CRITICAL = "critical"  # 낙폭 > 20% -> 전량 청산


@dataclass(frozen=True)
class PortfolioWeight(ValueObject):
    """종목 비중 (0.0 ~ 0.08)."""

    value: float
    MAX_SINGLE: float = 0.08  # 8%

    def _validate(self) -> None:
        if not (0.0 <= self.value <= self.MAX_SINGLE):
            raise ValueError(
                f"단일 종목 비중은 0~{self.MAX_SINGLE * 100:.0f}% 범위여야 합니다: {self.value}"
            )


@dataclass(frozen=True)
class SectorWeight(ValueObject):
    """섹터 비중 (0.0 ~ 0.25)."""

    value: float
    MAX_SECTOR: float = 0.25  # 25%

    def _validate(self) -> None:
        if not (0.0 <= self.value <= self.MAX_SECTOR):
            raise ValueError(
                f"섹터 비중은 0~{self.MAX_SECTOR * 100:.0f}% 범위여야 합니다: {self.value}"
            )


@dataclass(frozen=True)
class KellyFraction(ValueObject):
    """Kelly 비율 — 1/4 Fractional Kelly 고정.

    FRACTION = 0.25 (불변). Full Kelly 직접 사용 금지.
    """

    full_kelly: float = 0.0  # 원래 Full Kelly 값 (계산용)

    FRACTION: float = 0.25  # 1/4 Kelly — 절대 변경 금지

    @property
    def value(self) -> float:
        return self.full_kelly * self.FRACTION

    def _validate(self) -> None:
        if self.full_kelly < 0:
            raise ValueError("Full Kelly는 0 이상이어야 합니다")


@dataclass(frozen=True)
class ATRStop(ValueObject):
    """ATR 기반 스탑로스.

    stop_price = entry_price - (atr * multiplier)
    multiplier 범위: 2.5 ~ 3.5 (ATR(21) 기준)
    """

    entry_price: float
    atr: float
    multiplier: float = 2.5  # 2.5-3.5x ATR(21)

    @property
    def stop_price(self) -> float:
        return self.entry_price - (self.atr * self.multiplier)

    def _validate(self) -> None:
        if not (2.5 <= self.multiplier <= 3.5):
            raise ValueError(f"ATR 배수는 2.5-3.5x 범위여야 합니다: {self.multiplier}")
        if self.atr <= 0:
            raise ValueError("ATR은 양수여야 합니다")
        if self.entry_price <= 0:
            raise ValueError("진입 가격은 양수여야 합니다")


@dataclass(frozen=True)
class TakeProfitLevels(ValueObject):
    """Take-profit 레벨 VO.

    intrinsic_value와 entry_price 간 갭의 50%/75%/100%에서 분할 매도.
    """

    entry_price: float
    intrinsic_value: float

    @property
    def has_upside(self) -> bool:
        return self.intrinsic_value > self.entry_price

    @property
    def levels(self) -> list[dict]:
        """Take-profit 레벨 목록. 업사이드 없으면 빈 리스트."""
        if not self.has_upside:
            return []

        gap = self.intrinsic_value - self.entry_price
        return [
            {"pct": 0.50, "price": round(self.entry_price + gap * 0.50, 2), "action": "sell_25pct"},
            {"pct": 0.75, "price": round(self.entry_price + gap * 0.75, 2), "action": "sell_25pct"},
            {"pct": 1.00, "price": round(self.intrinsic_value, 2), "action": "sell_remaining"},
        ]

    def _validate(self) -> None:
        if self.entry_price <= 0:
            raise ValueError("진입 가격은 양수여야 합니다")
        if self.intrinsic_value <= 0:
            raise ValueError("내재 가치는 양수여야 합니다")
