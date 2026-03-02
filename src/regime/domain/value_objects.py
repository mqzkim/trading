"""Regime 도메인 — Value Objects.

불변 규칙:
  VIX 임계값(20/30/40)은 학술 검증값 — 임의 변경 금지
  RegimeType은 4가지만 존재 (DOMAIN.md 참조)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from src.shared.domain import ValueObject


class RegimeType(Enum):
    """시장 레짐 유형. 4가지 고정값."""
    BULL = "Bull"
    BEAR = "Bear"
    SIDEWAYS = "Sideways"
    CRISIS = "Crisis"


@dataclass(frozen=True)
class VIXLevel(ValueObject):
    """공포 지수(VIX) 측정값.

    불변 임계값:
      < 20: 낮음 (Bull 구간)
      20-30: 보통
      30-40: 높음 (Bear 구간)
      > 40: 극단적 (Crisis 구간)
    """
    value: float

    def _validate(self) -> None:
        if self.value < 0:
            raise ValueError(f"VIX cannot be negative: {self.value}")

    @property
    def is_low(self) -> bool:
        return self.value < 20

    @property
    def is_elevated(self) -> bool:
        return 20 <= self.value < 30

    @property
    def is_high(self) -> bool:
        return 30 <= self.value < 40

    @property
    def is_extreme(self) -> bool:
        return self.value >= 40


@dataclass(frozen=True)
class TrendStrength(ValueObject):
    """ADX 기반 추세 강도 (0-100).

    ADX < 20: 추세 없음 (Sideways)
    ADX > 25: 강한 추세
    """
    adx: float

    def _validate(self) -> None:
        if not 0 <= self.adx <= 100:
            raise ValueError(f"ADX must be 0-100, got {self.adx}")

    @property
    def has_trend(self) -> bool:
        return self.adx >= 20

    @property
    def is_strong_trend(self) -> bool:
        return self.adx >= 25


@dataclass(frozen=True)
class YieldCurve(ValueObject):
    """장단기 금리차 (10Y - 2Y).

    역전(음수): 경기침체 신호
    -0.5 이하: Crisis 조건
    """
    spread: float  # 10Y - 2Y (%)

    def _validate(self) -> None:
        if not -10 <= self.spread <= 10:
            raise ValueError(f"Yield curve spread out of range: {self.spread}")

    @property
    def is_inverted(self) -> bool:
        return self.spread < 0

    @property
    def is_severely_inverted(self) -> bool:
        return self.spread < -0.5


@dataclass(frozen=True)
class SP500Position(ValueObject):
    """S&P 500 현재가 대비 200일 이동평균 상대 위치."""
    current_price: float
    ma_200: float

    def _validate(self) -> None:
        if self.current_price <= 0 or self.ma_200 <= 0:
            raise ValueError("Prices must be positive")

    @property
    def is_above_ma200(self) -> bool:
        return self.current_price > self.ma_200

    @property
    def deviation_pct(self) -> float:
        """현재가의 200MA 대비 편차 (%)."""
        return (self.current_price - self.ma_200) / self.ma_200 * 100
