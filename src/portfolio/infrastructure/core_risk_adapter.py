"""Portfolio Infrastructure — CoreRiskAdapter.

personal/sizer/kelly 및 personal/risk/drawdown 래핑.
수학 재구현 없이 위임(delegation)만 수행.
"""
from __future__ import annotations

from personal.risk.drawdown import assess_drawdown
from personal.sizer.kelly import (
    atr_position_size,
    kelly_fraction,
    validate_position,
)


class CoreRiskAdapter:
    """personal/ 모듈의 리스크 계산을 DDD 포트폴리오 컨텍스트에 노출하는 어댑터."""

    def compute_kelly(
        self, win_rate: float, avg_win: float, avg_loss: float
    ) -> float:
        """Fractional Kelly (1/4) 비율 계산. personal/sizer/kelly 위임."""
        return kelly_fraction(win_rate, avg_win, avg_loss)

    def compute_atr_stop(
        self,
        capital: float,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 3.0,
    ) -> dict:
        """ATR 기반 포지션 사이징. personal/sizer/kelly 위임."""
        return atr_position_size(capital, entry_price, atr, atr_multiplier)

    def validate_position(
        self,
        position_value: float,
        capital: float,
        sector_exposure: float = 0.0,
    ) -> dict:
        """포지션 한도 검증. personal/sizer/kelly 위임."""
        return validate_position(position_value, capital, sector_exposure)

    def assess_drawdown(
        self,
        peak_value: float,
        current_value: float,
        cooldown_days_remaining: int = 0,
    ) -> dict:
        """낙폭 수준 평가. personal/risk/drawdown 위임."""
        return assess_drawdown(peak_value, current_value, cooldown_days_remaining)
