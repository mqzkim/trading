# Phase 13: Automated Pipeline Scheduler - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

전체 screening-to-execution 파이프라인(ingest → regime → score → signal → plan → budget check → execute)을 장 마감 후 자동 실행. NYSE 시장 캘린더 인식, 장애 허용, dry-run 모드 지원. Paper mode에서 먼저 검증.

</domain>

<decisions>
## Implementation Decisions

### Run Timing & Schedule
- 장 마감 30분 후(16:30 ET) 자동 실행 -- 데이터 안정화 대기 후 실행
- APScheduler misfire_grace_time 활용 -- 프로세스 재시작 시 놓친 작업 즉시 실행
- exchange_calendars 라이브러리 사용 (STATE.md blocker 해결) -- 70+ 거래소 지원, 조기마감일 포함
- 주말/휴장/조기마감일 완전 스킵 + "skipped: holiday" 로그만 기록

### Pipeline Halt & Safety
- Crisis/drawdown tier≥2 감지 시: 전체 분석(ingest → regime → score → signal → plan) 실행하되, execute 직전에서 멈춤 -- 스코어 데이터는 계속 축적
- 매 파이프라인 실행 전 ReconciliationService.check_and_halt() 자동 실행 -- 불일치 시 파이프라인 중단 + 로그
- 기존 포지션 유지, 신규 진입만 차단 (strategy-recommendation.md 규칙 준수)

### Notifications
- Notifier 인터페이스 + Slack webhook 기본 구현
- .env에 SLACK_WEBHOOK_URL 설정
- 파이프라인 완료, 중단(halt), 에러 시 Slack 알림 발송
- 이메일 등 추가 채널은 Notifier 인터페이스 확장으로 대응

### Run Logging
- Stage-level summary 로깅: 각 stage 시작/종료 시간, 성공/실패 종목 수, 에러 메시지
- pipeline_runs SQLite 테이블에 영속화 -- run_id, 시작/종료, 각 stage 결과, 다음 스케줄
- dry-run 모드: 전체 파이프라인 실행 후 최종 주문 계획을 Rich table로 표시, 주문 제출만 스킵

### CLI Commands
- `trade pipeline run [--dry-run]` -- 전체 파이프라인 수동 실행
- `trade pipeline status` -- 최근 N회 실행 이력 + 다음 스케줄 표시
- 기존 `trade kill`, `trade sync` 명령어와 공존

### Stage Retry & Failure Handling
- 3회 재시도 + exponential backoff (1초, 2초, 4초 간격)
- ingest에서 일부 종목 실패 시: 성공한 종목만으로 다음 stage 계속 진행
- score/signal stage 종목별 실패: 해당 종목 스킵 + 로그 기록, 나머지 계속
- 파이프라인 중간 실패 후 재개 기능 불필요 -- 전체 재실행 (파이프라인 수 분 소요)

### Claude's Discretion
- APScheduler SQLite job store 스키마 설계
- pipeline_runs 테이블 스키마 세부 설계
- Stage 간 데이터 전달 메커니즘 (메모리 dict vs 이벤트)
- Slack webhook 메시지 포맷
- exchange_calendars 통합 구현 방식
- Notifier 인터페이스 설계

</decisions>

<specifics>
## Specific Ideas

- 기존 `DataPipeline` (data_ingest/infrastructure/pipeline.py)은 ingest만 담당 -- 전체 파이프라인 오케스트레이터는 새로 필요
- `bootstrap()` 에서 모든 핸들러가 이미 주입됨 -- 오케스트레이터는 bootstrap context를 받아서 순차 호출
- 각 CLI 명령(ingest, regime, score, signal, generate-plan)의 핵심 로직을 재사용
- v1.2 research 결정: "Single FastAPI process hosts commercial API + dashboard + APScheduler" -- 스케줄러는 FastAPI와 같은 프로세스
- PIPE-07: APScheduler + SQLite job persistence -- 프로세스 재시작 후 스케줄 복원

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DataPipeline` (data_ingest/infrastructure/pipeline.py): async 데이터 수집, ingest_universe() 메서드
- `bootstrap()` (bootstrap.py): 전체 핸들러 주입 완료 -- score_handler, signal_handler, regime_handler, portfolio_handler, trade_plan_handler
- `SafeExecutionAdapter` (execution/infrastructure/safe_adapter.py): cooldown 체크 포함된 안전 실행
- `ReconciliationService` (execution/infrastructure/reconciliation.py): check_and_halt() 메서드
- `KillSwitchService` (execution/infrastructure/kill_switch.py): 긴급 중단 + cooldown 활성화
- `SyncEventBus` (shared/infrastructure/sync_event_bus.py): 이벤트 기반 cross-context 통신

### Established Patterns
- Typer CLI (cli/main.py): @app.command() 패턴, _get_ctx() lazy bootstrap
- SQLite per-context DB (DBFactory): scoring.db, signals.db, portfolio.db 등 분리
- DDD handler 패턴: Command → Handler → Service → Repository
- Settings (pydantic-settings): .env 기반 설정 관리

### Integration Points
- `cli/main.py`: `trade pipeline run/status` 서브커맨드 추가
- `bootstrap.py`: 파이프라인 오케스트레이터 주입 지점
- `settings.py`: SLACK_WEBHOOK_URL, PIPELINE_SCHEDULE_TIME 등 설정 추가
- SQLite: pipeline_runs 테이블 + APScheduler job store

</code_context>

<deferred>
## Deferred Ideas

None -- 논의가 phase scope 내에서 유지됨

</deferred>

---

*Phase: 13-automated-pipeline-scheduler*
*Context gathered: 2026-03-13*
