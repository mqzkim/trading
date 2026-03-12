# Requirements: Intrinsic Alpha Trader v1

> Generated: 2026-03-12 | Status: Approved | Total: 32 requirements

## Category 1: Data Ingestion (DATA)

- [x] **DATA-01**: OHLCV 데이터 수집 — yfinance 기반 3년+ 가격 데이터 (daily OHLCV + adjusted close)
- [x] **DATA-02**: 재무제표 데이터 수집 — yfinance + edgartools 기반 SEC 재무 데이터 (income statement, balance sheet, cash flow)
- [x] **DATA-03**: 데이터 캐시/저장 — DuckDB(분석 워크로드) + SQLite(운영 상태) 이중 DB 아키텍처
- [x] **DATA-04**: 데이터 품질 검증 — 결측값, 이상치, stale data 감지 + point-in-time awareness (filing date 추적)

## Category 2: Scoring (SCOR)

- [x] **SCOR-01**: Safety Gate — Altman Z-Score > 1.81 AND Beneish M-Score < -1.78 hard gate (미통과 시 즉시 제외)
- [x] **SCOR-02**: Piotroski F-Score 계산 — 9항목 기본적 건전성 점수 (0-9)
- [x] **SCOR-03**: Altman Z-Score 계산 — 부도 위험도 평가 (Safe/Grey/Distress)
- [x] **SCOR-04**: Beneish M-Score 계산 — 이익 조작 가능성 탐지
- [x] **SCOR-05**: Mohanram G-Score 계산 — 성장주 품질 스코어 (0-8)
- [x] **SCOR-06**: Composite Score — 가중 평균 복합 스코어 (0-100) + regime 조정 가중치

## Category 3: Valuation (VALU)

- [x] **VALU-01**: DCF 모델 — Discounted Cash Flow, 2-stage growth model, terminal value 40% cap
- [x] **VALU-02**: EPV 모델 — Earnings Power Value, 정상화 수익력 기반 가치 평가
- [x] **VALU-03**: Relative Multiples 모델 — PER/PBR/EV-EBITDA 섹터 대비 상대 비교
- [x] **VALU-04**: Ensemble Weighting — DCF(40%) + EPV(35%) + Relative(25%) 가중 평균 + 신뢰도 계산
- [x] **VALU-05**: Margin of Safety — 내재가치 대비 현재가 할인율 계산, 20%+ threshold

## Category 4: Signal (SIGN)

- [x] **SIGN-01**: BUY/HOLD/SELL 시그널 — Quality score + Valuation gap 결합, 명확한 근거 텍스트 포함
- [x] **SIGN-02**: Screener/Ranker — Composite score 기준 Top N 종목 랭킹 + 필터링

## Category 5: Risk/Portfolio (RISK)

- [x] **RISK-01**: Fractional Kelly Position Sizing — 1/4 Kelly 기반 최적 포지션 크기 계산
- [x] **RISK-02**: ATR-based Stop-Loss — 2.5-3.5x ATR(21) trailing stop
- [x] **RISK-03**: Take-Profit 레벨 — 내재가치 기반 목표가 + 부분 익절 레벨
- [x] **RISK-04**: Drawdown Defense — 10%/15%/20% 3-tier 포트폴리오 드로다운 방어 프로토콜
- [x] **RISK-05**: Position/Sector Limits — Max position 8%, Max sector 25% 하드 리밋

## Category 6: Execution (EXEC)

- [x] **EXEC-01**: Trade Plan 생성 — entry/stop/target/size/reasoning 포함 구조화된 트레이드 플랜
- [x] **EXEC-02**: Human Approval CLI — 주문 전 사람 승인 필수 워크플로우 (Y/N + 수정 가능)
- [x] **EXEC-03**: Alpaca Paper Trading — alpaca-py SDK 기반 모의 트레이딩 주문 실행
- [x] **EXEC-04**: Bracket Order — entry + stop-loss + take-profit 일괄 주문

## Category 7: Interface (INTF)

- [x] **INTF-01**: CLI Dashboard — 포트폴리오 뷰, P&L, 포지션 현황, 드로다운 상태
- [x] **INTF-02**: Stock Screener CLI — 스코어 기반 종목 선별/랭킹 인터랙티브 뷰
- [x] **INTF-03**: Watchlist 관리 — 관심종목 CRUD + 알림 설정
- [x] **INTF-04**: 모니터링 알림 — stop hit, target reached, drawdown tier 변경 알림

## Category 8: Backtesting (BACK)

- [x] **BACK-01**: Walk-Forward Validation — out-of-sample 검증, Sharpe t-stat > 2, PBO < 10% 목표
- [x] **BACK-02**: 성과 리포트 — Sharpe ratio, max drawdown, win rate, profit factor 등 핵심 메트릭

---

## Cross-Cutting Concerns

- **Explainability**: 모든 스코어/시그널/추천은 데이터 포인트까지 역추적 가능
- **Point-in-Time**: 재무 데이터는 filing date 기준 (look-ahead bias 방지)
- **Audit Trail**: 모든 의사결정 과정 로깅 (scoring -> signal -> trade plan -> execution)
- **DDD Compliance**: 워크스페이스 DDD 규칙 준수 (도메인 순수성, 레이어 의존성, 이벤트 통신)

## Traceability Matrix

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1: Data Foundation | Complete |
| DATA-02 | Phase 1: Data Foundation | Complete |
| DATA-03 | Phase 1: Data Foundation | Complete |
| DATA-04 | Phase 1: Data Foundation | Complete |
| SCOR-01 | Phase 1: Data Foundation | Complete |
| SCOR-02 | Phase 1: Data Foundation | Complete |
| SCOR-03 | Phase 1: Data Foundation | Complete |
| SCOR-04 | Phase 1: Data Foundation | Complete |
| SCOR-05 | Phase 2: Analysis Core | Complete |
| SCOR-06 | Phase 2: Analysis Core | Complete |
| VALU-01 | Phase 2: Analysis Core | Complete |
| VALU-02 | Phase 2: Analysis Core | Complete |
| VALU-03 | Phase 2: Analysis Core | Complete |
| VALU-04 | Phase 2: Analysis Core | Complete |
| VALU-05 | Phase 2: Analysis Core | Complete |
| SIGN-01 | Phase 3: Decision Engine | Complete |
| SIGN-02 | Phase 3: Decision Engine | Complete |
| RISK-01 | Phase 3: Decision Engine | Complete |
| RISK-02 | Phase 3: Decision Engine | Complete |
| RISK-03 | Phase 3: Decision Engine | Complete |
| RISK-04 | Phase 3: Decision Engine | Complete |
| RISK-05 | Phase 3: Decision Engine | Complete |
| BACK-01 | Phase 3: Decision Engine | Complete |
| BACK-02 | Phase 3: Decision Engine | Complete |
| EXEC-01 | Phase 4: Execution and Interface | Complete |
| EXEC-02 | Phase 4: Execution and Interface | Complete |
| EXEC-03 | Phase 4: Execution and Interface | Complete |
| EXEC-04 | Phase 4: Execution and Interface | Complete |
| INTF-01 | Phase 4: Execution and Interface | Complete |
| INTF-02 | Phase 4: Execution and Interface | Complete |
| INTF-03 | Phase 4: Execution and Interface | Complete |
| INTF-04 | Phase 4: Execution and Interface | Complete |

---
*Approved: 2026-03-12*
