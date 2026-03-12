---
phase: 10-korean-broker-integration
plan: 01
subsystem: execution
tags: [ddd, abc, broker-adapter, order-spec, dependency-inversion]

# Dependency graph
requires:
  - phase: 04-execution-interface
    provides: "AlpacaExecutionAdapter, BracketSpec, TradePlanHandler"
provides:
  - "IBrokerAdapter ABC in execution/domain/repositories.py"
  - "OrderSpec VO with Optional stop_loss/take_profit"
  - "BracketSpec backward-compatible alias"
  - "TradePlanHandler decoupled from AlpacaExecutionAdapter"
affects: [10-02-korean-broker-integration, execution, bootstrap]

# Tech tracking
tech-stack:
  added: []
  patterns: [IBrokerAdapter dependency inversion, Optional bracket legs for non-US markets]

key-files:
  created:
    - tests/execution/__init__.py
    - tests/execution/test_broker_interface.py
    - tests/execution/test_order_spec.py
  modified:
    - src/execution/domain/repositories.py
    - src/execution/domain/value_objects.py
    - src/execution/domain/__init__.py
    - src/execution/application/handlers.py
    - src/execution/infrastructure/alpaca_adapter.py
    - tests/unit/test_trade_approval.py

key-decisions:
  - "OrderSpec.stop_loss_price and take_profit_price are Optional[float]=None for Korean market support"
  - "Alpaca real bracket path guards against None with explicit ValueError"
  - "BracketSpec = OrderSpec alias preserves all existing code"

patterns-established:
  - "IBrokerAdapter ABC: all broker adapters implement submit_order/get_positions/get_account"
  - "Optional bracket legs: non-US markets can omit stop_loss/take_profit at order spec level"

requirements-completed: [KR-01, KR-03]

# Metrics
duration: 4min
completed: 2026-03-12
---

# Phase 10 Plan 01: Broker Interface Abstraction Summary

**IBrokerAdapter ABC and OrderSpec VO with optional stop/target, decoupling TradePlanHandler from Alpaca**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-12T19:27:44Z
- **Completed:** 2026-03-12T19:31:42Z
- **Tasks:** 2 (TDD task 1 + auto task 2)
- **Files modified:** 9

## Accomplishments
- IBrokerAdapter ABC defined in execution/domain/repositories.py with submit_order, get_positions, get_account
- OrderSpec VO replaces BracketSpec with Optional stop_loss_price/take_profit_price for Korean market compatibility
- TradePlanHandler now depends on IBrokerAdapter interface (not AlpacaExecutionAdapter concrete class)
- AlpacaExecutionAdapter implements IBrokerAdapter with submit_order delegating to submit_bracket_order
- Full backward compatibility via BracketSpec = OrderSpec alias

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: IBrokerAdapter + OrderSpec tests** - `2475404` (test)
2. **Task 1 GREEN: IBrokerAdapter ABC + OrderSpec VO** - `c1c1dda` (feat)
3. **Task 2: Rewire TradePlanHandler to IBrokerAdapter** - `b85b16e` (feat)

_TDD task had RED + GREEN commits_

## Files Created/Modified
- `src/execution/domain/repositories.py` - Added IBrokerAdapter ABC (submit_order, get_positions, get_account)
- `src/execution/domain/value_objects.py` - Renamed BracketSpec to OrderSpec, Optional stop/target, BracketSpec alias
- `src/execution/domain/__init__.py` - Exports IBrokerAdapter, OrderSpec
- `src/execution/application/handlers.py` - IBrokerAdapter type hint, submit_order() call
- `src/execution/infrastructure/alpaca_adapter.py` - Inherits IBrokerAdapter, added submit_order delegate, None guard
- `tests/execution/test_broker_interface.py` - IBrokerAdapter ABC instantiation tests
- `tests/execution/test_order_spec.py` - OrderSpec Optional fields + BracketSpec alias tests
- `tests/unit/test_trade_approval.py` - Updated mock from submit_bracket_order to submit_order

## Decisions Made
- OrderSpec.stop_loss_price and take_profit_price are Optional[float]=None (Korean market has no bracket orders)
- Alpaca _real_bracket_order raises ValueError if stop_loss/take_profit is None (explicit fail-fast over silent mypy error)
- BracketSpec = OrderSpec simple alias (not subclass) -- simplest backward compat approach
- submit_order delegates to submit_bracket_order in AlpacaAdapter (preserves existing real Alpaca path untouched)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Alpaca real bracket path mypy type error with Optional fields**
- **Found during:** Task 2 (Rewire TradePlanHandler)
- **Issue:** mypy reported incompatible type float|None for Alpaca StopLossRequest/TakeProfitRequest
- **Fix:** Added explicit None guard with ValueError before Alpaca SDK call
- **Files modified:** src/execution/infrastructure/alpaca_adapter.py
- **Verification:** mypy passes with 0 errors
- **Committed in:** b85b16e (Task 2 commit)

**2. [Rule 1 - Bug] Existing test used submit_bracket_order mock**
- **Found during:** Task 2 (Rewire TradePlanHandler)
- **Issue:** test_trade_approval.py mocked submit_bracket_order but handler now calls submit_order
- **Fix:** Updated mock setup to use adapter.submit_order.return_value
- **Files modified:** tests/unit/test_trade_approval.py
- **Verification:** All 47 execution tests pass
- **Committed in:** b85b16e (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bug fixes)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- IBrokerAdapter interface ready for KisExecutionAdapter implementation in Plan 02
- OrderSpec supports Korean market orders (no bracket legs required)
- bootstrap.py still creates AlpacaExecutionAdapter -- Plan 02 will add market-conditional adapter creation

## Self-Check: PASSED

All 10 files verified present. All 3 commits verified in git log. All 5 content checks (IBrokerAdapter class, OrderSpec class, BracketSpec alias, IBrokerAdapter type hint, Alpaca inheritance) confirmed.

---
*Phase: 10-korean-broker-integration*
*Completed: 2026-03-12*
