# Phase 16: Web Dashboard - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

브라우저 기반 대시보드로 포트폴리오, 파이프라인, 리스크, 승인 상태에 대한 운영 가시성 제공. HTMX + Jinja2 + Tailwind CSS로 구현. 실시간 SSE 업데이트. 개인 전용 도구 (localhost, 인증 없음).

</domain>

<decisions>
## Implementation Decisions

### 페이지 구조 & 레이아웃
- 사이드바 + 컨텐츠 영역 레이아웃
- 사이드바 네비게이션 4개 페이지: Overview, Signals, Risk, Pipeline & Approval
- 상단에 Paper/Live 모드 배너 (DASH-09): Paper=초록, Live=빨간
- CSS: Tailwind CSS (Play CDN으로 빠른 셋업, 빌드 도구 불필요)

### Overview 페이지 (메인)
- 히어로 영역: 총 자산, 오늘 P&L, 드로다운 퍼센트, 마지막 파이프라인 상태 — 핵심 KPI 4개
- 보유 종목 테이블: ticker, 수량, 현재가, P&L(수익률+수익금), stop/target, composite score
- 에퀴티 커브 차트 (Plotly): 레짐 배경색 오버레이 (Bull=초록, Bear=빨간, Sideways=노란, Crisis=회색)

### Signals 페이지
- 최신 스코어링 결과: 정렬 가능 테이블 (composite, F/Z/M/G, 기술적, 시그널)
- 스코어 높을수록 배경색 진해지는 heatmap 스타일
- 전략별 합의 상태, 시그널 추천 목록

### Risk 페이지
- 드로다운 반원형 게이지: 0~20% 단계별 색상 (초록→노랑→빨강), 10/15/20% 기준선 표시
- 섹터 노출 도넛 차트: 각 섹터별 비율 + 25% 한도선
- 포지션 한도 활용률, 레짐 상태 배지

### Pipeline & Approval 페이지
- 파이프라인 실행 이력 테이블: run_id, 시작/종료, 각 stage 결과, 다음 스케줄
- Strategy Approval: 현재 상태 조회 + 새 승인 생성 폼 + 정지/해제 버튼 (수정/삭제는 CLI)
- Daily Budget: 프로그레스 바 + '$사용량 / $한도' 텍스트
- 매뉴얼 리뷰 대기 거래: 대기 목록 + 승인/거부 버튼 (HTMX POST)

### Trade History
- Overview 또는 별도 섹션에 거래 이력 테이블
- 컬럼: 날짜, ticker, 매수/매도, 수량, entry가, stop, target, fill가, 실현 P&L, 전략 출처

### SSE 실시간 업데이트
- 단일 /events SSE 엔드포인트에서 모든 이벤트 스트림
- 4개 이벤트 타입: OrderFilled, PipelineStatusChanged, DrawdownTierChanged, RegimeChanged
- HTMX hx-ext='sse'로 각 섹션이 필요한 이벤트만 구독
- 이벤트 수신 시 서버 렌더링된 HTML 단편을 hx-swap으로 교체 (JS 최소화)

### 접근 제어
- 인증 없음 — localhost:8000에서만 접근
- 개인 전용 도구이므로 추가 보안 불필요

### Claude's Discretion
- Jinja2 템플릿 구조 및 상속 패턴
- HTMX 속성 세부 설계 (hx-trigger, hx-swap 전략)
- Plotly 차트 구체적 설정값 (색상, 축, 레이아웃)
- SSE 이벤트 직렬화 포맷
- 사이드바 아이콘/스타일링 세부사항
- FastAPI 라우터 구조 (기존 commercial API와의 공존 방식)
- Trade History를 Overview에 포함할지 별도 페이지로 분리할지

</decisions>

<specifics>
## Specific Ideas

- v1.2 research 결정: "Single FastAPI process hosts commercial API + dashboard + APScheduler" — 같은 FastAPI 앱에 대시보드 라우터 추가
- v1.2 research 결정: "HTMX + Jinja2 for dashboard (no React/Node.js)" + "Only 2 new pip packages: APScheduler 3.11.2 + Plotly 6.5.x"
- Phase 15의 OrderFilledEvent가 SyncEventBus로 발행됨 — SSE 브릿지만 추가하면 실시간 체결 업데이트 가능
- Phase 14의 RegimeChangedEvent 핸들러가 승인 자동 정지 — 대시보드에서도 같은 이벤트로 레짐 배지 업데이트
- Phase 13의 pipeline_runs SQLite 테이블에 stage 결과 이미 영속화 — 대시보드는 조회만
- 에퀴티 커브 + 레짐 오버레이는 금융 대시보드의 핵심 시각화 — Plotly의 shape/annotation으로 구현 가능
- 드로다운 게이지의 10/15/20% 기준선은 strategy-recommendation.md의 낙폭 방어 3단계와 일치

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SyncEventBus` (shared/infrastructure/sync_event_bus.py): 모든 도메인 이벤트 발행/구독 — SSE 브릿지 연결 대상
- `OrderFilledEvent` (execution/domain/events.py): 실시간 체결 이벤트
- `RegimeChangedEvent` (regime/domain/events.py): 레짐 전환 이벤트
- `SqlitePipelineRunRepository` (pipeline/infrastructure/): 파이프라인 실행 이력 조회
- `SqliteApprovalRepository` (approval/infrastructure/): 승인 상태 CRUD
- `DailyBudgetTracker` (approval/domain/): 예산 사용량 추적
- `Portfolio` aggregate (portfolio/domain/aggregates.py): 보유 종목, P&L, 드로다운 계산
- `Settings` (settings.py): EXECUTION_MODE, 환경 설정 — 모드 배너 기반
- `bootstrap.py`: 모든 핸들러/리포지토리 주입 완료 — 대시보드 라우터에서 재사용

### Established Patterns
- DDD handler 패턴: Command → Handler → Service → Repository
- SQLite per-context DB (DBFactory): 각 도메인별 DB 분리
- Typer CLI + _get_ctx() lazy bootstrap
- Pydantic Settings: .env 기반 설정
- SyncEventBus.subscribe(): 이벤트 기반 cross-context 통신

### Integration Points
- FastAPI app: 대시보드 라우터 마운트 지점 (아직 FastAPI 앱 미존재 — 새로 생성 필요)
- `bootstrap.py`: 대시보드용 핸들러/리포지토리 주입
- `pyproject.toml`: jinja2, plotly 의존성 추가 필요 (Tailwind는 CDN)
- `settings.py`: DASHBOARD_PORT 등 대시보드 관련 설정

</code_context>

<deferred>
## Deferred Ideas

- 모바일 반응형 레이아웃 — DASH-10 (v2)
- 멀티유저 인증 — DASH-11 (v2)
- React/Next.js 전환 — DASH-12 (v2, HTMX 부족 시)
- Kill switch 버튼 (대시보드에서 긴급 중단) — 별도 phase 가능
- 종목별 스코어 이력 90일 차트 — PIPE-08 (v2)

</deferred>

---

*Phase: 16-web-dashboard*
*Context gathered: 2026-03-13*
