---
phase: 08-market-regime-detection
plan: 02
subsystem: regime
tags: [regime-detection, scoring-weights, event-bus, cli-rewiring, weight-adjustment]

# Dependency graph
requires:
  - phase: 08-01
    provides: DetectRegimeHandler with data fetching, 3-day confirmation, and RegimeChangedEvent publishing
  - phase: 07
    provides: CLI score command DDD pattern, CompositeScoringService with RegimeWeightAdjuster protocol
provides:
  - ConcreteRegimeWeightAdjuster with regime-specific scoring weight distributions
  - RegimeChangedEvent subscription wiring scoring weight adjuster in bootstrap.py
  - CLI regime command rewired through DDD handler with --history flag
affects: [scoring, signals, commercial-api]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Regime-specific weight maps: REGIME_SCORING_WEIGHTS overrides STRATEGY_WEIGHTS per regime"
    - "EventBus cross-context subscription: scoring adjuster listens to regime events"
    - "CLI --history N flag queries repository for past regime transitions"

key-files:
  created:
    - tests/unit/test_regime_weight_adjustment.py
    - tests/unit/test_cli_regime_ddd.py
  modified:
    - src/scoring/domain/services.py
    - src/bootstrap.py
    - cli/main.py
    - tests/unit/test_cli_commands.py

key-decisions:
  - "REGIME_SCORING_WEIGHTS placed in scoring domain services (not value_objects) -- weights are behavior, not data"
  - "ConcreteRegimeWeightAdjuster caches regime via on_regime_changed() for implicit use in adjust_weights()"
  - "CLI regime --history accesses handler._regime_repo directly for simplicity (no new query handler)"

patterns-established:
  - "Cross-context event subscription: regime events update scoring weights automatically"
  - "CLI history pattern: --history N flag with find_by_date_range for temporal queries"

requirements-completed: [REGIME-04, REGIME-05]

# Metrics
duration: 5min
completed: 2026-03-12
---

# Phase 08 Plan 02: Regime Scoring Weights and CLI Rewiring Summary

**ConcreteRegimeWeightAdjuster shifts scoring weights by regime (Bull tech 45%, Bear fund 55%, Crisis 60%), wired via EventBus; CLI regime command rewired through DDD handler with --history flag**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-12T10:39:22Z
- **Completed:** 2026-03-12T10:44:09Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- ConcreteRegimeWeightAdjuster returns 4 regime-specific weight distributions (Bull/Bear/Sideways/Crisis)
- EventBus subscription wires regime changes to scoring weight adjustments automatically
- CLI regime command fully rewired from legacy core.regime to DDD handler pattern
- CLI --history N flag shows regime transition history with dates, types, confidence
- 694 tests pass, lint clean

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for weight adjuster** - `b4b5c47` (test)
2. **Task 1 GREEN: ConcreteRegimeWeightAdjuster + bootstrap wiring** - `992e32d` (feat)
3. **Task 2 RED: Failing tests for CLI regime DDD** - `e64761d` (test)
4. **Task 2 GREEN: CLI regime rewired through DDD handler** - `4c38131` (feat)
5. **Task 3: Regression fix for existing tests** - `07446ec` (fix)

## Files Created/Modified
- `src/scoring/domain/services.py` - ConcreteRegimeWeightAdjuster with REGIME_SCORING_WEIGHTS map
- `src/bootstrap.py` - RegimeChangedEvent subscription to regime_adjuster.on_regime_changed
- `cli/main.py` - Regime command rewired through DDD handler, added --history flag
- `tests/unit/test_regime_weight_adjustment.py` - 8 tests for weight adjuster and EventBus subscription
- `tests/unit/test_cli_regime_ddd.py` - 5 tests for CLI DDD rewiring and history flag
- `tests/unit/test_cli_commands.py` - Updated TestRegimeCommand to use DDD handler mocks

## Decisions Made
- REGIME_SCORING_WEIGHTS placed in scoring domain services.py (co-located with the adjuster that uses it)
- ConcreteRegimeWeightAdjuster caches regime via on_regime_changed() event handler, enabling implicit regime-aware scoring without passing regime_type on every call
- CLI regime --history accesses handler._regime_repo.find_by_date_range directly for simplicity (no separate query handler needed for this read-only operation)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated TestRegimeCommand to DDD handler pattern**
- **Found during:** Task 3 (Full regression)
- **Issue:** Existing test_cli_commands.py TestRegimeCommand mocked legacy core.regime imports that no longer exist in regime function
- **Fix:** Rewrote TestRegimeCommand to mock _get_ctx() with regime_handler returning Ok() (same pattern as Phase 7's TestScoreCommand update)
- **Files modified:** tests/unit/test_cli_commands.py
- **Verification:** Full test suite passes (694 tests)
- **Committed in:** 07446ec

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Fix necessary for test compatibility after CLI rewiring. No scope creep.

## Issues Encountered
- Pre-existing test_api_routes.py import error (missing fastapi) -- out of scope, not caused by this plan's changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Regime detection fully wired end-to-end: data fetch -> detection -> confirmation -> event -> scoring weight adjustment
- CLI provides both current detection and historical view
- Phase 08 complete -- ready for Phase 09

## Self-Check: PASSED

All 6 files verified present. All 5 commit hashes verified in git log.

---
*Phase: 08-market-regime-detection*
*Completed: 2026-03-12*
