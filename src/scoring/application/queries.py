"""Scoring Application Layer — Queries (조회 요청)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GetLatestScoreQuery:
    """캐시된 최신 스코어 조회."""
    symbol: str


@dataclass(frozen=True)
class GetTopScoredQuery:
    """상위 스코어 종목 목록 조회."""
    limit: int = 20
    strategy: str = "swing"
    min_score: float = 60.0   # 최소 복합 점수
