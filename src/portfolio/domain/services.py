"""Portfolio 도메인 — Domain Services.

순수 도메인 로직. 인프라 의존성 없음.
"""
from __future__ import annotations

from .aggregates import DRAWDOWN_CAUTION, DRAWDOWN_CRITICAL, DRAWDOWN_WARNING
from .value_objects import ATRStop, DrawdownLevel, KellyFraction


class PortfolioRiskService:
    """포트폴리오 리스크 서비스.

    - Fractional Kelly 포지션 사이징 (1/4 고정, Full Kelly 금지)
    - ATR 기반 스탑로스 계산
    - 낙폭 수준 평가 및 대응 지침 제공
    """

    def compute_kelly_size(
        self,
        win_rate: float,
        win_loss_ratio: float,
        portfolio_value: float,
        price: float,
    ) -> dict:
        """Fractional Kelly 기반 포지션 크기 계산.

        Full Kelly = win_rate - (1 - win_rate) / win_loss_ratio
        Fractional Kelly = Full Kelly * 0.25 (1/4 고정)
        Kelly < 0 이면 투자 안 함 (shares=0).
        """
        if win_loss_ratio <= 0 or price <= 0 or portfolio_value <= 0:
            return {"shares": 0, "weight": 0.0, "kelly": 0.0, "full_kelly": 0.0}

        full_kelly = win_rate - (1 - win_rate) / win_loss_ratio
        full_kelly = max(0.0, full_kelly)

        fraction = KellyFraction(full_kelly=full_kelly)
        position_value = portfolio_value * fraction.value
        shares = int(position_value / price)

        return {
            "shares": shares,
            "weight": fraction.value,
            "kelly": fraction.value,
            "full_kelly": full_kelly,
        }

    def compute_atr_stop(
        self,
        entry_price: float,
        atr: float,
        multiplier: float = 2.5,
    ) -> ATRStop:
        """ATR 기반 스탑로스 생성.

        multiplier: 2.5~3.5 (ATR(21) 기준, 기본 2.5x)
        """
        return ATRStop(entry_price=entry_price, atr=atr, multiplier=multiplier)

    def assess_drawdown_defense(self, drawdown: float) -> dict:
        """낙폭 수준 평가 및 대응 지침 반환.

        Returns:
            level: DrawdownLevel 문자열
            action: 권장 조치
            can_open: 신규 진입 가능 여부
            reduce_pct: 축소 비율 (0, 50, 100)
        """
        if drawdown >= DRAWDOWN_CRITICAL:
            return {
                "level": DrawdownLevel.CRITICAL.value,
                "action": "전량 청산 후 최소 1개월 냉각기",
                "can_open": False,
                "reduce_pct": 100,
            }
        if drawdown >= DRAWDOWN_WARNING:
            return {
                "level": DrawdownLevel.WARNING.value,
                "action": "포지션 50% 축소, 방어적 전환",
                "can_open": False,
                "reduce_pct": 50,
            }
        if drawdown >= DRAWDOWN_CAUTION:
            return {
                "level": DrawdownLevel.CAUTION.value,
                "action": "신규 진입 중단, 모니터링 강화",
                "can_open": False,
                "reduce_pct": 0,
            }
        return {
            "level": DrawdownLevel.NORMAL.value,
            "action": "정상 운용",
            "can_open": True,
            "reduce_pct": 0,
        }
