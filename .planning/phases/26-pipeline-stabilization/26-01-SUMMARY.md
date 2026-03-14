---
phase: 26-pipeline-stabilization
plan: 01
subsystem: scoring, events, database
tags: [event-bus, duckdb, sqlite, ddd-adapters, upsert-sync]

# Dependency graph
requires:
  - phase: v1.3
    provides: ScoreSymbolHandler, SyncEventBus, SqliteScoreRepository, DuckDBSignalStore
provides:
  - ScoreSymbolHandler with bus injection and event publishing
  - Sub-score persistence in SQLite (fundamental, technical, sentiment, f/z/m)
  - Event-driven per-symbol DuckDB sync via ScoreUpdatedEvent
  - FundamentalDataAdapter, SentimentDataAdapter, TechnicalIndicatorAdapter.get()
affects: [26-02-PLAN, pipeline-e2e, screener, dashboard]

# Tech tracking
tech-stack:
  added: []
  patterns: [event-driven-sync, adapter-pattern, upsert-semantics]

key-files:
  created:
    - tests/unit/test_scoring_store_sync.py
    - tests/integration/test_event_bus_e2e.py
  modified:
    - src/scoring/application/handlers.py
    - src/scoring/infrastructure/sqlite_repo.py
    - src/scoring/infrastructure/core_scoring_adapter.py
    - src/scoring/infrastructure/__init__.py
    - src/scoring/infrastructure/in_memory_repo.py
    - src/scoring/domain/repositories.py
    - src/signals/infrastructure/duckdb_signal_store.py
    - src/bootstrap.py
    - tests/unit/test_score_handler_events.py

key-decisions:
  - "Event-driven per-symbol upsert sync instead of bulk delete+reinsert for DuckDB"
  - "FundamentalDataAdapter/SentimentDataAdapter wrap core/ imports in infrastructure layer"
  - "Bus parameter defaults to None for backward compatibility"

patterns-established:
  - "Event-driven sync: subscribe to domain event, sync single record via upsert"
  - "Adapter pattern: wrap core/ scoring functions behind .get(symbol) interface"

requirements-completed: [PIPE-02, PIPE-03, PIPE-06]

# Metrics
duration: 17min
completed: 2026-03-14
---

# Phase 26 Plan 01: Score Store Unification Summary

**Event bus wired into ScoreSymbolHandler with DDD adapter injection, sub-score persistence in SQLite, and event-driven per-symbol DuckDB upsert sync**

## Performance

- **Duration:** 17 min
- **Started:** 2026-03-14T14:29:35Z
- **Completed:** 2026-03-14T14:46:35Z
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments
- ScoreSymbolHandler publishes ScoreUpdatedEvent via injected bus on every successful scoring
- DDD adapters (FundamentalDataAdapter, TechnicalIndicatorAdapter, SentimentDataAdapter) replace inline core/ imports in the handler
- SQLite score repo persists all sub-scores (fundamental, technical, sentiment, f_score, z_score, m_score)
- DuckDB scores table auto-updates via event-driven per-symbol upsert sync
- Event bus has 5 active subscriptions: ScoreUpdatedEvent logger, ScoreUpdatedEvent DuckDB sync, RegimeChangedEvent adjuster, RegimeChangedEvent approval, DrawdownAlertEvent approval

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire event bus into ScoreSymbolHandler and inject DDD adapters**
   - `5fa8422` (test: RED - failing tests for bus publishing and adapter injection)
   - `9103d46` (feat: GREEN - wire event bus and inject DDD adapters)

2. **Task 2: Unify scoring store -- SQLite as authority, auto-sync to DuckDB**
   - `e49989c` (test: RED - failing tests for sub-score persistence and DuckDB upsert)
   - `aa9178d` (feat: GREEN - sub-score persistence and event-driven DuckDB sync)

3. **Task 3: Verify event bus end-to-end with integration test**
   - `5659a78` (test: integration test for event bus E2E wiring)

## Files Created/Modified

- `src/scoring/application/handlers.py` - Added bus parameter, event publishing, sub-score details in save()
- `src/scoring/infrastructure/sqlite_repo.py` - Sub-score persistence columns, find_all_latest_for_sync()
- `src/scoring/infrastructure/core_scoring_adapter.py` - FundamentalDataAdapter, SentimentDataAdapter, TechnicalIndicatorAdapter.get()
- `src/scoring/infrastructure/__init__.py` - Export new adapters
- `src/scoring/infrastructure/in_memory_repo.py` - Updated save() signature for details param
- `src/scoring/domain/repositories.py` - Updated IScoreRepository.save() with optional details
- `src/signals/infrastructure/duckdb_signal_store.py` - sync_scores() uses INSERT OR REPLACE upsert
- `src/bootstrap.py` - Wired bus, DDD adapters, and DuckDB sync subscriber into ScoreSymbolHandler
- `tests/unit/test_score_handler_events.py` - Added TestBusPublishing and TestAdapterInjection classes
- `tests/unit/test_scoring_store_sync.py` - New test file for sub-score persistence and DuckDB upsert
- `tests/integration/test_event_bus_e2e.py` - New integration test for event bus wiring

## Decisions Made

- **Event-driven per-symbol upsert sync:** Instead of bulk delete+reinsert, each ScoreUpdatedEvent triggers a single-row upsert to DuckDB. This prevents data loss during per-symbol scoring and is more efficient for incremental updates.
- **Adapter pattern for data fetching:** Created FundamentalDataAdapter and SentimentDataAdapter in infrastructure layer to wrap core/ imports. TechnicalIndicatorAdapter got a `.get(symbol)` method. This keeps the handler free of direct core/ imports while maintaining the same data flow.
- **Backward-compatible bus injection:** Bus defaults to None so all existing code (tests, CLI commands) continues to work without modification.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pre-existing DuckDB lock conflict (PID 787767 holding analytics.duckdb lock) caused test_bootstrap.py to fail. This is an external process issue, not related to our changes. Scoring-specific mypy and tests all pass cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Event bus is fully wired with 5 active subscriptions
- SQLite is the authoritative score store with complete sub-scores
- DuckDB auto-syncs on every scoring via event-driven upsert
- Ready for Plan 02 (pipeline E2E testing) -- the store mismatch and dead-letter event issues are resolved

## Self-Check: PASSED

All 8 key files verified as existing. All 5 task commits verified in git log.

---
*Phase: 26-pipeline-stabilization*
*Completed: 2026-03-14*
