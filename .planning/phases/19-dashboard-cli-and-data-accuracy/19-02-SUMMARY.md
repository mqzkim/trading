---
phase: 19-dashboard-cli-and-data-accuracy
plan: 02
subsystem: dashboard
tags: [plotly, htmx, fastapi, drawdown, equity-curve, portfolio]

# Dependency graph
requires:
  - phase: 16-web-dashboard
    provides: "Dashboard query handlers and risk page template"
  - phase: 12-safety-infrastructure
    provides: "Portfolio aggregate with drawdown property"
provides:
  - "Risk gauge shows real portfolio drawdown percentage on initial load"
  - "Equity curve accumulates P&L from entry/target price spread"
  - "Graceful degradation to 0.0/empty when no data exists"
affects: [20-ci-test-debt-cleanup]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Portfolio aggregate access via ctx dict pattern (same as OverviewQueryHandler)"
    - "P&L approximation from entry/target price spread for equity curve"

key-files:
  created: []
  modified:
    - src/dashboard/application/queries.py
    - tests/unit/test_dashboard_web.py

key-decisions:
  - "RiskQueryHandler stores self._ctx for portfolio access (matches OverviewQueryHandler pattern)"
  - "Drawdown fraction multiplied by 100 for gauge percentage display"
  - "Equity curve P&L uses take_profit_price as exit proxy (optimistic upper bound, acceptable for v1)"

patterns-established:
  - "Portfolio drawdown access pattern: ctx.get('portfolio_handler')._portfolio_repo.find_by_id('default')"

requirements-completed: [DASH-04, DASH-08]

# Metrics
duration: 3min
completed: 2026-03-13
---

# Phase 19 Plan 02: Dashboard Data Accuracy Summary

**Real portfolio drawdown in risk gauge and cumulative P&L equity curve via entry/target price spread computation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-13T19:03:36Z
- **Completed:** 2026-03-13T19:06:13Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Risk page drawdown gauge now shows real portfolio drawdown percentage from Portfolio aggregate (not hardcoded 0.0)
- Equity curve accumulates P&L from entry/target price spread for executed trades (not flat zero line)
- Both features degrade gracefully to 0.0/empty when no portfolio or trades exist
- All 29 dashboard tests pass including 4 new accuracy tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Add tests for drawdown and equity curve accuracy** - `b5c5b9c` (test -- TDD RED)
2. **Task 2: Fix RiskQueryHandler drawdown and equity curve P&L** - `a9049f5` (fix -- TDD GREEN)

_Note: TDD task -- test commit (RED) followed by implementation commit (GREEN)_

## Files Created/Modified
- `src/dashboard/application/queries.py` - RiskQueryHandler reads real drawdown from Portfolio aggregate; _build_equity_curve computes cumulative P&L
- `tests/unit/test_dashboard_web.py` - 4 new tests: drawdown from portfolio, drawdown no-portfolio fallback, equity curve P&L accumulation, equity curve empty trades

## Decisions Made
- RiskQueryHandler now stores `self._ctx` to access portfolio_handler (same pattern as OverviewQueryHandler)
- Drawdown `portfolio.drawdown` (0.0-1.0 fraction) multiplied by 100 for gauge percentage display (0-20 range)
- Equity curve P&L uses `take_profit_price` as exit price proxy -- optimistic upper bound since `trade_plans` table lacks `exit_price`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 19 complete (both plans done): `trade serve` CLI command + dashboard data accuracy
- Phase 20 (CI/Test Debt Cleanup) can proceed: mypy arg-type error and test_api_routes version mismatch

## Self-Check: PASSED

All files exist, all commits verified.

---
*Phase: 19-dashboard-cli-and-data-accuracy*
*Completed: 2026-03-13*
