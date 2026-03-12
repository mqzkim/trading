---
phase: 03-decision-engine
plan: 02
subsystem: risk-management
tags: [kelly, atr, take-profit, drawdown, sector-limits, position-sizing]

# Dependency graph
requires:
  - phase: 02-analysis-core
    provides: "Ensemble valuation with intrinsic value estimates"
provides:
  - "TakeProfitLevels VO computing 3 exit levels from intrinsic value gap"
  - "CoreRiskAdapter wrapping personal/sizer/kelly and personal/risk/drawdown"
  - "Portfolio.sector_weight() for 25% sector limit enforcement"
  - "PortfolioManagerHandler with take-profit and sector integration"
affects: [03-decision-engine, 04-execution-interface]

# Tech tracking
tech-stack:
  added: []
  patterns: [infrastructure-adapter-delegation, vo-computed-properties]

key-files:
  created:
    - src/portfolio/infrastructure/core_risk_adapter.py
    - tests/unit/test_take_profit.py
    - tests/unit/test_portfolio_risk.py
    - tests/unit/test_portfolio_sizing.py
  modified:
    - src/portfolio/domain/value_objects.py
    - src/portfolio/domain/aggregates.py
    - src/portfolio/domain/__init__.py
    - src/portfolio/application/commands.py
    - src/portfolio/application/handlers.py
    - src/portfolio/infrastructure/__init__.py

key-decisions:
  - "CoreRiskAdapter delegates to personal/ functions without math rewriting -- thin adapter only"
  - "TakeProfitLevels VO uses computed property (levels) to derive 3 exit points from intrinsic value gap"
  - "Portfolio.drawdown uses total_value_or_initial to handle empty portfolios correctly (cash = initial_value)"

patterns-established:
  - "Infrastructure adapter delegation: CoreRiskAdapter wraps personal/ functions for DDD boundary"
  - "VO computed properties: TakeProfitLevels.levels derives data from frozen fields"

requirements-completed: [RISK-01, RISK-02, RISK-03, RISK-04, RISK-05]

# Metrics
duration: 7min
completed: 2026-03-12
---

# Phase 3 Plan 02: Risk Management Summary

**Fractional Kelly sizing, ATR stops, take-profit from intrinsic value, drawdown defense, and 8%/25% hard limits via CoreRiskAdapter delegation**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-12T01:04:48Z
- **Completed:** 2026-03-12T01:12:29Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- TakeProfitLevels VO computes 3 exit levels at 50%/75%/100% of intrinsic value gap
- CoreRiskAdapter delegates to personal/sizer/kelly and personal/risk/drawdown without math rewriting
- Portfolio aggregate enforces 25% sector limit via sector_weight() in can_open_position()
- PortfolioManagerHandler integrates take-profit levels and sector enforcement in open_position flow
- 31 new tests covering RISK-01 through RISK-05

## Task Commits

Each task was committed atomically:

1. **Task 1: TakeProfitLevels VO + sector enforcement + CoreRiskAdapter** - `34bad82` (feat)
2. **Task 2: Enhanced PortfolioManagerHandler with take-profit + sector checks** - `a561556` (feat)

## Files Created/Modified
- `src/portfolio/infrastructure/core_risk_adapter.py` - Adapter wrapping personal/sizer/kelly and personal/risk/drawdown
- `src/portfolio/domain/value_objects.py` - Added TakeProfitLevels VO with computed exit levels
- `src/portfolio/domain/aggregates.py` - Added sector_weight(), total_value_or_initial, sector check in can_open_position()
- `src/portfolio/domain/__init__.py` - Exported TakeProfitLevels
- `src/portfolio/application/commands.py` - Added intrinsic_value field to OpenPositionCommand
- `src/portfolio/application/handlers.py` - Integrated take-profit levels and sector enforcement
- `src/portfolio/infrastructure/__init__.py` - Exported CoreRiskAdapter
- `tests/unit/test_take_profit.py` - 10 tests for TakeProfitLevels VO
- `tests/unit/test_portfolio_risk.py` - 15 tests for sector weight, drawdown defense, CoreRiskAdapter
- `tests/unit/test_portfolio_sizing.py` - 6 tests for handler integration

## Decisions Made
- CoreRiskAdapter delegates to personal/ functions without math rewriting -- thin adapter only
- TakeProfitLevels VO uses computed property (levels) to derive 3 exit points from intrinsic value gap
- Portfolio.drawdown uses total_value_or_initial to handle empty portfolios correctly (cash = initial_value)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed drawdown calculation for empty portfolios**
- **Found during:** Task 2 (handler integration)
- **Issue:** Portfolio.drawdown used raw total_value (0 for empty portfolios) against peak_value (initial_value), causing 100% drawdown on new portfolios
- **Fix:** Changed drawdown property to use total_value_or_initial, treating empty portfolios as holding cash at initial_value
- **Files modified:** src/portfolio/domain/aggregates.py
- **Verification:** All 421 tests pass, new portfolios correctly show 0% drawdown
- **Committed in:** a561556 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Bug fix essential for correct drawdown behavior on new portfolios. No scope creep.

## Issues Encountered
- Test values needed adjustment for Kelly weight calculations -- default win_rate=0.55 with win_loss_ratio=2.0 produces weight 0.08125 which exceeds the 8% single position limit. Tests adjusted to use win_rate=0.50 for conservative sizing.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All risk management infrastructure complete
- CoreRiskAdapter provides bridge to personal/ math modules
- Take-profit, drawdown defense, and sector limits fully integrated in handler
- Ready for Phase 3 Plan 03 (signal generation or execution planning)

## Self-Check: PASSED

- All 11 files verified present
- Commit 34bad82 (Task 1) verified
- Commit a561556 (Task 2) verified
- 421/421 tests pass, 0 failures

---
*Phase: 03-decision-engine*
*Completed: 2026-03-12*
