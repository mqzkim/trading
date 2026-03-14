"""Scoring Infrastructure — InMemory Repository (테스트용)."""
from __future__ import annotations

from typing import Optional

from src.scoring.domain import IScoreRepository
from src.scoring.domain.value_objects import CompositeScore


class InMemoryScoreRepository(IScoreRepository):
    """메모리 기반 스코어 저장소. 단위 테스트 전용."""

    def __init__(self) -> None:
        # symbol -> CompositeScore (최신 1개만 보관)
        self._store: dict[str, CompositeScore] = {}

    # ── IScoreRepository 구현 ─────────────────────────────────────

    def save(self, symbol: str, score: CompositeScore, details: dict | None = None) -> None:
        self._store[symbol] = score

    def find_latest(self, symbol: str) -> Optional[CompositeScore]:
        return self._store.get(symbol)

    def find_all_latest(self, limit: int = 100) -> dict[str, CompositeScore]:
        sorted_items = sorted(
            self._store.items(),
            key=lambda kv: kv[1].value,
            reverse=True,
        )
        return dict(sorted_items[:limit])
