"""Scoring 도메인 — Value Objects.

불변 규칙:
  SafetyGate: Z-Score > 1.81 AND M-Score < -1.78 (DOMAIN.md 참조)
  CompositeScore: 0-100 범위
  전략별 가중치: WEIGHTS 딕셔너리 (임의 변경 금지)
"""
from __future__ import annotations

from dataclasses import dataclass
from src.shared.domain import ValueObject

# 전략별 가중치 — 변경 불가 (검증된 배분)
STRATEGY_WEIGHTS: dict[str, dict[str, float]] = {
    "swing":    {"fundamental": 0.35, "technical": 0.40, "sentiment": 0.25},
    "position": {"fundamental": 0.50, "technical": 0.30, "sentiment": 0.20},
}
DEFAULT_STRATEGY = "swing"


@dataclass(frozen=True)
class Symbol(ValueObject):
    """주식 종목 코드."""
    ticker: str

    def _validate(self) -> None:
        if not self.ticker or not self.ticker.isupper():
            raise ValueError(f"Invalid ticker: {self.ticker!r}. Must be uppercase.")
        if len(self.ticker) > 10:
            raise ValueError(f"Ticker too long: {self.ticker!r}")


@dataclass(frozen=True)
class FundamentalScore(ValueObject):
    """기본적 분석 점수 (0-100).

    구성: Piotroski F-Score, Altman Z-Score, Beneish M-Score, G-Score
    """
    value: float
    f_score: float | None = None    # Piotroski (0-9)
    z_score: float | None = None    # Altman
    m_score: float | None = None    # Beneish

    def _validate(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(f"FundamentalScore must be 0-100, got {self.value}")


@dataclass(frozen=True)
class TechnicalScore(ValueObject):
    """기술적 분석 점수 (0-100).

    구성: 200MA 추세, RSI, MACD, OBV
    """
    value: float

    def _validate(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(f"TechnicalScore must be 0-100, got {self.value}")


@dataclass(frozen=True)
class SentimentScore(ValueObject):
    """센티먼트 점수 (0-100).

    구성: 뉴스 감성, 내부자 거래, 애널리스트 추정치
    중립 기본값: 50
    """
    value: float

    def _validate(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(f"SentimentScore must be 0-100, got {self.value}")


@dataclass(frozen=True)
class SafetyGate(ValueObject):
    """안전성 필터 — 파산/회계조작 위험 차단.

    통과 조건 (변경 불가):
      Altman Z-Score > 1.81  (파산 위험 없음)
      Beneish M-Score < -1.78  (회계 조작 없음)
    """
    z_score: float | None
    m_score: float | None

    # 불변 임계값 — 학술 검증값
    Z_SCORE_THRESHOLD: float = 1.81
    M_SCORE_THRESHOLD: float = -1.78

    def _validate(self) -> None:
        pass  # None 허용 (데이터 부족 시 통과 처리)

    @property
    def passed(self) -> bool:
        """안전성 필터 통과 여부."""
        if self.z_score is not None and self.z_score <= self.Z_SCORE_THRESHOLD:
            return False
        if self.m_score is not None and self.m_score >= self.M_SCORE_THRESHOLD:
            return False
        return True


@dataclass(frozen=True)
class CompositeScore(ValueObject):
    """전략별 가중 복합 점수 (0-100).

    risk_adjusted_score = composite - 0.3 * tail_risk_penalty
    """
    value: float                    # 복합 점수
    risk_adjusted: float            # 꼬리위험 조정 점수
    strategy: str = DEFAULT_STRATEGY
    weights: dict[str, float] | None = None

    def _validate(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(f"CompositeScore must be 0-100, got {self.value}")
        if not 0 <= self.risk_adjusted <= 100:
            raise ValueError(f"risk_adjusted must be 0-100, got {self.risk_adjusted}")
        if self.strategy not in STRATEGY_WEIGHTS:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    @classmethod
    def compute(
        cls,
        fundamental: FundamentalScore,
        technical: TechnicalScore,
        sentiment: SentimentScore,
        strategy: str = DEFAULT_STRATEGY,
        tail_risk_penalty: float = 0.0,
    ) -> "CompositeScore":
        """가중 합산으로 복합 점수 계산."""
        w = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS[DEFAULT_STRATEGY])
        raw = (
            w["fundamental"] * fundamental.value
            + w["technical"] * technical.value
            + w["sentiment"] * sentiment.value
        )
        raw = max(0.0, min(100.0, raw))
        risk_adj = max(0.0, min(100.0, raw - 0.3 * tail_risk_penalty))
        return cls(
            value=round(raw, 1),
            risk_adjusted=round(risk_adj, 1),
            strategy=strategy,
            weights=w,
        )
