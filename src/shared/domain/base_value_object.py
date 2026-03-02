"""Base Value Object — DDD Value Object 기반 클래스."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)  # frozen=True → 불변 강제
class ValueObject(ABC):
    """
    식별자 없이 속성 값으로 동일성을 판단하는 불변 객체.

    규칙:
    - frozen=True 유지 (변경 불가)
    - 생성 시 __post_init__에서 불변식(invariant) 검증
    - 변경이 필요하면 새 인스턴스를 생성
    """

    def __post_init__(self) -> None:
        self._validate()

    @abstractmethod
    def _validate(self) -> None:
        """불변식 검증. 위반 시 ValueError 발생."""
        ...
