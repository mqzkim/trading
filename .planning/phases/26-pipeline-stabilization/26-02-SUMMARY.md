---
phase: 26-pipeline-stabilization
plan: 02
subsystem: pipeline, dashboard, database
tags: [price-adapter, valuation-adapter, ddd-injection, duckdb, current-price, target-price, pnl]

# Dependency graph
requires:
  - phase: 26-01
    provides: Event bus wiring, ScoreSymbolHandler with DDD adapters, DuckDB upsert sync
provides:
  - PriceAdapter for real-time current_price lookups via DataClient
  - ValuationAdapter for DuckDB intrinsic_value reads
  - Dashboard positions with real current_price and target_price
  - Pipeline _run_plan with injected valuation_reader (no infrastructure imports in domain)
  - Pipeline E2E integration test with mocked externals
affects: [dashboard, pipeline, scoring-expansion, commercial-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [adapter-injection, graceful-fallback, batch-price-fetch]

key-files:
  created:
    - src/dashboard/infrastructure/price_adapter.py
    - src/pipeline/infrastructure/valuation_adapter.py
    - tests/unit/test_price_and_target.py
  modified:
    - src/dashboard/application/queries.py
    - src/dashboard/infrastructure/__init__.py
    - src/pipeline/domain/services.py
    - src/pipeline/infrastructure/__init__.py
    - src/bootstrap.py
    - tests/integration/test_pipeline_e2e.py

key-decisions:
  - "PriceAdapter uses DataClient.get_full(symbol, days=5) for minimal data fetch"
  - "ValuationAdapter opens separate read-only DuckDB connection to avoid lock conflicts"
  - "Pipeline _run_plan uses injected data_client and valuation_reader from handlers dict -- no core.data.client import in domain"
  - "Shared DataClient instance between PriceAdapter and pipeline via bootstrap"

patterns-established:
  - "Adapter injection: infrastructure adapters injected as callables via handlers dict"
  - "Graceful fallback: price -> entry_price, intrinsic_value -> margin heuristic -> 1.2x"
  - "Batch fetch: PriceAdapter.get_latest_prices() for multiple symbols"

requirements-completed: [PIPE-01, PIPE-04, PIPE-05]

# Metrics
duration: 7min
completed: 2026-03-14
---

# Phase 26 Plan 02: Pipeline Data Quality and E2E Stability Summary

**Real market prices via PriceAdapter, valuation-derived target_price via ValuationAdapter, and E2E pipeline integration test with mocked externals**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-14T14:50:13Z
- **Completed:** 2026-03-14T14:57:07Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Dashboard positions show real current_price from DataClient with graceful fallback to entry_price
- Dashboard target_price populated from trade plan take_profit_price (not hardcoded 0.0)
- P&L calculation uses real current_price vs entry_price (pnl_pct and pnl_dollar)
- Pipeline _run_plan uses injected valuation_reader callable for intrinsic_value lookup (DDD-compliant)
- Removed direct core.data.client import from pipeline domain service
- Full pipeline E2E test with mocked externals completes with COMPLETED status

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire real current_price and target_price into dashboard queries**
   - `922f887` (test: RED - failing tests for price adapter and dashboard position data)
   - `0c22f5e` (feat: GREEN - wire real current_price and target_price into dashboard)

2. **Task 2: Fix pipeline _run_plan target_price via injected ValuationAdapter and add E2E test**
   - `eed8687` (test: RED - ValuationAdapter and pipeline E2E orchestrator tests)
   - `f559021` (feat: GREEN - inject valuation_reader and data_client into pipeline domain service)

## Files Created/Modified

- `src/dashboard/infrastructure/price_adapter.py` - PriceAdapter: fetches latest close price from DataClient with graceful fallback
- `src/dashboard/application/queries.py` - _get_positions uses PriceAdapter for current_price, trade_plan_repo for target_price
- `src/dashboard/infrastructure/__init__.py` - Export PriceAdapter
- `src/pipeline/infrastructure/valuation_adapter.py` - ValuationAdapter: reads intrinsic_value from DuckDB valuation_results
- `src/pipeline/domain/services.py` - _run_plan uses injected data_client and valuation_reader; added _get_intrinsic_value helper
- `src/pipeline/infrastructure/__init__.py` - Export ValuationAdapter
- `src/bootstrap.py` - Wire PriceAdapter, data_client, ValuationAdapter into context dict
- `tests/unit/test_price_and_target.py` - 9 unit tests for PriceAdapter and dashboard position data
- `tests/integration/test_pipeline_e2e.py` - 6 new tests for ValuationAdapter and pipeline orchestrator E2E

## Decisions Made

- **PriceAdapter uses minimal data fetch:** `get_full(symbol, days=5)` to minimize API calls while still getting latest close price
- **Separate read-only DuckDB connection:** ValuationAdapter opens its own read-only connection to avoid lock conflicts with the main write connection
- **DDD compliance in domain service:** Removed `from core.data.client import DataClient` from pipeline domain service; data_client is now injected via handlers dict
- **Shared DataClient instance:** Single DataClient instance shared between PriceAdapter and pipeline via bootstrap context

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ValuationAdapter uses data_dir path instead of non-existent duckdb_path()**
- **Found during:** Task 2 (ValuationAdapter creation)
- **Issue:** Plan referenced `self._db_factory.duckdb_path()` but DBFactory has no such method
- **Fix:** Used `os.path.join(self._db_factory.data_dir, "analytics.duckdb")` to construct path
- **Files modified:** src/pipeline/infrastructure/valuation_adapter.py
- **Verification:** ValuationAdapter tests pass with correct DuckDB path
- **Committed in:** eed8687

**2. [Rule 1 - Bug] Pipeline _run_plan created DataClient() directly in domain layer**
- **Found during:** Task 2 (pipeline domain service update)
- **Issue:** `_run_plan` had `from core.data.client import DataClient` -- a DDD violation (infrastructure import in domain)
- **Fix:** Injected `data_client` via handlers dict; bootstrap provides shared DataClient instance
- **Files modified:** src/pipeline/domain/services.py, src/bootstrap.py
- **Verification:** No infrastructure imports in domain service; pipeline E2E tests pass
- **Committed in:** f559021

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both auto-fixes align with plan intent (DDD compliance). No scope creep.

## Issues Encountered

- Pre-existing DuckDB lock conflict (PID 787767 holding analytics.duckdb lock) causes test_bootstrap.py to fail. This is an external process issue documented in 26-01-SUMMARY.md, not related to our changes. All scoring-specific and pipeline tests pass cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Dashboard positions now show real market prices and valuation-derived targets
- Pipeline chain is operationally stable with mocked E2E test coverage
- Event bus, score store, price adapter, and valuation adapter all wired and tested
- Phase 26 (Pipeline Stabilization) is complete -- ready for Phase 27 (Scoring Expansion)
- The DuckDB lock conflict from PID 787767 should be resolved before production use

## Self-Check: PASSED

All 9 key files verified as existing. All 4 task commits verified in git log.

---
*Phase: 26-pipeline-stabilization*
*Completed: 2026-03-14*
