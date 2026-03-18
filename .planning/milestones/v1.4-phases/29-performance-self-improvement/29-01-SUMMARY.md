---
phase: 29-performance-self-improvement
plan: 01
subsystem: api, database, domain
tags: [duckdb, brinson-fachler, information-coefficient, kelly, fastapi, attribution]

requires:
  - phase: 28-commercial-api-dashboard
    provides: Dashboard performance page shell, commercial API framework
provides:
  - src/performance/ DDD bounded context (domain, application, infrastructure layers)
  - DuckDB trades table with 17-field schema and auto-increment ID
  - DuckDB proposals table for parameter adjustment workflow
  - Brinson-Fachler 4-level attribution (portfolio/strategy/trade/skill)
  - IC calculation per scoring axis (fundamental/technical/sentiment)
  - Kelly efficiency computation
  - GET /api/v1/performance/attribution endpoint
  - PUT /api/v1/performance/proposals/{id}/approve and /reject endpoints
  - GET /api/v1/performance/proposals/pending and /history endpoints
  - PositionClosedEvent event-driven trade persistence via TradePersistenceHandler
affects: [29-02-PLAN, dashboard-performance-page]

tech-stack:
  added: [scipy]
  patterns: [event-driven-persistence, on-demand-attribution, duckdb-sequence-autoincrement]

key-files:
  created:
    - src/performance/domain/entities.py
    - src/performance/domain/value_objects.py
    - src/performance/domain/services.py
    - src/performance/domain/repositories.py
    - src/performance/application/handlers.py
    - src/performance/infrastructure/duckdb_trade_repository.py
    - src/performance/infrastructure/duckdb_proposal_repository.py
    - src/performance/infrastructure/trade_persistence_handler.py
    - commercial/api/routers/performance.py
    - commercial/api/schemas/performance.py
    - tests/unit/test_performance_trade_repo.py
    - tests/unit/test_brinson_fachler.py
    - tests/unit/test_ic_calculation.py
    - tests/unit/test_kelly_efficiency.py
    - tests/unit/test_position_score_snapshot.py
  modified:
    - src/portfolio/domain/events.py
    - src/portfolio/domain/entities.py
    - commercial/api/main.py
    - commercial/api/dependencies.py
    - src/bootstrap.py

key-decisions:
  - "DuckDB sequence for trades table auto-increment ID (CREATE SEQUENCE trades_id_seq)"
  - "scipy.stats.spearmanr for IC calculation -- standard library, no custom rank implementation"
  - "Kelly efficiency uses 1/4 fractional Kelly per project risk rules"
  - "Sortino ratio in performance domain services (not core/backtest) to avoid modifying stable backtest module"
  - "All PositionClosedEvent fields have defaults for backward compatibility"

patterns-established:
  - "Event-driven trade persistence: PositionClosedEvent -> TradePersistenceHandler -> DuckDB"
  - "On-demand attribution: compute at request time, no caching or scheduled jobs"
  - "Score snapshot capture: Position entity stores score_snapshot dict from entry, passed through to PositionClosedEvent"

requirements-completed: [PERF-01, PERF-02, PERF-03, PERF-04, PERF-05]

duration: 6min
completed: 2026-03-17
---

# Phase 29 Plan 01: Performance Backend Summary

**DuckDB trade persistence with Brinson-Fachler 4-level attribution, IC/Kelly validation, and commercial API endpoint**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-17T20:25:00Z
- **Completed:** 2026-03-17T20:31:00Z
- **Tasks:** 3
- **Files modified:** 22

## Accomplishments
- Built complete src/performance/ DDD bounded context with domain/application/infrastructure layers
- Extended PositionOpenedEvent with score_snapshot and PositionClosedEvent with full trade context (11 new fields)
- Implemented Brinson-Fachler 4-level attribution, Spearman IC per axis, Kelly efficiency services
- DuckDB trades table (17 fields) and proposals table with CRUD operations
- GET /api/v1/performance/attribution endpoint with KPIs, brinson_table, signal_ic, kelly_efficiency
- Proposal approve/reject/pending/history endpoints
- Event-driven trade persistence wired in bootstrap.py
- All 15 unit tests pass, mypy 0 new errors, ruff 0 errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Test scaffolds (Wave 0)** - `14d049c` (test)
2. **Task 2: Performance DDD context + portfolio event extensions** - `36e62ed` (feat)
3. **Task 3: Commercial API router + bootstrap wiring** - `ccf32f8` (feat)

## Files Created/Modified
- `src/performance/domain/entities.py` - ClosedTrade entity with 17 fields
- `src/performance/domain/value_objects.py` - AttributionLevel, PerformanceReport VOs
- `src/performance/domain/services.py` - BrinsonFachler, IC, Kelly, compute_sortino services
- `src/performance/domain/repositories.py` - ITradeHistoryRepository, IProposalRepository ABCs
- `src/performance/application/handlers.py` - AttributionHandler with approve/reject
- `src/performance/infrastructure/duckdb_trade_repository.py` - DuckDB trades CRUD
- `src/performance/infrastructure/duckdb_proposal_repository.py` - DuckDB proposals CRUD
- `src/performance/infrastructure/trade_persistence_handler.py` - PositionClosedEvent handler
- `commercial/api/routers/performance.py` - 5 performance endpoints
- `commercial/api/schemas/performance.py` - Pydantic response schemas
- `src/portfolio/domain/events.py` - Extended PositionOpenedEvent/PositionClosedEvent
- `src/portfolio/domain/entities.py` - Position.score_snapshot + enriched close()
- `commercial/api/main.py` - Registered performance router
- `commercial/api/dependencies.py` - Added get_attribution_handler
- `src/bootstrap.py` - Wired trade history repo, proposal repo, attribution handler, event subscription

## Decisions Made
- DuckDB sequence for auto-increment trade IDs (not TEXT PRIMARY KEY as context suggested)
- scipy installed for Spearman IC calculation
- Sortino ratio added to performance domain services, not core/backtest (avoids modifying stable module)
- PositionClosedEvent extended with defaults for backward compatibility (not new event type)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed scipy dependency**
- **Found during:** Task 2 (IC calculation service)
- **Issue:** scipy.stats.spearmanr import failed -- scipy not installed
- **Fix:** pip install scipy
- **Verification:** IC calculation tests pass with real Spearman correlation
- **Committed in:** 36e62ed (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** scipy is listed in RESEARCH.md as standard stack. No scope creep.

## Issues Encountered
- 2 pre-existing mypy errors (pipeline handler union-attr, main.py rate limit type) -- not caused by this plan, out of scope

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Performance backend complete, ready for 29-02 (self-improvement proposals, dashboard integration)
- All 5 PERF requirements satisfied with passing tests
- Attribution endpoint returns empty state for < 50 trades as specified

---
*Phase: 29-performance-self-improvement*
*Completed: 2026-03-17*
