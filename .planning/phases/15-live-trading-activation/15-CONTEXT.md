# Phase 15: Live Trading Activation - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Alpaca 라이브 계정에서 실제 주문 실행. 승인된 안전 경계 내에서 자동 실행하되, circuit breaker로 연속 실패 시 자동 중단, 백그라운드 order monitor로 모든 미체결 주문 추적, WebSocket으로 실시간 체결 수신, 초기 25% 자본 제한으로 시작하여 점진적 증가.

</domain>

<decisions>
## Implementation Decisions

### Circuit Breaker
- 단일 파이프라인 실행 내에서 3회 연속 주문 실패 시 트립
- 트립 시 동작: Slack 알림 발송 + 모든 미체결 주문 취소 (포지션은 유지 — stop-loss가 보호)
- 리셋 방식: 수동 CLI 리셋 가능 + 다음 파이프라인 실행 시 자동 리셋 (하루 냉각기 효과)
- 파이프라인 실행 간 실패 카운트는 초기화됨

### Order Monitor
- 백그라운드 스레드로 실행 — 파이프라인이 주문 제출한 후부터 모든 주문 터미널까지 추적
- 파이프라인 실행 중에만 활성 — 파이프라인 종료 시 모니터도 종료
- Stuck 주문: 5분 타임아웃 후 자동 취소 + Slack 알림
- WebSocket(LIVE-04)과 병행하여 폴백 역할 수행

### WebSocket 실시간 체결
- Alpaca TradingStream이 주 체결 수신 채널 (LIVE-04)
- WebSocket 단절 시: 자동 폴링 모니터로 전환 + WebSocket 리커넥션 시도, 재연결 성공 시 폴링 중단
- 파이프라인 실행 중에만 WebSocket 연결 (상시 데몬 아님)
- Fill 이벤트는 SyncEventBus로 OrderFilledEvent 발행 — portfolio, pipeline 등 다른 컨텍스트가 구독 (Phase 16 대시보드 SSE와 연동 가능)

### 자본 배분 Ramp-up
- LIVE_CAPITAL_RATIO 환경변수 (Settings): 0.25 기본값 — US_CAPITAL * LIVE_CAPITAL_RATIO가 실제 사용 가능 자본
- Approval 예산과 별도로 동작 (이중 안전장치: LIVE_CAPITAL_RATIO로 전체 상한, Approval budget으로 일일 한도)
- 4단계: 25% → 50% → 75% → 100%
- 반자동 CLI 명령으로 조정: `trade config set-capital-ratio 0.5` (확인 프롬프트 포함)
- 증가 시 현재 성과 요약(승률, 수익률, 실행일수) 경고 표시 — 강제 차단 없음, 사용자 판단에 맡김

### Claude's Discretion
- Order monitor 스레드 구현 방식 (threading.Thread vs concurrent.futures)
- WebSocket 리커넥션 간격 및 최대 재시도 횟수
- Circuit breaker 내부 상태 관리 (메모리 vs SQLite)
- `trade config` CLI 서브커맨드 구조
- OrderFilledEvent 도메인 이벤트 스키마

</decisions>

<specifics>
## Specific Ideas

- SafeExecutionAdapter에 circuit breaker 로직 추가 (기존 cooldown 체크 패턴 확장)
- AlpacaExecutionAdapter의 paper=False 경로 이미 구현됨 — LIVE_KEY/SECRET로 초기화
- strategy-recommendation.md의 25% 점진 재진입 규칙과 LIVE_CAPITAL_RATIO 4단계가 일치
- Phase 12 deferred: "WebSocket 기반 실시간 주문 모니터링 — Phase 15 (LIVE-04)"
- Phase 12 deferred: "Circuit breaker (3회 연속 실패 시 자동 중단) — Phase 15 (LIVE-06)"
- Phase 13의 PipelineOrchestrator._run_execute()에서 SafeExecutionAdapter 호출 — circuit breaker는 이 레벨에서 동작

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SafeExecutionAdapter` (execution/infrastructure/safe_adapter.py): cooldown 체크 + LIVE 모드 폴링/bracket 검증 — circuit breaker 로직 추가 대상
- `AlpacaExecutionAdapter` (execution/infrastructure/alpaca_adapter.py): paper=False 경로 지원, `_client` 접근으로 폴링 가능
- `SyncEventBus` (shared/infrastructure/sync_event_bus.py): OrderFilledEvent 발행 채널
- `Notifier` (pipeline/infrastructure/): Slack webhook — circuit breaker/stuck order 알림 재사용
- `KillSwitchService` (execution/infrastructure/kill_switch.py): 미체결 취소 로직 — circuit breaker 트립 시 재사용
- `Settings` (settings.py): ALPACA_LIVE_KEY/SECRET, EXECUTION_MODE 이미 정의됨

### Established Patterns
- SafeExecutionAdapter decorator 패턴: inner adapter 래핑 + 안전 체크
- alpaca-py lazy import: 메서드 내부 import (유지)
- SyncEventBus.subscribe() 이벤트 기반 cross-context 통신
- SQLite per-context DB + DBFactory
- Typer CLI @app.command() + _get_ctx() lazy bootstrap

### Integration Points
- `safe_adapter.py`: circuit breaker 로직 + order monitor 스레드 시작 지점
- `bootstrap.py`: LIVE_CAPITAL_RATIO 설정 반영, WebSocket stream 초기화
- `settings.py`: LIVE_CAPITAL_RATIO 환경변수 추가
- `pipeline/domain/services.py`: PipelineOrchestrator._run_execute()에서 circuit breaker 상태 확인
- `cli/main.py`: `trade config set-capital-ratio`, `trade circuit-breaker reset` CLI 명령어 추가

</code_context>

<deferred>
## Deferred Ideas

None — 논의가 phase scope 내에서 유지됨

</deferred>

---

*Phase: 15-live-trading-activation*
*Context gathered: 2026-03-13*
