# Regime — 시장 레짐 분석 바운디드 컨텍스트

## 책임

현재 시장 상태(Bull/Bear/Sideways/Crisis)를 판별하고, 레짐 전환 신호를 감지한다.
다른 컨텍스트(Scoring, Signals)에 레짐 정보를 이벤트로 제공하여 전략 가중치 조정을 가능하게 한다.

## 핵심 엔티티

| 객체 | 종류 | 설명 |
|------|------|------|
| `MarketRegime` | Aggregate | 현재 레짐 상태 + 전환 확률 보유 |
| `RegimeType` | Value Object | Bull / Bear / Sideways / Crisis (4가지) |
| `VIXLevel` | Value Object | 공포 지수 측정값 (임계값: 20, 30, 40) |
| `TrendStrength` | Value Object | ADX 기반 추세 강도 (0-100) |
| `YieldCurve` | Value Object | 장단기 금리차 (10Y-2Y) |

## 도메인 서비스

| 서비스 | 역할 |
|--------|------|
| `RegimeDetectionService` | 4가지 지표 종합 → 레짐 판별 |
| `RegimeTransitionService` | 레짐 전환 확률 계산 |

## 외부 의존성

- **수신 이벤트**: `MarketDataUpdatedEvent` ← Data Ingest 컨텍스트
- **발행 이벤트**: `RegimeChangedEvent` → Scoring, Signals 컨텍스트
- **외부 API**: yfinance (VIX, S&P 500, 금리 데이터)

## 주요 유스케이스

1. **DetectCurrentRegime**: VIX + 200MA + ADX + 금리차 → 레짐 판별
2. **GetRegimeHistory**: 과거 레짐 이력 조회
3. **MonitorRegimeTransition**: 레짐 전환 임박 감지 + 알림

## 레짐 판별 기준 (변경 불가 비즈니스 규칙)

```
Bull:     VIX < 20  AND  S&P > 200MA  AND  ADX > 25  AND  YieldCurve > 0
Bear:     VIX > 30  AND  S&P < 200MA
Sideways: ADX < 20 (추세 없음)
Crisis:   VIX > 40  OR  YieldCurve < -0.5 (심각한 역전)
```

## 변경 불가 규칙

- VIX 기준값(20/30/40)은 학술 검증값 — 임의 변경 금지
- S&P 500 200일 이동평균 기준은 고정
- 레짐 전환은 3일 연속 확인 후 확정 (하루 변동으로 전환 금지)
- 레짐 판별 결과는 반드시 SQLite에 기록 (감사 추적)

## 현재 구현 위치

```
core/regime/__init__.py → 레짐 판별 로직 (향후 src/regime/domain/services.py로 이전)
```

## DDD 목표 구조

```
src/regime/
  domain/
    entities.py          # MarketRegime entity
    value_objects.py     # RegimeType, VIXLevel, TrendStrength, YieldCurve
    events.py            # RegimeChangedEvent
    services.py          # RegimeDetectionService
    repositories.py      # IRegimeRepository (ABC)
    __init__.py
  application/
    commands.py          # DetectRegimeCommand
    queries.py           # GetCurrentRegimeQuery, GetRegimeHistoryQuery
    handlers.py          # DetectRegimeHandler, GetRegimeHistoryHandler
    __init__.py
  infrastructure/
    persistence.py       # SQLiteRegimeRepository
    external.py          # YFinanceRegimeDataClient
    __init__.py
```
