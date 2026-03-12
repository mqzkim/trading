# Phase 12: Safety Infrastructure - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Execution layer is production-safe -- explicit mode switching, no silent failures, persistent risk state, broker reconciliation. System starts in paper mode by default; live mode requires explicit .env setting and confirmation. Order failures in live mode raise errors (never phantom fills or silent mock fallbacks). Drawdown cooldown persists across restarts. Kill switch cancels orders and halts pipeline immediately.

</domain>

<decisions>
## Implementation Decisions

### Execution Mode Switching
- EXECUTION_MODE=paper|live enum in .env only -- CLI flag 전환 불가 (실수 방지)
- 기본값 paper -- credentials만으로 live 전환 불가
- live 모드 시작 시 확인 프롬프트 필수 ("Are you sure? yes/no") -- cron 자동화 시 --confirm 플래그 필요
- 별도 API 키: ALPACA_PAPER_KEY/SECRET + ALPACA_LIVE_KEY/SECRET -- EXECUTION_MODE에 따라 자동 선택

### Live Mode Failure Policy
- live 모드에서 주문 실패 시: 로그 기록 + 해당 종목 스킵 + 다음 종목 계속 처리
- mock 폴백 절대 금지 -- live에서 _mock_bracket_order() 호출 경로 완전 제거
- 현재 코드의 `_real_bracket_order()` except 블록이 mock 반환하는 패턴 제거 필수
- 연속 실패 카운트는 Phase 15 circuit breaker(LIVE-06)에서 처리

### Position Reconciliation
- 파이프라인 시작 시 1회 SQLite vs 브로커 포지션 정합성 체크
- 불일치 발견 시: 상세 diff 출력 + 신규 주문 차단 (파이프라인 중단)
- 해결: `trade sync` CLI 명령으로 브로커 기준 동기화 실행 (사용자가 diff 확인 후 승인)
- 실행 중 동적 체크 없음 -- 시작 시 1회로 충분

### Drawdown Cooldown Persistence
- SQLite 테이블에 영속화: triggered_at, expires_at (30일 후), current_tier (10/15/20), re_entry_pct (0/25/50/75/100)
- 프로세스 재시작 시 SQLite에서 cooldown 상태 복원
- --force-override 플래그로 수동 오버라이드 가능 (비상용) + 경고 메시지 출력
- 냉각기 후 재진입: 자본의 25%씩 4단계 점진 재진입 (strategy-recommendation.md 규칙)
- 냉각기 중: 데이터 수집/스코어링/시그널은 계속 실행, 주문 제출만 차단

### Kill Switch
- 두 가지 모드 제공:
  - `trade kill` -- 모든 미체결 주문 취소 + 파이프라인 즉시 중단 (확인 없이 즉시 실행)
  - `trade kill --liquidate` -- 미체결 취소 + 전체 포지션 시장가 매도 (확인 프롬프트 필수)
- kill 실행 후 자동으로 cooldown 상태 진입 (kill 이유 + 시간 기록)
- 감정적 재진입 방지 목적

### Claude's Discretion
- SafeExecutionAdapter 내부 구현 패턴 (기존 AlpacaExecutionAdapter 래핑 vs 새 클래스)
- SQLite cooldown/reconciliation 테이블 스키마 세부 설계
- 주문 상태 폴링 인터벌 및 타임아웃 값
- bracket order leg 검증 구현 방식
- 확인 프롬프트 UX (Rich prompt vs 단순 input)

</decisions>

<specifics>
## Specific Ideas

- 현재 `_real_bracket_order()`의 except 블록이 `self._mock_bracket_order(spec)` 반환 -- 이것이 SAFE-02의 핵심 수정 대상
- `paper=True` 하드코딩 (alpaca_adapter.py:44) -> EXECUTION_MODE 기반 동적 선택으로 변경
- Phase 10에서 확립한 IBrokerAdapter ABC 패턴 유지 -- SafeExecutionAdapter도 동일 인터페이스 구현
- strategy-recommendation.md의 낙폭 방어 3단계 + 25% 점진 재진입 규칙을 코드에 정확히 반영

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `IBrokerAdapter` (execution/domain/repositories.py): market-agnostic 브로커 인터페이스 -- submit_order, get_positions, get_account
- `AlpacaExecutionAdapter` (execution/infrastructure/alpaca_adapter.py): 래핑 대상. mock fallback + paper=True 하드코딩 수정 필요
- `Portfolio` aggregate (portfolio/domain/aggregates.py): drawdown 계산 + DrawdownLevel 판정 -- cooldown 트리거 기반
- `PortfolioRiskService` (portfolio/domain/services.py): assess_drawdown_defense() -- cooldown 판단 로직 기존 구현
- `DrawdownLevel` enum (portfolio/domain/value_objects.py): NORMAL/CAUTION/WARNING/CRITICAL 4단계

### Established Patterns
- Mock fallback: credentials 없으면 mock 모드 (Phase 12에서 live 모드는 mock 금지로 변경)
- Lazy import: alpaca-py는 메서드 내부 import (유지)
- DDD adapter: core/ -> infrastructure adapter -> domain service 주입
- bootstrap.py: 시장별/모드별 어댑터 주입 지점

### Integration Points
- `bootstrap.py` (line 118): AlpacaExecutionAdapter 생성 지점 -- EXECUTION_MODE 분기 추가
- `portfolio/application/handlers.py`: PortfolioManagerHandler -- cooldown 상태 체크 연동
- CLI layer: `trade` 명령어 그룹에 `kill`, `sync` 서브커맨드 추가
- SQLite DB: cooldown_state, position_reconciliation 테이블 추가

</code_context>

<deferred>
## Deferred Ideas

- WebSocket 기반 실시간 주문 모니터링 -- Phase 15 (LIVE-04)
- Circuit breaker (3회 연속 실패 시 자동 중단) -- Phase 15 (LIVE-06)
- Dashboard에서 kill switch 버튼 -- Phase 16 (DASH-06)
- KIS 브로커에 대한 동일 safety 적용 -- 향후 별도 phase

</deferred>

---

*Phase: 12-safety-infrastructure*
*Context gathered: 2026-03-13*
