# Requirements: Intrinsic Alpha Trader

**Defined:** 2026-03-12
**Core Value:** Every recommendation must be explainable and risk-controlled -- capital preservation and positive expectancy over maximizing returns.

## v1.1 Requirements

Requirements for Stabilization & Expansion milestone. Each maps to roadmap phases.

### Infrastructure

- [x] **INFRA-01**: SyncEventBus 구현 및 기존 4개 바운디드 컨텍스트 배선
- [x] **INFRA-02**: Composition Root (bootstrap) 구현으로 God Orchestrator 제거
- [x] **INFRA-03**: DB Connection Factory (DuckDB/SQLite 통합 관리)
- [x] **INFRA-04**: DuckDB/SQLite 스코어링 스토어 불일치 수정
- [x] **INFRA-05**: 누락 CLI 명령어 추가 (ingest, generate-plan, backtest)
- [x] **INFRA-06**: G-Score 블렌딩 및 레짐 조정 DDD 핸들러 배선
- [x] **INFRA-07**: 도메인 이벤트 EventBus 발행 배선
- [x] **INFRA-08**: Cross-context 직접 import 수정 (execution -> portfolio)
- [x] **INFRA-09**: 나머지 tech debt 항목 해결 (v1.0 감사 기준)

### Data Pipeline

- [x] **DATA-01**: yfinance 실제 API 데이터 파이프라인 검증 (adjusted close 동작 포함)
- [x] **DATA-02**: edgartools XBRL 커버리지 소형주 검증
- [x] **DATA-03**: 데이터 품질 검증 레이어 (결측/이상치 탐지)
- [x] **DATA-04**: pykrx 기반 KOSPI/KOSDAQ OHLCV 데이터 수집 어댑터
- [x] **DATA-05**: pykrx 기반 한국 시장 재무제표 수집 (PER/PBR/DIV)
- [x] **DATA-06**: 레짐 감지용 데이터 수집 (VIX, S&P 500, 수익률 곡선)

### Technical Scoring

- [x] **TECH-01**: RSI/MACD/MA/ADX/OBV 5개 지표를 DDD 스코어링 컨텍스트에 통합
- [x] **TECH-02**: 기술적 복합 점수 (0-100) 산출 (가중 합산)
- [x] **TECH-03**: 기존 CompositeScore에 기술 점수 통합 (기본40%/기술40%/센티먼트20%)
- [x] **TECH-04**: 서브 스코어 분해 출력 (5개 지표별 개별 점수 + 설명)

### Regime Detection

- [ ] **REGIME-01**: VIX/S&P500/ADX/수익률곡선 데이터 기반 레짐 판별 배선
- [ ] **REGIME-02**: 3일 확인 로직 배선 (기존 MarketRegime.is_confirmed)
- [ ] **REGIME-03**: RegimeChangedEvent EventBus 발행
- [ ] **REGIME-04**: 레짐별 스코어링 가중치 자동 조정 (Bull/Bear/Sideways/Crisis)
- [ ] **REGIME-05**: CLI에서 현재 레짐 + 90일 히스토리 조회

### Signal Fusion

- [ ] **SIGNAL-01**: CAN SLIM 7개 기준 스코어링 구현
- [ ] **SIGNAL-02**: Magic Formula (Earnings Yield + ROC) 랭킹 구현
- [ ] **SIGNAL-03**: Dual Momentum (절대 + 상대) 시그널 구현
- [ ] **SIGNAL-04**: Trend Following (20/55일 고점 돌파 + ADX) 구현
- [ ] **SIGNAL-05**: 4전략 합의 시그널 (3/4 동의 = 강한 시그널) 배선
- [ ] **SIGNAL-06**: 레짐 가중 전략 합산 (Bull->모멘텀 강화, Bear->퀄리티 강화)
- [ ] **SIGNAL-07**: 전략별 추론 체인 출력 (왜 BUY/HOLD/SELL인지 설명)

### Korean Broker

- [ ] **KR-01**: python-kis 기반 KIS 브로커 어댑터 (IBrokerRepository 구현)
- [ ] **KR-02**: KIS 모의투자 지원 (mock trading 환경)
- [ ] **KR-03**: KRW 통화 처리 및 포지션 사이징 적용

### Commercial API

- [ ] **API-01**: QuantScore API 엔드포인트 (복합 점수 조회)
- [ ] **API-02**: RegimeRadar API 엔드포인트 (현재 레짐 + 히스토리)
- [ ] **API-03**: SignalFusion API 엔드포인트 (합의 시그널 조회)
- [ ] **API-04**: JWT 기반 티어 인증 (free/basic/pro)
- [ ] **API-05**: 티어별 Rate Limiting (slowapi)
- [ ] **API-06**: API 키 관리 및 면책조항 응답 포함

## v1.2+ Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Analytics

- **ADV-01**: HMM 기반 확률적 레짐 감지 (hmmlearn GaussianHMM)
- **ADV-02**: SEC 파일링 NLP 분석 (감성/키워드)
- **ADV-03**: 센티먼트 스코어링 (뉴스/소셜 감성 점수)

### Scaling

- **SCALE-01**: Redis 기반 분산 캐싱 (멀티 인스턴스 지원)
- **SCALE-02**: Stripe 결제 연동 (수요 검증 후)

### Interface

- **UI-01**: Web GUI 대시보드 (Streamlit 또는 Next.js)
- **UI-02**: 모바일 알림 (Slack/Telegram 봇)

## Out of Scope

| Feature | Reason |
|---------|--------|
| 풀 자동 실행 | 페이퍼 트레이딩 검증 선행 필요 |
| 실시간 인트라데이 트레이딩 | 일간 단위 중기 보유 전략 |
| 옵션/파생상품 | 주식 전용 시스템 |
| ML 최적화 지표 가중치 | 과적합 위험, 고정 가중치 우선 |
| 50+ 기술적 지표 | 5개 직교 지표로 충분, 지표 과잉 방지 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 5 | Complete |
| INFRA-02 | Phase 5 | Complete |
| INFRA-03 | Phase 5 | Complete |
| INFRA-04 | Phase 5 | Complete |
| INFRA-05 | Phase 5 | Complete |
| INFRA-06 | Phase 5 | Complete |
| INFRA-07 | Phase 5 | Complete |
| INFRA-08 | Phase 5 | Complete |
| INFRA-09 | Phase 5 | Complete |
| DATA-01 | Phase 6 | Complete |
| DATA-02 | Phase 6 | Complete |
| DATA-03 | Phase 6 | Complete |
| DATA-04 | Phase 6 | Complete |
| DATA-05 | Phase 6 | Complete |
| DATA-06 | Phase 6 | Complete |
| TECH-01 | Phase 7 | Complete |
| TECH-02 | Phase 7 | Complete |
| TECH-03 | Phase 7 | Complete |
| TECH-04 | Phase 7 | Complete |
| REGIME-01 | Phase 8 | Pending |
| REGIME-02 | Phase 8 | Pending |
| REGIME-03 | Phase 8 | Pending |
| REGIME-04 | Phase 8 | Pending |
| REGIME-05 | Phase 8 | Pending |
| SIGNAL-01 | Phase 9 | Pending |
| SIGNAL-02 | Phase 9 | Pending |
| SIGNAL-03 | Phase 9 | Pending |
| SIGNAL-04 | Phase 9 | Pending |
| SIGNAL-05 | Phase 9 | Pending |
| SIGNAL-06 | Phase 9 | Pending |
| SIGNAL-07 | Phase 9 | Pending |
| KR-01 | Phase 10 | Pending |
| KR-02 | Phase 10 | Pending |
| KR-03 | Phase 10 | Pending |
| API-01 | Phase 11 | Pending |
| API-02 | Phase 11 | Pending |
| API-03 | Phase 11 | Pending |
| API-04 | Phase 11 | Pending |
| API-05 | Phase 11 | Pending |
| API-06 | Phase 11 | Pending |

**Coverage:**
- v1.1 requirements: 35 total
- Mapped to phases: 35
- Unmapped: 0

---
*Requirements defined: 2026-03-12*
*Last updated: 2026-03-12 after roadmap creation*
