"""Signals 도메인 — Value Objects.

불변 규칙:
  합의 시그널: 4방법론 중 3개 이상 일치 (3/4 합의)
  BUY 조건: CompositeScore >= 60 + SafetyGate 통과
  SELL 조건: CompositeScore < 30 또는 3개 이상 SELL
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from src.shared.domain import ValueObject


class SignalDirection(Enum):
    """매매 방향."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class MethodologyType(Enum):
    """4가지 검증된 방법론 (변경 불가)."""
    CAN_SLIM = "CAN_SLIM"
    MAGIC_FORMULA = "MAGIC_FORMULA"
    DUAL_MOMENTUM = "DUAL_MOMENTUM"
    TREND_FOLLOWING = "TREND_FOLLOWING"


@dataclass(frozen=True)
class MethodologyResult(ValueObject):
    """단일 방법론의 시그널 결과."""
    methodology: MethodologyType
    direction: SignalDirection
    score: float        # 해당 방법론의 신호 강도 (0-100)
    reason: str = ""    # 판단 근거 (디버깅용)

    def _validate(self) -> None:
        if not 0 <= self.score <= 100:
            raise ValueError(f"Methodology score must be 0-100, got {self.score}")


@dataclass(frozen=True)
class ConsensusThreshold(ValueObject):
    """합의 임계값 — 기본 3/4 방법론."""
    required_count: int = 3   # 필요한 동의 방법론 수
    total_count: int = 4      # 전체 방법론 수

    def _validate(self) -> None:
        if not 1 <= self.required_count <= self.total_count:
            raise ValueError(
                f"required_count({self.required_count}) must be 1~{self.total_count}"
            )

    @property
    def ratio(self) -> float:
        return self.required_count / self.total_count


@dataclass(frozen=True)
class SignalStrength(ValueObject):
    """시그널 강도 (0-100) + 합의 에이전트 수."""
    value: float
    consensus_count: int   # 동의한 방법론 수
    total_count: int = 4

    def _validate(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(f"SignalStrength must be 0-100, got {self.value}")
        if not 0 <= self.consensus_count <= self.total_count:
            raise ValueError("consensus_count out of range")

    @property
    def consensus_ratio(self) -> float:
        return self.consensus_count / self.total_count

    @property
    def is_strong(self) -> bool:
        return self.value >= 70 and self.consensus_count >= 3
