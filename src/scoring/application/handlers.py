"""Scoring Application Layer — Handlers (유스케이스 조율).

ScoreSymbolHandler:
  1. 외부 데이터 조회 (Infrastructure 위임)
  2. Safety Gate 체크 (Domain Service)
  3. 3축 점수 계산 (기존 core/scoring/ 로직 활용)
  4. 복합 점수 산출 (Domain Service)
  5. 결과 저장 (Repository)
  6. 도메인 이벤트 발행
"""
from __future__ import annotations

from src.shared.domain import Ok, Err, Result
from src.scoring.domain import (
    FundamentalScore,
    TechnicalScore,
    SentimentScore,
    SafetyFilterService,
    CompositeScoringService,
    IScoreRepository,
    ScoreUpdatedEvent,
)
from .commands import ScoreSymbolCommand


class ScoringError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


class ScoreSymbolHandler:
    """단일 종목 스코어링 유스케이스.

    의존성 주입을 통해 외부 데이터 클라이언트와 Repository를 받는다.
    비즈니스 로직은 Domain Service에 위임.
    """

    def __init__(
        self,
        score_repo: IScoreRepository,
        # 데이터 클라이언트는 Infrastructure에서 주입
        fundamental_client=None,
        technical_client=None,
        sentiment_client=None,
    ):
        self._score_repo = score_repo
        self._safety = SafetyFilterService()
        self._composite = CompositeScoringService()
        self._fundamental_client = fundamental_client
        self._technical_client = technical_client
        self._sentiment_client = sentiment_client

    def handle(self, cmd: ScoreSymbolCommand) -> Result:
        """
        Returns:
            Ok({'symbol', 'composite_score', 'risk_adjusted_score', 'safety_passed', ...})
            Err(ScoringError)
        """
        symbol = cmd.symbol.upper()

        # 1. 외부 데이터 조회 (Infrastructure 담당)
        #    현재는 기존 core/scoring/ 로직을 직접 호출 (점진적 이전)
        try:
            fundamental_data = self._get_fundamental(symbol)
            technical_data = self._get_technical(symbol)
            sentiment_data = self._get_sentiment(symbol)
        except Exception as e:
            return Err(ScoringError(f"Data fetch failed: {e}", "DATA_FETCH_ERROR"))

        # 2. Safety Gate 체크 (Domain Service)
        z_score = fundamental_data.get("z_score")
        m_score = fundamental_data.get("m_score")
        is_safe = self._safety.is_safe(z_score, m_score)

        # Safety Gate 탈락 → zero 점수 반환
        if not is_safe:
            result = {
                "symbol": symbol,
                "safety_passed": False,
                "composite_score": 0,
                "risk_adjusted_score": 0,
                "z_score": z_score,
                "m_score": m_score,
            }
            return Ok(result)

        # 3. Value Objects 생성 (Domain 레이어)
        fundamental = FundamentalScore(
            value=fundamental_data.get("fundamental_score", 50),
            f_score=fundamental_data.get("f_score"),
            z_score=z_score,
            m_score=m_score,
        )
        technical = TechnicalScore(value=technical_data.get("technical_score", 50))
        sentiment = SentimentScore(value=sentiment_data.get("sentiment_score", 50))

        # 4. 복합 점수 산출 (Domain Service)
        composite = self._composite.compute(
            fundamental=fundamental,
            technical=technical,
            sentiment=sentiment,
            strategy=cmd.strategy,
            tail_risk_penalty=cmd.tail_risk_penalty,
            g_score=fundamental_data.get("g_score"),
            is_growth_stock=fundamental_data.get("is_growth_stock", False),
        )

        # 5. 결과 저장 (Repository)
        self._score_repo.save(symbol, composite)

        # 6. 도메인 이벤트 생성 (bus publish는 Plan 03에서 wiring)
        event = ScoreUpdatedEvent(
            symbol=symbol,
            composite_score=composite.value,
            risk_adjusted_score=composite.risk_adjusted,
            safety_passed=True,
            strategy=composite.strategy,
        )

        result = {
            "symbol": symbol,
            "safety_passed": True,
            "composite_score": composite.value,
            "risk_adjusted_score": composite.risk_adjusted,
            "strategy": composite.strategy,
            "fundamental_score": fundamental.value,
            "technical_score": technical.value,
            "sentiment_score": sentiment.value,
            "f_score": fundamental.f_score,
            "z_score": fundamental.z_score,
            "m_score": fundamental.m_score,
            "event": event,
        }
        return Ok(result)

    # ── Infrastructure 위임 (점진적 이전) ─────────────────────────

    def _get_fundamental(self, symbol: str) -> dict:
        """기존 core/scoring/fundamental.py 호출 (임시)."""
        if self._fundamental_client:
            return self._fundamental_client.get(symbol)
        # Fallback: 기존 로직 직접 import
        from core.scoring.fundamental import compute_fundamental_score  # type: ignore[import-untyped]
        return compute_fundamental_score(symbol)  # type: ignore[arg-type, call-arg]

    def _get_technical(self, symbol: str) -> dict:
        if self._technical_client:
            return self._technical_client.get(symbol)
        from core.scoring.technical import compute_technical_score  # type: ignore[import-untyped]
        return compute_technical_score(symbol)  # type: ignore[call-arg]

    def _get_sentiment(self, symbol: str) -> dict:
        if self._sentiment_client:
            return self._sentiment_client.get(symbol)
        from core.scoring.sentiment import compute_sentiment_score  # type: ignore[import-untyped]
        return compute_sentiment_score(symbol)  # type: ignore[arg-type]
