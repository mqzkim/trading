"""Regime 도메인 — Entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.shared.domain import Entity
from .value_objects import RegimeType, VIXLevel, TrendStrength, YieldCurve, SP500Position
from .events import RegimeChangedEvent


@dataclass(eq=False)
class MarketRegime(Entity[str]):
    """시장 레짐 Aggregate.

    불변식:
    - confidence는 0.0~1.0 범위
    - 레짐 전환 확인 조건: 3일 연속 (confirmed_days >= 3)
    """
    _id: str
    regime_type: RegimeType
    confidence: float
    vix: VIXLevel
    trend: TrendStrength
    yield_curve: YieldCurve
    sp500: SP500Position
    confirmed_days: int = 0
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_confirmed(self) -> bool:
        """3일 연속 확인 = 레짐 확정."""
        return self.confirmed_days >= 3

    def transition_to(self, new_regime: RegimeType, confidence: float) -> "MarketRegime":
        """레짐 전환. 기존 레짐과 다를 경우만 이벤트 발행."""
        if new_regime == self.regime_type:
            return self

        event = RegimeChangedEvent(
            previous_regime=self.regime_type,
            new_regime=new_regime,
            confidence=confidence,
            vix_value=self.vix.value,
            adx_value=self.trend.adx,
        )
        self.add_domain_event(event)
        return MarketRegime(
            _id=self._id,
            regime_type=new_regime,
            confidence=confidence,
            vix=self.vix,
            trend=self.trend,
            yield_curve=self.yield_curve,
            sp500=self.sp500,
            confirmed_days=0,  # 새 레짐은 아직 미확정
        )
