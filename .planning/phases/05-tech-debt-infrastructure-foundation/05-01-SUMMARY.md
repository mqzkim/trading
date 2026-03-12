---
phase: 05-tech-debt-infrastructure-foundation
plan: 01
subsystem: infra
tags: [event-bus, duckdb, sqlite, composition-root, dependency-injection, ddd]

# Dependency graph
requires: []
provides:
  - SyncEventBus for synchronous CLI event routing
  - DBFactory for centralized database path and connection management
  - bootstrap() composition root wiring all bounded contexts
affects: [05-02, 05-03, 06-event-publishing, cli-commands]

# Tech tracking
tech-stack:
  added: [duckdb]
  patterns: [composition-root, factory-pattern, synchronous-event-bus]

key-files:
  created:
    - src/shared/infrastructure/sync_event_bus.py
    - src/shared/infrastructure/db_factory.py
    - src/bootstrap.py
    - tests/unit/test_sync_event_bus.py
    - tests/unit/test_db_factory.py
    - tests/unit/test_bootstrap.py
  modified:
    - src/shared/infrastructure/__init__.py

key-decisions:
  - "SyncEventBus mirrors AsyncEventBus API but fully synchronous for CLI context"
  - "DBFactory uses lazy singleton for DuckDB, string paths for SQLite"
  - "bootstrap() eagerly creates all handlers (CLI startup cost negligible)"
  - "Event subscriptions defined in comments for Phase 6+ activation per RESEARCH pitfall 3"

patterns-established:
  - "Composition Root pattern: single bootstrap() function wires all contexts"
  - "Factory injection: bootstrap(db_factory=...) for test isolation"
  - "All cross-context imports confined to src/bootstrap.py only"

requirements-completed: [INFRA-01, INFRA-02, INFRA-03]

# Metrics
duration: 4min
completed: 2026-03-12
---

# Phase 5 Plan 1: Infrastructure Primitives Summary

**SyncEventBus, DBFactory, and bootstrap() composition root replacing God Orchestrator pattern with DDD dependency injection**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-12T03:33:17Z
- **Completed:** 2026-03-12T03:37:25Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- SyncEventBus with subscribe/publish routing, matching AsyncEventBus API but fully synchronous
- DBFactory centralizing all database paths (SQLite) and connections (DuckDB) from a single data directory
- bootstrap() composition root wiring all 5 handlers (score, signal, regime, portfolio, trade_plan) with injected repositories
- 16 new unit tests (5 SyncEventBus + 5 DBFactory + 6 bootstrap), all passing
- 523 total unit tests passing (up from 499)

## Task Commits

Each task was committed atomically:

1. **Task 1: SyncEventBus and DBFactory (RED)** - `624097f` (test)
2. **Task 1: SyncEventBus and DBFactory (GREEN)** - `353a6f1` (feat)
3. **Task 2: Composition Root bootstrap (RED)** - `679331f` (test)
4. **Task 2: Composition Root bootstrap (GREEN)** - `8e53eee` (feat)

_TDD tasks have separate RED/GREEN commits._

## Files Created/Modified
- `src/shared/infrastructure/sync_event_bus.py` - Synchronous event bus with subscribe/publish
- `src/shared/infrastructure/db_factory.py` - Centralized database path and connection factory
- `src/shared/infrastructure/__init__.py` - Updated exports (SyncEventBus, DBFactory)
- `src/bootstrap.py` - Composition root wiring all bounded contexts
- `tests/unit/test_sync_event_bus.py` - 5 tests for event routing behavior
- `tests/unit/test_db_factory.py` - 5 tests for connection and path management
- `tests/unit/test_bootstrap.py` - 6 tests for context wiring and injection

## Decisions Made
- SyncEventBus mirrors AsyncEventBus API (subscribe/publish) but removes all async/await -- appropriate for CLI synchronous context
- DBFactory uses lazy singleton pattern for DuckDB (analytics.duckdb) and string path generation for SQLite stores
- bootstrap() creates all handlers eagerly -- CLI startup cost is negligible, lazy init deferred to Phase 6+ if API server needs it
- Event subscriptions are defined as comments in bootstrap.py -- will be activated one at a time in Phase 6+ per RESEARCH pitfall 3

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed dataclass kw_only for test event classes**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Test fake event dataclasses inheriting DomainEvent failed because DomainEvent has `occurred_on` with a default value, and Python dataclasses do not allow non-default fields after default fields
- **Fix:** Added `kw_only=True` to test event dataclass decorators, matching the pattern used by all production event classes (e.g., DataIngestedEvent)
- **Files modified:** tests/unit/test_sync_event_bus.py
- **Verification:** All 5 SyncEventBus tests pass
- **Committed in:** 353a6f1 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor test fixture fix. No scope creep.

## Issues Encountered
- Pre-existing broken test discovered: `test_screener.py::TestDuckDBSignalStoreRepository::test_save_persists_signal` fails due to missing DuckDB `scores` table. Logged to deferred-items.md. Not related to this plan.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SyncEventBus, DBFactory, and bootstrap() are ready for consumption by Plans 05-02 (CLI commands) and 05-03 (screener fix)
- Event subscription wiring is prepared but deactivated, ready for Phase 6 activation
- No blockers

---
*Phase: 05-tech-debt-infrastructure-foundation*
*Completed: 2026-03-12*
