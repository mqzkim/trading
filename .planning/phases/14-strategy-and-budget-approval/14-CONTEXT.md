# Phase 14: Strategy and Budget Approval - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

자동 파이프라인(Phase 13)과 주문 실행 사이의 게이팅 레이어. 사용자가 사전 정의한 전략 파라미터(스코어 임계값, 허용 레짐, 최대 거래 비율, 만료일)와 일일 예산 한도 내에서만 자동 실행. 범위를 벗어나는 거래는 수동 리뷰 대기열로 전환. 레짐 변경/drawdown 시 자동 정지.

</domain>

<decisions>
## Implementation Decisions

### Approval 재승인 정책
- 레짐이 허용 목록으로 복귀 시: `suspended_reasons`에서 `regime_change` 자동 제거 → 다른 정지 사유 없으면 자동 재활성화 + Slack 알림
- Drawdown tier 해제(tier 1 이하 복귀) 시: 자동 재활성화 **안 함** — 사용자가 수동으로 `trade approve resume` 실행해야 재개
- Approval 만료 24시간 전 Slack 경고 알림 발송 (파이프라인 실행 시 만료 임박 체크)
- Approval 정지/재활성화 모두 Slack 알림 발송

### 리뷰 큐 운영
- 개별 approve/reject: `trade review list` 로 목록 확인, `trade review approve <symbol>` / `trade review reject <symbol>` 로 처리
- 리뷰에서 approve한 거래는 즉시 주문 제출 (시장 시간 외면 다음 오픈 시 실행)
- 리뷰되지 않은 거래는 24시간 후 자동 만료 + 로그 기록 (시장 상황 변화로 오래된 거래 계획은 유효하지 않음)
- 파이프라인 완료 알림에 "리뷰 대기: N건" 포함 (개별 건별 알림은 없음)

### 예산 운영
- 예산은 approval 엔티티에 포함 (`daily_budget_cap` 필드) — 별도 설정 아님
- 일별 리셋, 이월 없음 — 매일 UTC 자정 기준 spent=0 리셋
- 예산 spent 계산: 주문 제출(submit) 시점에 position_value를 spent에 반영 (채결 여부 무관)
- 예산 80% 사용 시 Slack 경고 알림 — 나머지 거래가 리뷰 큐로 갈 수 있음을 예고

### CLI 인터페이스
- 명령어 네이밍: Claude's Discretion (`trade approve` 또는 `trade strategy` 시리즈)
- 파라미터 입력: 플래그 기반 — `--score`, `--regimes`, `--max-pct`, `--budget`, `--expires` (스크립트/자동화 호환)
- `trade approve status` 출력: 현재 approval 상태 + 오늘 예산 spent/remaining + 리뷰 대기 건수 통합 표시
- Approval 없이 파이프라인 실행 시: 분석(ingest→regime→score→signal→plan)만 실행, execute 단계 스킵 + "No active approval" 로그. 데이터 축적은 계속.

### Claude's Discretion
- CLI 명령어 정확한 네이밍 (`trade approve` vs `trade strategy`)
- 리뷰 큐 Rich table 포맷 세부 설계
- Slack 알림 메시지 포맷 및 세부 내용
- SQLite 스키마 세부 설계 (research 추천 참조)
- ApprovalGateService 내부 구현 패턴

</decisions>

<specifics>
## Specific Ideas

- Phase 13의 `_run_execute()`에서 auto-approve 패턴을 ApprovalGateService로 교체 (13-03 결정: "manual approval deferred to Phase 14")
- `suspended_reasons: set[str]` 패턴으로 복수 정지 사유 추적 (regime_change, drawdown_tier2)
- CooldownState(Phase 12) 패턴 재사용: expiry는 Python에서 체크, SQLite에 영속화
- SyncEventBus의 RegimeChangedEvent 구독으로 자동 정지 구현

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SyncEventBus` (shared/infrastructure/sync_event_bus.py): RegimeChangedEvent 구독 — approval 자동 정지 구현
- `CooldownState` (execution/domain/value_objects.py): 만료/영속화 패턴 — StrategyApproval 엔티티 참조
- `PipelineOrchestrator._run_execute()` (pipeline/domain/services.py): auto-approve 교체 대상
- `Notifier` (pipeline/infrastructure/): Slack 알림 — approval 이벤트 알림 재사용
- `SafeExecutionAdapter` (execution/infrastructure/safe_adapter.py): 브로커 실행 어댑터

### Established Patterns
- DDD bounded context: `src/{context}/domain/`, `application/`, `infrastructure/` 구조
- SQLite per-context: `CREATE TABLE IF NOT EXISTS` 패턴, DBFactory 사용
- Typer CLI: `@app.command()` 패턴, `_get_ctx()` lazy bootstrap
- 이벤트 기반 cross-context 통신: `SyncEventBus.subscribe()`

### Integration Points
- `bootstrap.py`: ApprovalGateService + 리포지토리 주입, RegimeChangedEvent 구독 등록
- `pipeline/domain/services.py`: `_run_execute()` 내 approval gate 체크 삽입
- `cli/main.py`: `trade approve` / `trade review` 서브커맨드 추가
- SQLite: strategy_approvals, daily_budget, trade_review_queue 테이블 추가

</code_context>

<deferred>
## Deferred Ideas

None — 논의가 phase scope 내에서 유지됨

</deferred>

---

*Phase: 14-strategy-and-budget-approval*
*Context gathered: 2026-03-13*
