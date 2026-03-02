"""Regime Application Layer — Commands."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class DetectRegimeCommand:
    """현재 시장 레짐 감지 명령."""
    # 외부 데이터 직접 전달 (인프라에서 미리 조회)
    vix: float
    sp500_price: float
    sp500_ma200: float
    adx: float
    yield_spread: float  # 10Y - 2Y


@dataclass(frozen=True)
class GetRegimeQuery:
    """최근 레짐 조회."""
    limit: int = 1
