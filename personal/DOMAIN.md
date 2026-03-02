# Portfolio — 개인 포트폴리오 관리 바운디드 컨텍스트

## 책임

매매 시그널을 받아 포지션 크기 결정, 리스크 검증, 주문 실행까지 전체 포트폴리오 라이프사이클을 관리한다.
**개인 전용 — 상업 제품(commercial/)에서 절대 재사용 금지** (투자 자문 라이센스 문제).

## 핵심 엔티티

| 객체 | 종류 | 설명 |
|------|------|------|
| `Portfolio` | Aggregate | 전체 포트폴리오 상태 (포지션 + 현금 + 낙폭) |
| `Position` | Entity | 개별 종목 포지션 (수량, 진입가, 현재가) |
| `PortfolioId` | Value Object | 포트폴리오 식별자 |
| `KellyFraction` | Value Object | Fractional Kelly 비율 (기본 1/4) |
| `ATRStop` | Value Object | ATR 기반 스탑로스 (2.5-3.5x ATR(21)) |
| `DrawdownLevel` | Value Object | 낙폭 단계 (10% / 15% / 20%) |
| `RiskBudget` | Value Object | 종목별/섹터별 리스크 한도 |

## 도메인 서비스

| 서비스 | 역할 |
|--------|------|
| `PositionSizingService` | Fractional Kelly + ATR 기반 포지션 크기 결정 |
| `RiskValidationService` | 종목/섹터 한도 검증 + 낙폭 방어 트리거 |
| `DrawdownDefenseService` | 낙폭 단계별 방어 전략 실행 |
| `RebalancingService` | 월간/분기 리밸런싱 계산 |

## 외부 의존성

- **수신 이벤트**: `SignalGeneratedEvent` ← Signals 컨텍스트
- **발행 이벤트**: `OrderExecutedEvent` → 외부 (Alpaca 브로커)
- **외부 API**: Alpaca Paper Trading (주문 실행)

## 리스크 한도 (변경 불가 비즈니스 규칙)

```
단일 종목 최대: 8%
섹터 최대: 25%
거래당 리스크: 자본의 1%
ATR 스탑: 2.5-3.5x ATR(21)
Fractional Kelly: 1/4 (Full Kelly 절대 금지)
```

## 낙폭 방어 3단계 (변경 불가)

```
10% 낙폭: 신규 진입 중단 + 모니터링 강화
15% 낙폭: 포지션 50% 축소 + 방어적 전환
20% 낙폭: 전량 청산 + 최소 1개월 냉각기 (냉각기 후 25%씩 점진 재진입)
```

## 주요 유스케이스

1. **ProcessSignal**: 시그널 수신 → 포지션 크기 계산 → 리스크 검증 → 주문 실행
2. **CheckDrawdown**: 현재 낙폭 계산 → 방어 단계 판정
3. **Rebalance**: 월간/분기 포트폴리오 리밸런싱
4. **GeneratePerformanceReport**: 성과 분석 리포트 생성

## 현재 구현 위치

```
personal/sizer/     → PositionSizingService
personal/risk/      → RiskValidationService
personal/execution/ → 주문 실행
```

## DDD 목표 구조

```
src/portfolio/
  domain/
    entities.py          # Portfolio aggregate, Position entity
    value_objects.py     # KellyFraction, ATRStop, DrawdownLevel, RiskBudget
    events.py            # OrderExecutedEvent, DrawdownTriggeredEvent
    services.py          # PositionSizingService, RiskValidationService, DrawdownDefenseService
    repositories.py      # IPortfolioRepository, IPositionRepository (ABC)
    __init__.py
  application/
    commands.py          # ProcessSignalCommand, RebalanceCommand
    queries.py           # GetPortfolioStatusQuery, GetDrawdownQuery
    handlers.py          # ProcessSignalHandler, RebalanceHandler
    __init__.py
  infrastructure/
    persistence.py       # SQLitePortfolioRepository
    brokers/             # AlpacaPaperBroker
    __init__.py
```
