"""Signals Application Layer — Queries."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class GetActiveSignalQuery:
    """종목의 활성 시그널 조회."""
    symbol: str


@dataclass(frozen=True)
class GetSignalHistoryQuery:
    """종목의 시그널 이력 조회."""
    symbol: str
    limit: int = 10
