---
phase: 20-ci-test-debt-cleanup
plan: 02
subsystem: testing
tags: [pytest, fastapi, api-routes, smoke-tests]

# Dependency graph
requires:
  - phase: 11-commercial-fastapi-rest-api
    provides: v1.1 API with versioned routes and JWT auth
provides:
  - Passing smoke tests for API route registration and health endpoint
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [smoke-test-pattern-for-route-registration]

key-files:
  created: []
  modified:
    - tests/unit/test_api_routes.py

key-decisions:
  - "Auth route test uses /api/v1/auth/token (actual route) instead of /register (does not exist)"

patterns-established:
  - "Route registration smoke tests: assert non-404 to verify route exists without auth"

requirements-completed: [CI-02]

# Metrics
duration: 2min
completed: 2026-03-14
---

# Phase 20 Plan 02: Rewrite test_api_routes.py Summary

**Replaced 303-line stale pre-v1.1 test file with 9 minimal smoke tests for current API surface**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-13T20:03:04Z
- **Completed:** 2026-03-13T20:04:38Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Rewrote test_api_routes.py from 303 lines (stale mock-heavy tests) to 62 lines (clean smoke tests)
- All 9 tests pass: health endpoint (3), route registration (4), DISCLAIMER constant (2)
- Zero overlap with existing test_api_v1_*.py comprehensive test coverage

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite test_api_routes.py for current v1.1 API surface** - `17efad9` (fix)

## Files Created/Modified
- `tests/unit/test_api_routes.py` - Smoke tests: health returns 1.1.0, v1 routes registered (non-404), DISCLAIMER importable

## Decisions Made
- Auth route test uses `/api/v1/auth/token` (actual POST endpoint) instead of `/api/v1/auth/register` (does not exist in the API)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed non-existent auth register route in test**
- **Found during:** Task 1 (Rewrite test_api_routes.py)
- **Issue:** Plan specified testing `POST /api/v1/auth/register` but this route does not exist; auth router has `/token`, `/keys` endpoints
- **Fix:** Changed test to use `POST /api/v1/auth/token` which is the actual auth endpoint
- **Files modified:** tests/unit/test_api_routes.py
- **Verification:** All 9 tests pass
- **Committed in:** 17efad9

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor correction to match actual API surface. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All test_api_routes.py tests pass alongside existing test_api_v1_*.py suite
- CI test debt cleanup phase can proceed to completion

## Self-Check: PASSED

- FOUND: tests/unit/test_api_routes.py (68 lines, min_lines=30)
- FOUND: commit 17efad9
- 9/9 tests passing

---
*Phase: 20-ci-test-debt-cleanup*
*Completed: 2026-03-14*
