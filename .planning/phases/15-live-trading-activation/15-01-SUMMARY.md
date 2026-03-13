---
phase: 15-live-trading-activation
plan: 01
subsystem: execution
tags: [circuit-breaker, capital-ratio, kill-switch, safety, cli]

requires:
  - phase: 12-safety-infrastructure
    provides: SafeExecutionAdapter, KillSwitchService, CooldownRepository
provides:
  - CircuitBreakerTrippedError in SafeExecutionAdapter (3 consecutive failures)
  - OrderFilledEvent domain event for order monitoring
  - LIVE_CAPITAL_RATIO setting with bootstrap enforcement
  - CLI config show/set-capital-ratio and circuit-breaker status/reset commands
affects: [15-02-plan, 16-web-dashboard]

tech-stack:
  added: []
  patterns: [circuit-breaker-pattern, capital-ratio-enforcement]

key-files:
  created:
    - tests/unit/test_circuit_breaker.py
    - tests/unit/test_capital_ratio.py
    - tests/unit/test_cli_config.py
  modified:
    - src/execution/domain/events.py
    - src/execution/infrastructure/safe_adapter.py
    - src/settings.py
    - src/bootstrap.py
    - cli/main.py

key-decisions:
  - "Circuit breaker trips on 3rd failure (not after), calling kill switch with liquidate=False"
  - "Notifier wired into SafeExecutionAdapter after pipeline notifier creation in bootstrap"
  - "safe_adapter and kill_switch added to bootstrap context dict for CLI access"

patterns-established:
  - "Circuit breaker pattern: consecutive failure tracking with automatic halt and manual reset"
  - "Capital ratio enforcement: live mode applies ratio at bootstrap, paper mode uses full capital"

requirements-completed: [LIVE-01, LIVE-02, LIVE-05, LIVE-06]

duration: 7min
completed: 2026-03-13
---

# Phase 15 Plan 01: Circuit Breaker and Capital Ratio Summary

**Circuit breaker halts trading after 3 consecutive failures with kill switch activation, LIVE_CAPITAL_RATIO=0.25 limits live capital, CLI commands for config and reset**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-13T13:48:24Z
- **Completed:** 2026-03-13T13:55:40Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- CircuitBreakerTrippedError raised after 3 consecutive order failures, triggers KillSwitchService and notifier
- LIVE_CAPITAL_RATIO=0.25 enforced in bootstrap for live mode (25% of US_CAPITAL)
- OrderFilledEvent domain event added for order monitoring in Plan 02
- CLI commands: config show, config set-capital-ratio, circuit-breaker status, circuit-breaker reset

## Task Commits

Each task was committed atomically:

1. **Task 1: Circuit breaker + OrderFilledEvent + capital ratio** (TDD)
   - `439d9fe` (test: add failing tests for circuit breaker, capital ratio, OrderFilledEvent)
   - `85adc47` (feat: circuit breaker, OrderFilledEvent, LIVE_CAPITAL_RATIO with bootstrap wiring)
2. **Task 2: CLI commands for config and circuit breaker** - `8185f81` (feat: CLI commands)

## Files Created/Modified
- `src/execution/domain/events.py` - Added OrderFilledEvent with position_qty field
- `src/execution/infrastructure/safe_adapter.py` - CircuitBreakerTrippedError, circuit breaker logic in SafeExecutionAdapter
- `src/settings.py` - LIVE_CAPITAL_RATIO=0.25 setting
- `src/bootstrap.py` - Capital ratio enforcement, kill_switch/safe_adapter wiring and ctx keys
- `cli/main.py` - config show/set-capital-ratio, circuit-breaker status/reset commands
- `tests/unit/test_circuit_breaker.py` - 6 circuit breaker tests
- `tests/unit/test_capital_ratio.py` - 4 capital ratio and OrderFilledEvent tests
- `tests/unit/test_cli_config.py` - 4 CLI command tests

## Decisions Made
- Circuit breaker trips on the 3rd failure (counter reaches max_failures), calls kill switch with liquidate=False to cancel open orders but not close positions
- Notifier wired into SafeExecutionAdapter after pipeline notifier is created in bootstrap (deferred assignment)
- safe_adapter and kill_switch added as top-level keys in bootstrap context dict for direct CLI access
- Pre-existing mypy module resolution issue (dual module names) left as-is -- not caused by this plan

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed OrderSpec field names in tests**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Test used `side` and `order_type` fields but OrderSpec uses `direction` and `entry_price`
- **Fix:** Updated _spec() helper to use correct OrderSpec fields
- **Files modified:** tests/unit/test_circuit_breaker.py
- **Verification:** All tests pass
- **Committed in:** 85adc47

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor test helper fix. No scope creep.

## Issues Encountered
- Pre-existing test failure in test_api_routes.py (version 1.0.0 vs 1.1.0 mismatch) -- not related to this plan

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Circuit breaker and capital ratio ready for live trading activation
- OrderFilledEvent available for Plan 02 (order monitoring/WebSocket)
- safe_adapter in bootstrap context enables Plan 02 to wire order monitor

---
*Phase: 15-live-trading-activation*
*Completed: 2026-03-13*
