"""Portfolio Application Layer — Commands."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OpenPositionCommand:
    """포지션 진입 명령."""

    symbol: str
    entry_price: float
    portfolio_id: str
    strategy: str = "swing"         # "swing" | "position"
    sector: str = "unknown"
    win_rate: float = 0.55          # Kelly 계산용
    win_loss_ratio: float = 2.0     # 평균 수익/손실 비율
    atr: Optional[float] = None     # ATR(21), None이면 stop 없음
    atr_multiplier: float = 2.5


@dataclass(frozen=True)
class ClosePositionCommand:
    """포지션 청산 명령."""

    symbol: str
    portfolio_id: str
    exit_price: float


@dataclass(frozen=True)
class GetPortfolioQuery:
    """포트폴리오 현황 조회."""

    portfolio_id: str


@dataclass(frozen=True)
class GetPositionsQuery:
    """포지션 목록 조회."""

    portfolio_id: str
