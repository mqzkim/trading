"""Result 패턴 — 예외 대신 명시적 성공/실패 타입."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> T:  # type: ignore
        raise self.error


# 사용 예:
# result: Result[CompositeScore, ScoringError] = scoring_service.score(symbol)
# if result.is_ok():
#     score = result.unwrap()
Result = Ok | Err
