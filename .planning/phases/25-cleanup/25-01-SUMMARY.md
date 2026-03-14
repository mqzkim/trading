---
phase: 25-cleanup
plan: 01
subsystem: dashboard
tags: [cleanup, htmx, jinja2, plotly, ddd, legacy-removal]

# Dependency graph
requires:
  - phase: 24-real-time-integration
    provides: SSE event wiring to React components (React dashboard fully replaces HTMX)
provides:
  - Clean codebase without legacy HTMX/Jinja2/Plotly dashboard code
  - Fixed DDD violation in queries.py (application no longer imports presentation)
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Application layer queries return raw data dicts only (no chart rendering)"

key-files:
  created: []
  modified:
    - src/dashboard/presentation/app.py
    - src/dashboard/application/queries.py
    - src/dashboard/presentation/api_routes.py
    - pyproject.toml
    - tests/unit/test_dashboard_sse.py

key-decisions:
  - "Removed plotly and jinja2 from direct dependencies; jinja2 remains as transitive dep of edgartools"
  - "Fixed DDD violation: queries.py (application) no longer imports from charts.py (presentation)"

patterns-established:
  - "Dashboard backend serves pure JSON data only; all chart rendering done by React frontend"

requirements-completed: [CLNP-01, CLNP-02]

# Metrics
duration: 5min
completed: 2026-03-14
---

# Phase 25 Plan 01: Legacy Cleanup Summary

**Removed 18 legacy HTMX/Jinja2 files and Plotly dependency, fixed DDD layer violation in queries.py**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-14T12:33:08Z
- **Completed:** 2026-03-14T12:37:45Z
- **Tasks:** 2
- **Files modified:** 22 (18 deleted, 4 modified)

## Accomplishments
- Deleted 13 HTML templates, routes.py (342 lines), charts.py (139 lines), and 2 test files (35 tests)
- Fixed DDD layer violation: application/queries.py no longer imports from presentation/charts.py
- Removed plotly and jinja2 from pyproject.toml direct dependencies
- Cleaned up api_routes.py dead .pop() calls and stale HTMX/Plotly references

## Task Commits

Each task was committed atomically:

1. **Task 1: Delete legacy files and update source code** - `937667e` (feat)
2. **Task 2: Remove dependencies and run full verification** - `b3e00eb` (chore)

## Files Created/Modified
- `src/dashboard/presentation/templates/` - DELETED (13 HTML files)
- `src/dashboard/presentation/routes.py` - DELETED (342 lines of HTMX routes)
- `src/dashboard/presentation/charts.py` - DELETED (139 lines of Plotly chart builders)
- `tests/unit/test_dashboard_web.py` - DELETED (30 tests for HTMX routes)
- `tests/unit/test_dashboard_charts.py` - DELETED (5 tests for Plotly charts)
- `src/dashboard/presentation/app.py` - Removed legacy router import and include
- `src/dashboard/application/queries.py` - Removed Plotly chart generation and presentation import
- `src/dashboard/presentation/api_routes.py` - Removed dead .pop() calls and stale references
- `pyproject.toml` - Removed plotly>=6.0 and jinja2>=3.1 dependencies
- `tests/unit/test_dashboard_sse.py` - Fixed SSE endpoint path assertion

## Decisions Made
- Removed plotly and jinja2 from direct dependencies; jinja2 remains installed as transitive dependency of edgartools
- Fixed DDD violation: application/queries.py no longer imports from presentation/charts.py

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed SSE endpoint path in test_dashboard_sse.py**
- **Found during:** Task 2 (full verification)
- **Issue:** test_sse_endpoint_content_type checked for `/dashboard/events` path which was on the deleted HTMX router; SSE endpoint is at `/api/v1/dashboard/events`
- **Fix:** Updated assertion to check `/api/v1/dashboard/events`
- **Files modified:** tests/unit/test_dashboard_sse.py
- **Verification:** All 18 dashboard tests pass
- **Committed in:** b3e00eb (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test was referencing a path from the deleted legacy router. Essential fix for test correctness.

## Issues Encountered
- Pre-existing test failures (13 in CLI/domain tests, 1 in integration, 1 in bootstrap) unrelated to dashboard cleanup -- logged but not addressed per scope boundary rules
- Pre-existing mypy error in src/pipeline/application/handlers.py (union-attr) unrelated to changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- v1.3 Bloomberg Dashboard milestone is complete
- All React dashboard JSON API endpoints work correctly
- No legacy HTMX/Jinja2/Plotly code remains in the codebase

---
*Phase: 25-cleanup*
*Completed: 2026-03-14*
