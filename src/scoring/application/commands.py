"""Scoring Application Layer — Commands (상태 변경 요청)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreSymbolCommand:
    """단일 종목 스코어링 명령."""
    symbol: str
    strategy: str = "swing"
    tail_risk_penalty: float = 0.0


@dataclass(frozen=True)
class BatchScoreCommand:
    """종목 리스트 스코어링 명령."""
    symbols: tuple[str, ...]
    strategy: str = "swing"
    max_workers: int = 4   # 병렬 실행 워커 수
