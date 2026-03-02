# Scoring — 종목 스코어링 바운디드 컨텍스트

## 책임

주식 종목에 대해 기본적(Fundamental) + 기술적(Technical) + 센티먼트(Sentiment) 분석을 수행하여 0-100 복합 스코어를 산출한다.
안전성 게이트(Safety Gate)를 통과한 종목만 스코어링 결과를 Signals 컨텍스트에 제공한다.

## 핵심 엔티티

| 객체 | 종류 | 설명 |
|------|------|------|
| `ScoringResult` | Aggregate | 종목 스코어링 최종 결과 (복합 + 3축 분해) |
| `Symbol` | Value Object | 주식 종목 코드 (예: "AAPL") |
| `CompositeScore` | Value Object | 0-100 복합 점수 + 전략별 가중치 |
| `FundamentalScore` | Value Object | Piotroski F-Score, Altman Z-Score 기반 |
| `TechnicalScore` | Value Object | 200MA, RSI, MACD, OBV 기반 |
| `SentimentScore` | Value Object | 뉴스 감성, 내부자 거래, 애널리스트 추정치 |
| `SafetyGate` | Value Object | Z-Score > 1.81 AND M-Score < -1.78 통과 여부 |

## 도메인 서비스

| 서비스 | 역할 |
|--------|------|
| `CompositeScoringService` | 3축 점수 → 복합 점수 계산 |
| `SafetyFilterService` | 안전성 필터 판정 (Z-Score, M-Score) |
| `SectorNormalizationService` | 섹터 중립 정규화 |

## 전략별 가중치 (변경 불가 비즈니스 규칙)

```python
WEIGHTS = {
    "swing":    {"fundamental": 0.35, "technical": 0.40, "sentiment": 0.25},
    "position": {"fundamental": 0.50, "technical": 0.30, "sentiment": 0.20},
}
```

## 외부 의존성

- **수신 이벤트**: `RegimeChangedEvent` ← Regime 컨텍스트 (가중치 조정용)
- **발행 이벤트**: `ScoreUpdatedEvent` → Signals 컨텍스트
- **외부 API**: yfinance, EODHD (재무 데이터)

## 주요 유스케이스

1. **ScoreSymbol**: 단일 종목 전체 스코어링 파이프라인 실행
2. **BatchScoreSymbols**: 종목 리스트 병렬 스코어링
3. **GetLatestScore**: 캐시된 최신 스코어 조회

## 안전성 필터 기준 (변경 불가)

```
통과 조건:
  Altman Z-Score > 1.81  (파산 위험 없음)
  Beneish M-Score < -1.78  (회계 조작 없음)

탈락 시:
  composite_score = 0
  risk_adjusted_score = 0
  (Signals 컨텍스트에 zero 점수 전달)
```

## 현재 구현 위치

```
core/scoring/composite.py   → 복합 점수 계산
core/scoring/fundamental.py → 기본적 분석
core/scoring/technical.py   → 기술적 분석
core/scoring/sentiment.py   → 센티먼트 분석
core/scoring/safety.py      → 안전성 필터
```

## DDD 목표 구조

```
src/scoring/
  domain/
    entities.py          # ScoringResult entity
    value_objects.py     # CompositeScore, FundamentalScore, TechnicalScore, SentimentScore, SafetyGate
    events.py            # ScoreUpdatedEvent
    services.py          # CompositeScoringService, SafetyFilterService
    repositories.py      # IScoreRepository (ABC)
    __init__.py
  application/
    commands.py          # ScoreSymbolCommand, BatchScoreCommand
    queries.py           # GetLatestScoreQuery
    handlers.py          # ScoreSymbolHandler, GetLatestScoreHandler
    __init__.py
  infrastructure/
    persistence.py       # SQLiteScoreRepository
    external.py          # YFinanceDataClient, EODHDClient
    __init__.py
```
