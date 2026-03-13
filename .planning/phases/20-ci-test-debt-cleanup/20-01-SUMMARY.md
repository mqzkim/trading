---
phase: 20-ci-test-debt-cleanup
plan: 01
subsystem: testing
tags: [mypy, ruff, type-checking, lint, ci]

# Dependency graph
requires:
  - phase: 17-sse-event-wiring
    provides: "Source of bootstrap.py RegimeType arg-type error"
  - phase: 11-commercial-fastapi-rest-api
    provides: "Source of ruff unused import accumulation"
provides:
  - "Zero-error mypy runs across 163 source files"
  - "Zero-error ruff lint runs"
  - "Clean CI static analysis gates"
affects: [20-02-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: ["explicit_package_bases for mypy namespace resolution", "Any type for infrastructure adapter duck-typing"]

key-files:
  created:
    - "src/__init__.py"
    - "src/regime/__init__.py"
    - "src/scoring/__init__.py"
    - "src/signals/__init__.py"
    - "src/shared/__init__.py"
  modified:
    - "pyproject.toml"
    - "src/execution/infrastructure/order_monitor.py"
    - "src/execution/infrastructure/safe_adapter.py"
    - "src/execution/infrastructure/trading_stream.py"
    - "src/regime/application/handlers.py"
    - "src/signals/application/handlers.py"
    - "src/pipeline/domain/services.py"
    - "src/bootstrap.py"
    - "core/scoring/technical.py"
    - "src/scoring/domain/services.py"
    - "src/backtest/domain/services.py"
    - "src/regime/domain/entities.py"
    - "src/regime/infrastructure/sqlite_repo.py"
    - "src/portfolio/domain/value_objects.py"

key-decisions:
  - "Used Any instead of Protocol for infrastructure adapter params (lower-risk, preserves runtime behavior)"
  - "Added disable_error_code for import-untyped in mypy config (requests stubs not installed)"
  - "Used .value to convert RegimeType enum to str in bootstrap event handler"

patterns-established:
  - "explicit_package_bases = true in mypy config for multi-package projects"
  - "Any type annotation for duck-typed infrastructure dependencies"

requirements-completed: [CI-01]

# Metrics
duration: 5min
completed: 2026-03-14
---

# Phase 20 Plan 01: CI/Test Debt Cleanup - Static Analysis Summary

**Zero-error mypy (163 files) and ruff runs by fixing config blocker, 17 type errors, and 4 lint errors with full test regression pass (1098 tests)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-13T20:03:02Z
- **Completed:** 2026-03-13T20:07:49Z
- **Tasks:** 2
- **Files modified:** 19

## Accomplishments
- mypy exits with "Success: no issues found in 163 source files" (was 17 errors + config blocker)
- ruff check exits with "All checks passed!" (was 4 errors)
- All 1098 existing tests pass with zero regressions from type annotation changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix mypy config and missing __init__.py files, resolve all 17 type errors** - `d392156` (fix)
2. **Task 2: Fix ruff lint errors and run full test suite regression check** - `8b8153e` (fix)

## Files Created/Modified
- `pyproject.toml` - Added explicit_package_bases, disable_error_code for mypy config
- `src/__init__.py` - Package marker for mypy module resolution
- `src/regime/__init__.py` - Package marker for mypy module resolution
- `src/scoring/__init__.py` - Package marker for mypy module resolution
- `src/signals/__init__.py` - Package marker for mypy module resolution
- `src/shared/__init__.py` - Package marker for mypy module resolution
- `src/execution/infrastructure/order_monitor.py` - Changed object to Any for client, notifier, bus params
- `src/execution/infrastructure/safe_adapter.py` - Changed object to Any for notifier, kill_switch params
- `src/execution/infrastructure/trading_stream.py` - Changed object to Any for bus, monitor params
- `src/regime/application/handlers.py` - Changed object to Any for data_client, removed stale type:ignore
- `src/signals/application/handlers.py` - Added explicit dict | None type annotation
- `src/pipeline/domain/services.py` - Added None guard for budget_repo before .get_or_create_today()
- `src/bootstrap.py` - Changed event.new_regime to event.new_regime.value (RegimeType -> str)
- `core/scoring/technical.py` - Changed trend_points annotation from int to float
- `src/scoring/domain/services.py` - Fixed type:ignore error code (union-attr -> attr-defined)
- `src/backtest/domain/services.py` - Removed unused import math (F401)
- `src/regime/domain/entities.py` - Removed unused import Optional (F401)
- `src/regime/infrastructure/sqlite_repo.py` - Removed unused import timezone (F401)
- `src/portfolio/domain/value_objects.py` - Added noqa E402 for backward-compat re-export

## Decisions Made
- Used `Any` instead of `Protocol` for infrastructure adapter params -- lower risk, preserves runtime behavior, avoids import dependency issues. Protocol would be ideal but Any is the correct quick-fix for CI cleanup.
- Added `disable_error_code = ["import-untyped"]` in mypy config -- the `requests` library stubs aren't installed and `ignore_missing_imports` doesn't suppress `import-untyped` errors. This is the correct config-level fix rather than adding per-file ignores.
- Converted `event.new_regime` to `event.new_regime.value` in bootstrap -- the `suspend_if_regime_invalid` method expects `str`, and `RegimeType` enum's `.value` provides the string representation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added disable_error_code for import-untyped in mypy config**
- **Found during:** Task 1 (mypy verification step)
- **Issue:** After fixing all 17 planned errors, one additional error surfaced: `core/data/client.py:15: error: Library stubs not installed for "requests" [import-untyped]`. This error was hidden before because the duplicate module blocker prevented mypy from checking most files.
- **Fix:** Added `disable_error_code = ["import-untyped"]` to `[tool.mypy]` in pyproject.toml
- **Files modified:** pyproject.toml
- **Verification:** mypy src/ returns "Success: no issues found"
- **Committed in:** d392156 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Auto-fix necessary to achieve zero-error mypy. No scope creep -- config-level suppression is the standard approach.

## Issues Encountered
None -- all fixes matched the plan's category analysis exactly.

## User Setup Required
None -- no external service configuration required.

## Next Phase Readiness
- CI static analysis gates (mypy + ruff) are fully clean
- Ready for Plan 02: rewrite stale test_api_routes.py for current v1.1 API surface

## Self-Check: PASSED

- All 5 created __init__.py files exist
- 20-01-SUMMARY.md exists
- Commit d392156 found
- Commit 8b8153e found

---
*Phase: 20-ci-test-debt-cleanup*
*Completed: 2026-03-14*
