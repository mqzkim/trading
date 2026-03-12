---
phase: 05-tech-debt-infrastructure-foundation
plan: 03
subsystem: cli, infra, event-bus
tags: [typer, cli, event-bus, bootstrap, composition-root, ddd]

# Dependency graph
requires:
  - phase: 05-01
    provides: SyncEventBus, DBFactory, bootstrap() composition root
  - phase: 05-02
    provides: ScoreUpdatedEvent creation in handler, DDD boundary enforcement
provides:
  - 3 new CLI commands (ingest, generate-plan, backtest) completing system CLI surface
  - All handler-using CLI commands migrated to bootstrap() context
  - Event bus with active ScoreUpdatedEvent subscription proving infrastructure works
  - Integration test proving end-to-end event routing
affects: [06-live-data, 07-api, cli-commands, event-publishing]

# Tech tracking
tech-stack:
  added: []
  patterns: [lazy-bootstrap-context, event-logging-handler]

key-files:
  created:
    - tests/unit/test_cli_ingest.py
    - tests/unit/test_cli_generate_plan.py
    - tests/unit/test_cli_backtest.py
    - tests/integration/test_event_wiring.py
  modified:
    - cli/main.py
    - src/bootstrap.py
    - tests/unit/test_cli_approve.py
    - tests/unit/test_cli_dashboard.py
    - tests/unit/test_cli_screener.py

key-decisions:
  - "Lazy bootstrap context via _get_ctx() -- bootstrap() called once on first handler-using command"
  - "Event bus wired with minimal logging handler (no side effects) per RESEARCH pitfall 3"
  - "score_events list in context dict for observability of event flow"
  - "regime/score/signal/analyze commands keep existing core/ imports (orchestrator path still functional)"

patterns-established:
  - "Lazy context pattern: _get_ctx() caches bootstrap() result at module level"
  - "Event logging handler: _log_score_event appends to list for tracking without side effects"
  - "Source-module patching: tests patch at import source for lazy-import CLI commands"

requirements-completed: [INFRA-05, INFRA-01, INFRA-07]

# Metrics
duration: 10min
completed: 2026-03-12
---

# Phase 5 Plan 03: Bootstrap CLI & Event Wiring Summary

**3 new CLI commands (ingest, generate-plan, backtest), all handler-using commands migrated to bootstrap() context, and event bus wired with ScoreUpdatedEvent logging handler proving end-to-end infrastructure**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-12T03:45:18Z
- **Completed:** 2026-03-12T03:56:07Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 9

## Accomplishments
- 3 new CLI commands (ingest, generate-plan, backtest) making all system capabilities reachable from CLI
- All handler-using commands (dashboard, screener, approve, execute, monitor) migrated from inline instantiation to bootstrap() context
- Event bus wired with ScoreUpdatedEvent logging handler -- proves publish/subscribe infrastructure works end-to-end
- 15 commands total visible in CLI help (version + 14 functional commands)
- 571 tests passing (full suite green, up from 529 pre-plan)

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1 RED: CLI command tests** - `77a0f27` (test)
2. **Task 1 GREEN: CLI commands + bootstrap migration** - `004bc81` (feat)
3. **Task 2 RED: Event wiring integration test** - `8135185` (test)
4. **Task 2 GREEN: Wire event bus subscription** - `5b1dd33` (feat)
5. **Lint fix** - `ab5ae22` (fix)

_TDD tasks have separate RED/GREEN commits._

## Files Created/Modified

### Created
- `tests/unit/test_cli_ingest.py` - 4 tests for ingest CLI command (tickers, universe, no-args error, failure counts)
- `tests/unit/test_cli_generate_plan.py` - 2 tests for generate-plan command (display, rejection)
- `tests/unit/test_cli_backtest.py` - 2 tests for backtest command (with dates, default dates)
- `tests/integration/test_event_wiring.py` - 5 tests proving event bus works end-to-end

### Modified
- `cli/main.py` - Added ingest, generate-plan, backtest commands; migrated dashboard/screener/approve/execute/monitor to _get_ctx()
- `src/bootstrap.py` - Wired ScoreUpdatedEvent logging handler, added score_events to context dict
- `tests/unit/test_cli_approve.py` - Updated to use bootstrap context injection pattern
- `tests/unit/test_cli_dashboard.py` - Updated to use bootstrap context injection pattern
- `tests/unit/test_cli_screener.py` - Updated to use bootstrap context injection pattern

## Decisions Made
- **Lazy bootstrap context:** `_get_ctx()` helper calls `bootstrap()` once and caches result at module level. Commands that don't need handlers (version, regime, score, signal, analyze) skip bootstrap entirely, keeping startup fast.
- **Event bus minimal wiring:** Following RESEARCH pitfall 3, wired only a logging handler for ScoreUpdatedEvent. No cross-context subscriptions activated. This proves infrastructure works without risking cascading side effects.
- **score_events list in context:** Event handler appends to a mutable list stored in context dict, enabling both observability and test assertions.
- **Core/ commands unchanged:** regime, score, signal, analyze commands keep their existing `core/` imports since the orchestrator path is still functional and full migration to DDD handlers is Phase 6+ work.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated existing CLI tests for bootstrap migration**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Migrating dashboard, screener, approve, execute, monitor to use `_get_ctx()` broke existing tests that patched source-module constructors (SqliteTradePlanRepository, etc.)
- **Fix:** Rewrote test_cli_approve.py, test_cli_dashboard.py, test_cli_screener.py to inject mock context directly into `cli.main._ctx` instead of patching constructors
- **Files modified:** tests/unit/test_cli_approve.py, tests/unit/test_cli_dashboard.py, tests/unit/test_cli_screener.py
- **Verification:** All 31 CLI tests pass
- **Committed in:** `004bc81` (Task 1 GREEN commit)

**2. [Rule 1 - Bug] Removed unused import in _fetch_ohlcv_for_backtest**
- **Found during:** Final verification (ruff check)
- **Issue:** `generate_signals` imported but not used in helper function
- **Fix:** Removed unused import
- **Files modified:** cli/main.py
- **Verification:** ruff check passes clean
- **Committed in:** `ab5ae22`

---

**Total deviations:** 2 auto-fixed (1 blocking test fix, 1 lint bug)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Pre-existing mypy error in `core/scoring/technical.py:42` (incompatible types). Not caused by this plan, not in modified files. Out of scope.

## User Setup Required
None -- no external service configuration required.

## Next Phase Readiness
- Phase 5 complete: all 3 plans executed successfully
- All system capabilities reachable from CLI (15 commands)
- Event bus infrastructure proven -- ready for Phase 6 cross-context activation
- 571 tests passing, full DDD boundary enforcement active
- No blockers for Phase 6 (Live Data & API)

## Self-Check: PASSED

All 4 created files verified present on disk.
All 5 modified files verified present on disk.
All 5 commit hashes verified in git log.

---
*Phase: 05-tech-debt-infrastructure-foundation*
*Completed: 2026-03-12*
