---
phase: 09-multi-strategy-signal-fusion
plan: 02
subsystem: signals
tags: [cli-signal-rewiring, ddd-handler, rich-output, regime-weighted-display, core-signal-adapter]

# Dependency graph
requires:
  - phase: 09-multi-strategy-signal-fusion
    plan: 01
    provides: SignalFusionService with regime_type, GenerateSignalCommand.regime_type, methodology_directions dict, strategy_weights in handler result
  - phase: 08-market-regime-detection
    provides: DetectRegimeHandler with sentinel-zero auto-fetch pattern
  - phase: 07-technical-scoring-engine
    provides: ScoreSymbolHandler with composite_score and safety_passed
provides:
  - CLI signal command routed through DDD GenerateSignalHandler (no legacy imports)
  - CoreSignalAdapter wired into signal_handler in bootstrap.py
  - Rich Panel+Table output showing regime, per-strategy signals/scores/weights, reasoning chain
  - _build_signal_symbol_data helper for evaluator data extraction
affects: [phase-11 (commercial API), CLI testing patterns]

# Tech tracking
tech-stack:
  added: []
  patterns: [CLI DDD handler routing for signal command, Rich Panel+Table signal display with regime context]

key-files:
  created:
    - tests/unit/test_signal_reasoning.py
  modified:
    - src/bootstrap.py
    - cli/main.py
    - tests/unit/test_cli_commands.py

key-decisions:
  - "symbol_data built via _build_signal_symbol_data helper using core DataClient (data fetch stays in CLI layer, not handler)"
  - "Per-strategy directions read from structured methodology_directions dict, not parsed from reasoning trace text"
  - "DetectRegimeCommand called with sentinel zeros (same pattern as CLI regime command) for auto-fetch"
  - "CLI signal test updated to mock DDD handlers instead of legacy core modules"

patterns-established:
  - "CLI signal routing: regime_handler -> score_handler -> signal_handler chain through DDD commands"
  - "Rich signal output: Panel (direction + consensus + regime subtitle) + Table (strategy/signal/score/weight) + Reasoning Panel"

requirements-completed: [SIGNAL-05, SIGNAL-07]

# Metrics
duration: 5min
completed: 2026-03-12
---

# Phase 9 Plan 02: CLI Signal DDD Rewiring Summary

**CLI signal command rewired through DDD GenerateSignalHandler with Rich Panel+Table showing regime-weighted strategy breakdown and full reasoning chain**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-12T12:13:54Z
- **Completed:** 2026-03-12T12:19:37Z
- **Tasks:** 1 (TDD: test + implementation)
- **Files modified:** 4

## Accomplishments
- CLI signal command routes through DDD GenerateSignalHandler instead of legacy core/signals/consensus
- bootstrap.py wires CoreSignalAdapter into signal_handler enabling the adapter evaluation path
- Rich output shows regime name with confidence, per-strategy signals/scores/weights in table, consensus count, weighted strength, composite score, and full reasoning chain in Panel
- No legacy imports from core.signals or core.regime.classifier remain in the signal function

## Task Commits

Each task was committed atomically:

1. **Task 1 (TDD RED): Reasoning trace tests** - `803d476` (test: add reasoning trace tests)
2. **Task 1 (TDD GREEN): Implementation** - `1672b1b` (feat: rewire CLI signal through DDD handler)

## Files Created/Modified
- `tests/unit/test_signal_reasoning.py` - 5 tests for reasoning trace regime context (regime line, weight percentages, per-methodology annotations, backward compat)
- `src/bootstrap.py` - CoreSignalAdapter wired into GenerateSignalHandler
- `cli/main.py` - Signal command rewired through DDD handlers; added _build_signal_symbol_data and _render_signal_output helpers
- `tests/unit/test_cli_commands.py` - TestSignalCommand updated from legacy mock to DDD handler mocks; removed unused imports

## Decisions Made
- symbol_data built via _build_signal_symbol_data helper using core DataClient (data fetch stays in CLI layer, not handler)
- Per-strategy directions read from structured methodology_directions dict (from Plan 01), not parsed from reasoning trace text
- DetectRegimeCommand called with sentinel zeros (0.0 for all fields) to trigger auto-fetch in handler, same pattern as CLI regime command
- CLI signal test updated to mock DDD handlers (regime_handler, score_handler, signal_handler) instead of legacy core modules

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated CLI signal test to match new DDD output**
- **Found during:** Task 1 (full suite run after implementation)
- **Issue:** test_cli_commands.py::TestSignalCommand::test_signal_command tested legacy CLI format with core.signals.consensus mocks, which now fails since signal routes through DDD handler
- **Fix:** Rewrote test to mock DDD handlers (regime_handler, score_handler, signal_handler) and assert new output format (BUY, CAN SLIM, Signal Consensus)
- **Files modified:** tests/unit/test_cli_commands.py
- **Verification:** All 716 tests pass (excluding pre-existing fastapi import error in test_api_routes.py)
- **Committed in:** 1672b1b (part of implementation commit)

**2. [Rule 1 - Bug] Fixed unused imports in test files**
- **Found during:** Task 1 (ruff lint check)
- **Issue:** Unused `json`, `pytest`, `DEFAULT_SIGNAL_WEIGHTS` imports flagged by ruff
- **Fix:** Removed unused imports from test_signal_reasoning.py and test_cli_commands.py
- **Files modified:** tests/unit/test_signal_reasoning.py, tests/unit/test_cli_commands.py
- **Verification:** ruff check passes cleanly
- **Committed in:** 1672b1b (part of implementation commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep.

## Issues Encountered
- DetectRegimeCommand requires positional arguments (vix, sp500_price, sp500_ma200, adx, yield_spread) -- resolved by using sentinel zeros pattern consistent with CLI regime command
- mypy has pre-existing module resolution issue with project structure (duplicate module names) -- not caused by this plan's changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Signal generation pipeline is fully DDD-wired end-to-end (CLI -> bootstrap -> handler -> adapter -> core evaluators)
- Commercial API (Phase 11) can reuse the same DDD handler chain with different presentation layer
- All 716 tests pass (excluding pre-existing test_api_routes.py FastAPI import issue)

## Self-Check: PASSED

All 4 files verified present. All 2 commits verified in git log.

---
*Phase: 09-multi-strategy-signal-fusion*
*Completed: 2026-03-12*
