"""Signals Application Layer — Commands."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GenerateSignalCommand:
    """단일 종목 시그널 생성 명령."""
    symbol: str
    # 실행할 방법론 목록. 기본: 4가지 전부
    methodologies: tuple[str, ...] = ("can_slim", "magic_formula", "dual_momentum", "trend_following")
    # 안전 게이트 통과 여부 (Infrastructure에서 주입, 기본 True)
    safety_passed: bool = True
    # 복합 점수 (None이면 방법론 평균 사용)
    composite_score: float | None = None


@dataclass(frozen=True)
class BatchSignalCommand:
    """종목 리스트 시그널 생성 명령."""
    symbols: tuple[str, ...]
    methodologies: tuple[str, ...] = ("can_slim", "magic_formula", "dual_momentum", "trend_following")
    max_workers: int = 4
