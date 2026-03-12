# Deferred Items - Phase 03

## Pre-existing Test Failures

### test_portfolio_sizing.py::TestHandlerOpenPositionFlow::test_full_flow_with_take_profit
- **Found during:** 03-01 execution
- **Issue:** `OpenPositionCommand.__init__() got an unexpected keyword argument 'intrinsic_value'` -- test references a field not yet added to the command dataclass
- **Scope:** Out of scope for 03-01 (pre-existing, unrelated to signals context)
- **Likely fix:** Add `intrinsic_value` field to `OpenPositionCommand` in `src/portfolio/application/commands.py` -- expected to be addressed in 03-02 or 03-03 plan (portfolio/risk management)
