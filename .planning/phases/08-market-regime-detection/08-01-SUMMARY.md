---
phase: 08-market-regime-detection
plan: 01
subsystem: regime
tags: [regime-detection, event-bus, confirmation-logic, adx, yfinance, ddd-handler]

# Dependency graph
requires:
  - phase: 06-live-data-pipeline
    provides: RegimeDataClient with VIX/S&P500/yield data fetching
  - phase: 05-tech-debt
    provides: SyncEventBus, bootstrap wiring, DDD handler pattern
provides:
  - DetectRegimeHandler with data fetching, 3-day confirmation, and RegimeChangedEvent publishing
  - RegimeDataClient extended with ADX computation from S&P500 OHLCV
  - bootstrap.py bus injection into regime handler
affects: [08-02 (CLI rewiring, scoring weight adjustment), scoring, signals]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "3-day confirmation state machine via find_latest() in handler"
    - "Last-confirmed-regime tracking for event deduplication"
    - "ADX computed from S&P500 OHLCV using core.data.indicators.adx()"

key-files:
  created:
    - tests/unit/test_regime_handler_wiring.py
    - tests/unit/test_regime_confirmation.py
    - tests/unit/test_regime_event_publish.py
  modified:
    - src/regime/application/handlers.py
    - src/data_ingest/infrastructure/regime_data_client.py
    - src/bootstrap.py
    - tests/unit/test_regime_data_client.py

key-decisions:
  - "Confirmation state tracked via _last_confirmed_type instance variable for accurate event previous_regime field"
  - "ADX added to RegimeDataClient.fetch_regime_snapshot() rather than computed in handler to keep data fetching in infrastructure"
  - "yield_spread (percentage) added alongside yield_spread_bps for handler compatibility"

patterns-established:
  - "Confirmation state machine: handler loads find_latest(), compares regime_type, increments or resets confirmed_days"
  - "Event deduplication: _last_confirmed_type tracks last confirmed regime to prevent duplicate events on continued confirmation"

requirements-completed: [REGIME-01, REGIME-02, REGIME-03]

# Metrics
duration: 6min
completed: 2026-03-12
---

# Phase 08 Plan 01: Regime Handler Wiring Summary

**DetectRegimeHandler wired with RegimeDataClient fallback (including ADX from S&P500 OHLCV), 3-day confirmation state machine, and RegimeChangedEvent publishing via SyncEventBus**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-12T10:30:14Z
- **Completed:** 2026-03-12T10:36:09Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- DetectRegimeHandler now fetches data via RegimeDataClient fallback pattern when sentinel zeros provided
- 3-day confirmation state machine: confirmed_days increments for same-regime, resets for different-regime
- RegimeChangedEvent published only on confirmed (>=3 days) regime transitions with correct previous/new regime fields
- RegimeDataClient extended with ADX(14) computed from S&P500 OHLCV data
- bootstrap.py passes bus to DetectRegimeHandler for cross-context event publishing
- 12 new tests covering data fetching, confirmation logic, and event publishing behavior

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests** - `5e97651` (test)
2. **Task 1 GREEN: Handler + data client implementation** - `27ed369` (feat)
3. **Task 2: Full regression + test fix** - `6abd821` (fix)

## Files Created/Modified
- `src/regime/application/handlers.py` - DetectRegimeHandler with bus/data_client injection, data-fetch fallback, 3-day confirmation, event publishing
- `src/data_ingest/infrastructure/regime_data_client.py` - ADX computation from S&P500 OHLCV added to fetch_regime_snapshot()
- `src/bootstrap.py` - DetectRegimeHandler wired with bus=bus
- `tests/unit/test_regime_handler_wiring.py` - 3 tests for data fetching (explicit, fallback, injected client)
- `tests/unit/test_regime_confirmation.py` - 5 tests for 3-day confirmation state machine
- `tests/unit/test_regime_event_publish.py` - 4 tests for EventBus publishing behavior
- `tests/unit/test_regime_data_client.py` - Updated expected keys for adx and yield_spread

## Decisions Made
- Confirmation state tracked via `_last_confirmed_type` instance variable for accurate `previous_regime` field in events (looking back through unconfirmed entries would require additional repo queries)
- ADX added directly to RegimeDataClient.fetch_regime_snapshot() to keep data fetching in infrastructure layer
- yield_spread (percentage) added alongside yield_spread_bps for DetectRegimeCommand compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing RegimeDataClient test for new keys**
- **Found during:** Task 2 (Full regression)
- **Issue:** test_regime_data_client.py expected 8 keys in snapshot; now returns 10 (adx + yield_spread added)
- **Fix:** Added "adx" and "yield_spread" to expected_keys set in test
- **Files modified:** tests/unit/test_regime_data_client.py
- **Verification:** Full test suite passes (681 tests)
- **Committed in:** 6abd821

**2. [Rule 1 - Bug] Fixed event previous_regime field accuracy**
- **Found during:** Task 1 GREEN (test 12 failing)
- **Issue:** When Bear becomes confirmed after Bull, `previous` points to Bear day 2 (not Bull), producing wrong previous_regime
- **Fix:** Added `_last_confirmed_type` instance variable to track last confirmed regime type across calls
- **Files modified:** src/regime/application/handlers.py
- **Verification:** All 12 tests pass including event field correctness test
- **Committed in:** 27ed369

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Pre-existing lint warnings in src/regime/domain/entities.py and src/regime/infrastructure/sqlite_repo.py (unused imports) -- out of scope, not caused by this plan's changes
- Pre-existing test_api_routes.py import error (missing fastapi) -- out of scope

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Handler fully wired with data fetching, confirmation, and event publishing
- Ready for Plan 02: CLI rewiring and scoring weight adjustment
- RegimeChangedEvent subscription slot in bootstrap.py ready for scoring context wiring

## Self-Check: PASSED

All 8 files verified present. All 3 commit hashes verified in git log.

---
*Phase: 08-market-regime-detection*
*Completed: 2026-03-12*
