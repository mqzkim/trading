# Signals — 매매 시그널 바운디드 컨텍스트

## 책임

4가지 검증된 방법론(CAN SLIM, Magic Formula, Dual Momentum, Trend Following)을 동시 실행하여 합의(Consensus) 시그널을 생성한다.
Scoring 컨텍스트의 스코어와 Regime 컨텍스트의 레짐 정보를 결합하여 최종 매매 시그널을 산출한다.

## 핵심 엔티티

| 객체 | 종류 | 설명 |
|------|------|------|
| `TradeSignal` | Aggregate | 최종 매매 시그널 (방향 + 강도 + 합의율) |
| `SignalDirection` | Value Object | BUY / SELL / HOLD |
| `SignalStrength` | Value Object | 0-100 강도 + 합의 에이전트 수 |
| `MethodologyResult` | Value Object | 단일 방법론의 시그널 결과 |
| `ConsensusThreshold` | Value Object | 합의 임계값 (기본: 3/4 방법론) |

## 도메인 서비스

| 서비스 | 역할 |
|--------|------|
| `SignalFusionService` | 4가지 방법론 결과 → 합의 시그널 |
| `RegimeWeightingService` | 레짐에 따른 방법론 가중치 조정 |
| `SignalValidationService` | 시그널 품질 검증 (IC 계산) |

## 4가지 방법론 (변경 불가)

| 방법론 | 핵심 지표 | 선택 기준 |
|--------|-----------|-----------|
| CAN SLIM | 실적 성장 + 기관 매수 | Bull 레짐 최적 |
| Magic Formula | 고ROC + 저EV/EBIT | 전 레짐 유효 |
| Dual Momentum | 절대/상대 모멘텀 | 추세 전환 감지 |
| Trend Following | 200MA + ATR | Bear/Crisis 생존 |

## 외부 의존성

- **수신 이벤트**: `ScoreUpdatedEvent` ← Scoring 컨텍스트
- **수신 이벤트**: `RegimeChangedEvent` ← Regime 컨텍스트
- **발행 이벤트**: `SignalGeneratedEvent` → Portfolio 컨텍스트

## 주요 유스케이스

1. **GenerateSignals**: 스코어 + 레짐 → 4방법론 동시 실행 → 합의 시그널
2. **GetActiveSignals**: 현재 유효한 시그널 목록 조회
3. **ValidateSignalIC**: 시그널 IC(Information Coefficient) 검증 (>= 0.03)

## 합의 시그널 기준 (변경 불가)

```
BUY 시그널 발생 조건:
  - 4가지 방법론 중 3개 이상 BUY
  - CompositeScore >= 60
  - SafetyGate 통과

SELL 시그널 발생 조건:
  - 4가지 방법론 중 3개 이상 SELL
  - 또는 CompositeScore < 30

HOLD:
  - 합의 미달 또는 중간 구간
```

## 시그널 유효 기간

- 스윙 트레이딩: 2주
- 포지션 트레이딩: 1개월

## DDD 목표 구조

```
src/signals/
  domain/
    entities.py          # TradeSignal entity
    value_objects.py     # SignalDirection, SignalStrength, MethodologyResult, ConsensusThreshold
    events.py            # SignalGeneratedEvent
    services.py          # SignalFusionService, RegimeWeightingService
    repositories.py      # ISignalRepository (ABC)
    __init__.py
  application/
    commands.py          # GenerateSignalsCommand
    queries.py           # GetActiveSignalsQuery
    handlers.py          # GenerateSignalsHandler
    __init__.py
  infrastructure/
    persistence.py       # SQLiteSignalRepository
    methodologies/       # CAN SLIM, Magic Formula, Dual Momentum, Trend Following 구현
    __init__.py
```
