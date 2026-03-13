---
phase: 16-web-dashboard
plan: 03
subsystem: ui
tags: [htmx, jinja2, plotly, tailwind, scoring, risk, signals, dashboard]

# Dependency graph
requires:
  - phase: 16-web-dashboard
    provides: "Dashboard foundation (app factory, base template, SSE bridge, chart utilities)"
provides:
  - "SignalsQueryHandler fetching scores + active signals with sortable output"
  - "RiskQueryHandler fetching positions, sector weights, regime, and Plotly chart JSON"
  - "Signals page with heatmap-styled scoring table and signal recommendation cards"
  - "Risk page with drawdown gauge, sector donut, position limits bar, regime badge"
affects: [16-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [Heatmap bg-color via Jinja2 conditionals on score thresholds, Plotly tojson inline rendering]

key-files:
  created: []
  modified:
    - src/dashboard/application/queries.py
    - src/dashboard/presentation/routes.py
    - src/dashboard/presentation/templates/signals.html
    - src/dashboard/presentation/templates/risk.html
    - src/dashboard/presentation/templates/partials/drawdown_gauge.html
    - src/dashboard/presentation/templates/partials/regime_badge.html
    - tests/unit/test_dashboard_web.py
    - src/bootstrap.py

key-decisions:
  - "SignalsQueryHandler uses score_repo.find_all_latest() returning dict[str, CompositeScore] and maps to flat dicts for template"
  - "RiskQueryHandler calculates sector weights from position entry_price * quantity (no live price feed in v1)"
  - "Drawdown defaults to 0.0 without Portfolio aggregate in ctx -- SSE updates provide real-time values"
  - "signal_repo added to bootstrap ctx dict for dashboard query access"

patterns-established:
  - "Heatmap scoring: Jinja2 conditionals apply Tailwind bg-color classes based on composite score thresholds (>80, >60, >40)"
  - "Plotly inline rendering: {{ chart_json | tojson }} passed to Plotly.newPlot in script tag"

requirements-completed: [DASH-02, DASH-04]

# Metrics
duration: 4min
completed: 2026-03-13
---

# Phase 16 Plan 03: Signals + Risk Pages Summary

**Scoring heatmap table with sortable columns and signal recommendations, plus risk dashboard with Plotly drawdown gauge, sector donut chart, position limits bar, and color-coded regime badge**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-13T15:20:26Z
- **Completed:** 2026-03-13T15:24:30Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- SignalsQueryHandler and RiskQueryHandler with full data aggregation from score, signal, position, and regime repos
- Signals page with heatmap-styled scoring table (bg-green/yellow/red based on composite score) and signal recommendation cards
- Risk page with Plotly drawdown gauge (0-20% with tier markers), sector donut chart, position limits progress bar, and regime badge
- 7 new tests (18 total passing) covering scoring table, empty states, gauge, regime badge, sector chart, and position limits

## Task Commits

Each task was committed atomically:

1. **Task 1: Signals + Risk query handlers and route wiring** - `cb46de2` (feat)
2. **Task 2: Signals + Risk page templates and tests** - `66de1af` (feat)

## Files Created/Modified
- `src/dashboard/application/queries.py` - Added SignalsQueryHandler and RiskQueryHandler classes
- `src/dashboard/presentation/routes.py` - Wired signals/risk routes to query handlers with sort params
- `src/dashboard/presentation/templates/signals.html` - Scoring table with heatmap + signal recommendation cards
- `src/dashboard/presentation/templates/risk.html` - 2-column layout with gauge, donut, limits, regime badge
- `src/dashboard/presentation/templates/partials/drawdown_gauge.html` - Plotly gauge with SSE swap target
- `src/dashboard/presentation/templates/partials/regime_badge.html` - Color-coded badge (Bull=green, Bear=red, etc.)
- `tests/unit/test_dashboard_web.py` - 7 new tests for signals/risk pages
- `src/bootstrap.py` - Added signal_repo to ctx dict

## Decisions Made
- SignalsQueryHandler maps CompositeScore VOs to flat dicts for template rendering simplicity
- RiskQueryHandler calculates sector weights from entry_price * quantity since no live price feed exists in v1
- Drawdown defaults to 0.0 (real-time SSE updates will provide actual values)
- Added signal_repo to bootstrap ctx for dashboard query access (was missing)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added signal_repo to bootstrap ctx**
- **Found during:** Task 1 (query handler implementation)
- **Issue:** signal_repo was not exposed in bootstrap ctx dict, preventing SignalsQueryHandler from accessing it
- **Fix:** Added "signal_repo": signal_repo to ctx dict in bootstrap.py
- **Files modified:** src/bootstrap.py
- **Verification:** SignalsQueryHandler instantiation and handle() succeeds with mock ctx
- **Committed in:** cb46de2 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Auto-fix necessary for query handler to access signal data. No scope creep.

## Issues Encountered
- Pre-existing mypy configuration issue (duplicate module names for dashboard package) -- not introduced by this plan, out of scope

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Signals and risk pages fully populated with data from query handlers
- Plan 04 can populate pipeline page and wire SSE real-time updates
- All 4 dashboard pages now have content (overview from 16-02, signals + risk from 16-03)

---
*Phase: 16-web-dashboard*
*Completed: 2026-03-13*
