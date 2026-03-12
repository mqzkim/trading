"""Signals Application Layer — Commands."""
from __future__ import annotations
from dataclasses import dataclass


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
    # 밸류에이션 갭 (valuation context에서 전달, 기본 0.0)
    margin_of_safety: float = 0.0
    # 시장 데이터 (CoreSignalAdapter로 전달)
    symbol_data: dict | None = None
    # 현재 시장 레짐 ("Bull"/"Bear"/"Sideways"/"Crisis" 또는 None)
    regime_type: str | None = None


@dataclass(frozen=True)
class BatchSignalCommand:
    """종목 리스트 시그널 생성 명령."""
    symbols: tuple[str, ...]
    methodologies: tuple[str, ...] = ("can_slim", "magic_formula", "dual_momentum", "trend_following")
    max_workers: int = 4
