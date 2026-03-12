---
phase: 07-technical-scoring-engine
plan: 03
subsystem: scoring
tags: [cli, ddd, handler, composite-weights, technical-indicators, gap-closure]

# Dependency graph
requires:
  - phase: 07-technical-scoring-engine (07-01, 07-02)
    provides: TechnicalScoringService domain service, ScoreSymbolHandler with sub-score wiring, TechnicalIndicatorAdapter
provides:
  - CLI score command routed through ScoreSymbolHandler (DDD handler)
  - Handler fallback fetches OHLCV + compute_all + returns raw indicators for sub-scoring
  - Legacy composite weights updated to 40/40/20 (safety net)
  - End-to-end sub-score flow from handler to CLI display
affects: [08-regime-detection, commercial-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [cli-through-ddd-handler, handler-fallback-raw-indicators]

key-files:
  created: []
  modified:
    - cli/main.py
    - core/scoring/composite.py
    - src/scoring/application/handlers.py
    - tests/unit/test_cli_score_technical.py
    - tests/unit/test_cli_commands.py

key-decisions:
  - "CLI score command uses ctx['score_handler'].handle() instead of legacy score_symbol()"
  - "Handler fallback fetches OHLCV, calls compute_all, merges raw indicator values for sub-score detection"
  - "Err result accessed via .error attribute (not unwrap_err method)"
  - "Regime detection kept as informational context in CLI, not part of scoring flow"

patterns-established:
  - "CLI commands route through DDD handlers via bootstrap context, not legacy core/ functions"
  - "Handler fallback pattern: when no injected client, fetch data inline and merge raw values"

requirements-completed: [TECH-01, TECH-02, TECH-03, TECH-04]

# Metrics
duration: 6min
completed: 2026-03-12
---

# Phase 7 Plan 3: Gap Closure Summary

**CLI score command rewired through DDD ScoreSymbolHandler with fixed handler fallback producing 5 technical sub-scores end-to-end**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-12T08:42:17Z
- **Completed:** 2026-03-12T08:48:08Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- CLI score command now routes through ScoreSymbolHandler.handle() instead of legacy core.scoring.composite.score_symbol()
- Handler _get_technical() fallback correctly fetches OHLCV, computes indicators via compute_all(), and returns raw values (rsi, macd_histogram, adx, obv_change_pct) enabling sub-score detection
- core/scoring/composite.py WEIGHTS["swing"] updated from 35/40/25 to 40/40/20 (safety net for analyze command)
- Previously dead sub-table rendering code in CLI is now active -- users see 5 technical indicator scores with explanations
- All 669 tests pass, lint clean, all 3 key links verified

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Add failing tests** - `4a28094` (test)
2. **Task 1 GREEN: Wire CLI + fix fallback + update weights** - `f8f5288` (feat)
3. **Task 2: Fix Err.error access + update CLI test mocks** - `1c9e29d` (fix)

**Plan metadata:** (pending)

_Note: Task 1 used TDD flow (RED -> GREEN). No REFACTOR phase needed._

## Files Created/Modified
- `cli/main.py` - Score command rewired through DDD handler, regime as informational context
- `core/scoring/composite.py` - WEIGHTS["swing"] updated to 40/40/20
- `src/scoring/application/handlers.py` - _get_technical() fallback fixed to fetch OHLCV + compute_all + merge raw values
- `tests/unit/test_cli_score_technical.py` - Added 3 gap closure tests (integration, AST, error handling)
- `tests/unit/test_cli_commands.py` - Updated TestScoreCommand to mock DDD handler path

## Decisions Made
- CLI score command uses `ctx["score_handler"].handle(ScoreSymbolCommand(...))` instead of legacy `score_symbol()` -- this closes the gap where the domain layer was implemented but never called from the CLI
- Handler fallback merges raw indicator values into the result dict so `_compute_technical_with_subscores()` can detect them via `any(key in technical_data for key in ("rsi", "macd_histogram", "adx", "obv_change_pct"))`
- Regime detection kept as informational context (try/except) in CLI, not part of the scoring flow -- regime is displayed in the table but does not affect the composite score calculation
- Used `result_wrapper.error` attribute instead of `unwrap_err()` since the Err dataclass exposes `.error` directly

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Err.error attribute access**
- **Found during:** Task 2 (Full regression)
- **Issue:** CLI used `result_wrapper.unwrap_err()` but `Err` dataclass only has `.error` attribute
- **Fix:** Changed to `result_wrapper.error`
- **Files modified:** cli/main.py
- **Verification:** All tests pass
- **Committed in:** 1c9e29d

**2. [Rule 1 - Bug] Updated test_cli_commands.py TestScoreCommand mocks**
- **Found during:** Task 2 (Full regression)
- **Issue:** Test mocked old imports (core.scoring.composite.score_symbol, core.orchestrator) but CLI now uses DDD handler path
- **Fix:** Rewrote test to mock `_get_ctx()` returning a handler that returns `Ok({...})`
- **Files modified:** tests/unit/test_cli_commands.py
- **Verification:** 669/669 tests pass
- **Committed in:** 1c9e29d

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness after CLI rewiring. No scope creep.

## Issues Encountered
- Pre-existing `test_api_routes.py` fails due to missing `fastapi` dependency (out of scope, documented in 07-VERIFICATION.md)
- Pre-existing mypy errors in `core/scoring/technical.py` and `core/data/client.py` (out of scope)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 7 fully complete: domain layer, handler wiring, and CLI surface all verified
- All 4 TECH requirements satisfied at CLI surface (not just domain layer)
- Ready for Phase 8 (Regime Detection) or any phase that depends on scoring engine

---
*Phase: 07-technical-scoring-engine*
*Completed: 2026-03-12*

## Self-Check: PASSED
- All 6 files verified present
- All 3 commits verified in git log
