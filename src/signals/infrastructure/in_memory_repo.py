"""Signals Infrastructure — InMemory Repository (테스트 전용)."""
from __future__ import annotations

from typing import Optional

from src.signals.domain import ISignalRepository


class InMemorySignalRepository(ISignalRepository):
    """메모리 기반 시그널 저장소.

    프로세스 재시작 시 데이터가 소멸한다.
    단위 테스트 및 로컬 개발 환경 전용으로만 사용한다.
    """

    def __init__(self) -> None:
        self._active: dict[str, dict] = {}  # symbol -> signal dict

    # ── ISignalRepository 구현 ─────────────────────────────────────

    def save(self, symbol: str, direction: str, strength: float, metadata: dict) -> None:
        """심볼의 시그널을 덮어쓴다 (기존 항목 자동 만료)."""
        self._active[symbol] = {
            "symbol": symbol,
            "direction": direction,
            "strength": strength,
            "metadata": metadata,
            "is_active": 1,
        }

    def find_active(self, symbol: str) -> Optional[dict]:
        """심볼의 활성 시그널을 반환. 없으면 None."""
        return self._active.get(symbol)

    def find_all_active(self) -> list[dict]:
        """BUY 또는 SELL 방향의 모든 활성 시그널을 반환."""
        return [
            v for v in self._active.values()
            if v.get("direction") in ("BUY", "SELL")
        ]
