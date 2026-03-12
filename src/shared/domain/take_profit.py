"""Shared Domain — TakeProfitLevels Value Object.

Moved from portfolio/domain/value_objects.py to shared kernel
to allow execution/domain to use it without cross-context import violation.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain import ValueObject


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
