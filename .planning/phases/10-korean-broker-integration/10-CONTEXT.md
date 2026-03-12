# Phase 10: Korean Broker Integration - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

KIS(한국투자증권) 브로커 어댑터를 구현하여 KOSPI/KOSDAQ 종목을 모의투자 환경에서 매매. 기존 US Alpaca와 동일한 리스크 체크 및 사용자 승인 워크플로 적용. Phase 6에서 구축한 한국 데이터 파이프라인(pykrx) 위에 구축.

</domain>

<decisions>
## Implementation Decisions

### KIS 계정 및 인증
- KIS 개발자 등록 아직 미완료 -- Mock-first로 개발
- 한국투자증권(KIS) 사용 확정
- Mock 모드로 전체 개발 완료 후 실제 KIS API 연결 (Alpaca mock fallback 패턴 동일)
- 인증 정보는 .env 패턴 동일: KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO

### 주문 방식과 Stop Loss
- 한국 시장은 bracket order 미지원 -- 시스템 모니터링 기반 stop loss
- 일간 가격 체크 후 조건 충족 시 시장가 매도 주문 제출 (중기 보유 전략에 적합)
- 기본 주문 유형: 시장가 (중기 보유라 슬리페이지 무시 가능)
- BUY/SELL 모두 지원 (stop loss 자동 매도에 필요)
- 호가 단위 + 가격제한(+-30%) 자동 검증 (잘못된 주문 방지)

### 통화 및 포지션 사이징
- US/KR 포트폴리오 분리 운영 (각각 별도 자본금, 환율 고려 불필요)
- 포지션 사이징 룰 동일 적용: Fractional Kelly(1/4) + ATR 기반 stop loss
- KRW 자본금은 .env에 설정: KR_CAPITAL (예: 10000000)
- 통화만 KRW로 변경, 나머지 리스크 룰 동일

### 브로커 추상화 구조
- execution/domain에 IBrokerAdapter ABC 정의 (DDD 원칙 준수)
- AlpacaExecutionAdapter와 KisExecutionAdapter 모두 IBrokerAdapter 구현
- 핸들러는 인터페이스만 의존 -- bootstrap에서 시장별 어댑터 주입
- BracketSpec을 범용 OrderSpec으로 확장 (stop_loss/take_profit 선택적 필드)
- Alpaca는 OrderSpec을 bracket order로 변환, KIS는 단건 주문으로 변환
- CLI --market kr/us 플래그로 시장 전환 (Phase 6에서 도입한 패턴 동일)

### Claude's Discretion
- IBrokerAdapter 메서드 시그니처 세부 설계
- Mock 모드 응답 데이터 구조
- 호가 단위 테이블 구현 방식
- Stop loss 모니터링 스케줄링 메커니즘
- KIS API 에러 핸들링 및 재시도 정책

</decisions>

<specifics>
## Specific Ideas

- Alpaca mock fallback 패턴을 그대로 차용: credentials 없으면 자동 mock 모드
- Stop loss는 CLI monitoring command나 cron 기반 일간 체크로 충분 (중기 보유 전략)
- 기존 core/execution/planner.py의 plan_entry() 리스크 수학은 재사용 (adapter pattern)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AlpacaExecutionAdapter` (src/execution/infrastructure/alpaca_adapter.py): mock fallback 패턴, submit_bracket_order/get_positions/get_account API
- `PyKRXClient` (src/data_ingest/infrastructure/pykrx_client.py): 한국 시장 데이터 수집 완료
- `TradePlanService` (src/execution/domain/services.py): plan_entry() 위임, 시장 무관한 리스크 계산
- `BracketSpec`, `OrderResult`, `TradePlan` VOs: 확장 기반

### Established Patterns
- Mock fallback: credentials 없으면 자동 mock 모드 (AlpacaExecutionAdapter._use_mock)
- Lazy import: alpaca-py는 메서드 내부에서만 import (module-level 금지) -- KIS도 동일 패턴
- DDD adapter: core/ 함수를 infrastructure adapter로 감싸서 도메인 서비스에 주입
- --market 플래그: Phase 6에서 도입한 CLI 시장 선택 패턴

### Integration Points
- `src/bootstrap.py`: 시장별 어댑터 주입 지점 (AlpacaAdapter → IBrokerAdapter)
- `src/execution/application/handlers.py`: TradePlanHandler가 adapter 직접 의존 → 인터페이스로 전환 필요
- CLI layer: --market 플래그 기존 위치에서 execution 명령까지 확장

</code_context>

<deferred>
## Deferred Ideas

- KIS 실전 매매 지원 -- Phase 10은 모의투자만, 실전은 Paper Trading 검증 후
- 환율 변환 및 US/KR 통합 포트폴리오 뷰 -- 현재는 분리 운영
- KIS WebSocket 실시간 호가 -- 중기 보유 전략에 불필요
- 한국 시장 특화 리스크 룰 (가격제한폭 활용 등) -- 동일 룰 우선 적용

</deferred>

---

*Phase: 10-korean-broker-integration*
*Context gathered: 2026-03-13*
