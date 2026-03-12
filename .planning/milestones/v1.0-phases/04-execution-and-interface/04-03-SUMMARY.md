---
phase: 04-execution-and-interface
plan: 03
subsystem: execution, cli
tags: [trade-approval, bracket-order, cli, alerts, domain-events, typer, rich]

# Dependency graph
requires:
  - phase: 04-execution-and-interface
    provides: "TradePlan/BracketSpec VOs, TradePlanService, AlpacaExecutionAdapter, SqliteTradePlanRepository (Plan 01)"
  - phase: 04-execution-and-interface
    provides: "CLI dashboard/screener/watchlist commands, WatchlistEntry VO, SqliteWatchlistRepository (Plan 02)"
provides:
  - "TradePlanHandler orchestrating generate->approve->execute lifecycle"
  - "GenerateTradePlanCommand, ApproveTradePlanCommand, ExecuteOrderCommand application commands"
  - "CLI approve, execute, monitor commands with human-in-the-loop confirmation"
  - "StopHitAlertEvent, TargetReachedAlertEvent domain events"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [command-handler-pattern, human-in-the-loop-cli, one-shot-monitoring]

key-files:
  created:
    - src/execution/application/__init__.py
    - src/execution/application/commands.py
    - src/execution/application/handlers.py
    - tests/unit/test_trade_approval.py
    - tests/unit/test_alerts.py
    - tests/unit/test_cli_approve.py
  modified:
    - src/execution/domain/events.py
    - src/execution/domain/__init__.py
    - cli/main.py

key-decisions:
  - "TradePlanHandler uses constructor DI for service, repo, and adapter (no global state)"
  - "Approve command includes optional quantity/stop-loss modification before execution"
  - "Monitor command is one-shot check (not persistent/live) using stored prices as proxy"
  - "Alert events (StopHitAlert, TargetReachedAlert) defined in execution domain for future event bus integration"

patterns-established:
  - "Command-Handler pattern: dataclass commands + handler class with DI"
  - "Approve-then-execute flow: approve returns dict, execute returns OrderResult"
  - "CLI one-shot monitoring: load positions/portfolio/watchlist, check conditions, print summary panel"

requirements-completed: [EXEC-02, INTF-04]

# Metrics
duration: 6min
completed: 2026-03-12
---

# Phase 04 Plan 03: Trade Approval Flow + Monitoring Alerts Summary

**Human-in-the-loop trade approval CLI with generate->approve->execute lifecycle and one-shot monitoring alerts**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-12T02:04:46Z
- **Completed:** 2026-03-12T02:10:42Z
- **Tasks:** 3/3 completed
- **Files modified:** 9

## Accomplishments
- Execution application layer with command-handler pattern orchestrating full trade lifecycle
- CLI approve command displays Rich table trade plan details with Y/N confirmation and optional modification
- CLI execute command for approved plans with --force option to skip confirmation
- CLI monitor command checks positions for stop conditions, portfolio drawdown alerts, and watchlist price alerts
- 24 new tests (11 approval handler + 6 alert events + 7 CLI behavioral)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for approval flow and alert events** - `8183717` (test)
2. **Task 1 GREEN: Execution application layer implementation** - `49ef08c` (feat)
3. **Task 2: CLI approve/execute/monitor commands with behavioral tests** - `95b1711` (feat)
4. **Task 3: Verify complete Phase 4 trade lifecycle** - checkpoint approved (human-verify)

**Plan metadata:** `18fb1cb` (docs: complete plan)

_TDD approach for Task 1: tests written first (RED), then implementation (GREEN)._

## Files Created/Modified
- `src/execution/application/__init__.py` - Application layer public API
- `src/execution/application/commands.py` - GenerateTradePlanCommand, ApproveTradePlanCommand, ExecuteOrderCommand
- `src/execution/application/handlers.py` - TradePlanHandler with generate/approve/execute methods
- `src/execution/domain/events.py` - Added StopHitAlertEvent, TargetReachedAlertEvent
- `src/execution/domain/__init__.py` - Exported new alert events
- `cli/main.py` - Added approve, execute, monitor commands
- `tests/unit/test_trade_approval.py` - 11 tests for TradePlanHandler lifecycle
- `tests/unit/test_alerts.py` - 6 tests for alert event creation and properties
- `tests/unit/test_cli_approve.py` - 7 tests for CLI approve/execute/monitor commands

## Decisions Made
- TradePlanHandler uses constructor DI for all dependencies (no global state, easy to mock)
- Approve command includes optional quantity/stop-loss modification flow before execution
- Monitor command is one-shot check (not persistent/live) -- real price fetch is a future enhancement
- Alert events defined in execution domain for future event bus integration

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed unused variables and imports in cli/main.py and test file**
- **Found during:** Task 2 (lint verification)
- **Issue:** Unused `result` and `approve_result` variables in approve command, unused `patch` and `BracketSpec` imports in test
- **Fix:** Removed variable assignments and unused imports
- **Files modified:** cli/main.py, tests/unit/test_trade_approval.py
- **Verification:** ruff check passed
- **Committed in:** 95b1711

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Trivial lint cleanup, no scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. Mock mode works without Alpaca credentials.

## Next Phase Readiness
- Complete Phase 4 trade lifecycle implemented (generate -> approve -> execute -> monitor)
- All EXEC and INTF requirements covered
- 523 total tests passing across full test suite
- Human verification checkpoint approved -- all CLI commands verified working
- All 4 phases (12 plans) of v1 milestone complete

## Self-Check: PASSED

All 9 files verified present. All commit hashes (8183717, 49ef08c, 95b1711) confirmed in git log.

---
*Phase: 04-execution-and-interface*
*Completed: 2026-03-12*
