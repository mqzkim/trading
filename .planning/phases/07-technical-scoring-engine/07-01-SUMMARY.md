---
phase: 07-technical-scoring-engine
plan: 01
subsystem: scoring
tags: [technical-indicators, rsi, macd, adx, obv, moving-average, ddd, domain-service, value-object]

# Dependency graph
requires:
  - phase: 05-tech-debt-infrastructure
    provides: DDD scoring bounded context (TechnicalScore VO, CompositeScoringService, CoreScoringAdapter)
provides:
  - TechnicalIndicatorScore VO with name, value 0-100, explanation, raw_value
  - TechnicalScore extended with 5 sub-scores (rsi, macd, ma, adx, obv)
  - TechnicalScoringService domain service producing composite from 5 indicators
  - TechnicalIndicatorAdapter bridging core/data/indicators to domain service
  - STRATEGY_WEIGHTS swing updated to 40/40/20 (TECH-03)
  - TECHNICAL_INDICATOR_WEIGHTS (rsi=0.20, macd=0.20, ma=0.25, adx=0.15, obv=0.20)
affects: [07-02, phase-08, phase-09, phase-11]

# Tech tracking
tech-stack:
  added: []
  patterns: [indicator-scoring-with-explanation, infrastructure-adapter-float-extraction, inverted-rsi-scoring]

key-files:
  created:
    - tests/unit/test_technical_scoring_service.py
  modified:
    - src/scoring/domain/value_objects.py
    - src/scoring/domain/services.py
    - src/scoring/domain/__init__.py
    - src/scoring/infrastructure/core_scoring_adapter.py
    - src/scoring/infrastructure/__init__.py
    - tests/unit/test_scoring_composite_v2.py
    - tests/unit/test_score_handler_events.py

key-decisions:
  - "RSI inverted scoring: low RSI (oversold) = high score (buying opportunity)"
  - "MA scoring: baseline 50 with +/-40 from MA200, +/-20 from MA50, +10/-10 golden/death cross"
  - "OBV scored by percentage change (not absolute value) to normalize across stock sizes"
  - "MACD histogram normalized to -5/+5 range for score mapping"
  - "ADX 0-50 mapped to 0-100 (values above 50 extremely rare)"

patterns-established:
  - "Indicator scoring pattern: _is_missing() guard -> assert type -> _norm() -> explanation -> TechnicalIndicatorScore"
  - "Infrastructure float extraction: _safe_last() from Series, _safe_float() NaN-to-None conversion"

requirements-completed: [TECH-01, TECH-02, TECH-03]

# Metrics
duration: 8min
completed: 2026-03-12
---

# Phase 7 Plan 01: Technical Scoring Engine Domain Layer Summary

**TechnicalScoringService produces 5 individual 0-100 indicator scores (RSI/MACD/MA/ADX/OBV) with plain-text explanations, composite technical score via weighted sum, and infrastructure adapter extracting floats from pandas indicators**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-12T07:58:57Z
- **Completed:** 2026-03-12T08:07:21Z
- **Tasks:** 2 (Task 1 TDD, Task 2 auto)
- **Files modified:** 8

## Accomplishments
- TechnicalIndicatorScore VO with validation (0-100), explanation string, optional raw_value
- TechnicalScore VO extended with 5 optional sub-scores, backward compatible (value-only still works)
- TechnicalScoringService with 5 private scoring methods, NaN/None handling, weighted composite
- TechnicalIndicatorAdapter bridges core/data/indicators.compute_all() to domain service
- STRATEGY_WEIGHTS swing updated from 35/40/25 to 40/40/20 per TECH-03
- 37 new tests + 7 updated existing tests, full suite 658 pass

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests** - `a70b5f5` (test)
2. **Task 1 GREEN: TechnicalScoringService + TechnicalIndicatorScore VO** - `d2d294a` (feat)
3. **Task 2: Infrastructure adapter + composite weight tests** - `b4c2c2f` (feat)

## Files Created/Modified
- `tests/unit/test_technical_scoring_service.py` - 33 tests covering VO, service, indicators, weights
- `src/scoring/domain/value_objects.py` - TechnicalIndicatorScore VO, TechnicalScore extended, STRATEGY_WEIGHTS 40/40/20
- `src/scoring/domain/services.py` - TechnicalScoringService, TECHNICAL_INDICATOR_WEIGHTS, _norm(), _is_missing()
- `src/scoring/domain/__init__.py` - Export new types and service
- `src/scoring/infrastructure/core_scoring_adapter.py` - TechnicalIndicatorAdapter, _safe_last(), _safe_float()
- `src/scoring/infrastructure/__init__.py` - Export TechnicalIndicatorAdapter
- `tests/unit/test_scoring_composite_v2.py` - 4 new TECH-03 weight verification tests
- `tests/unit/test_score_handler_events.py` - Updated assertion for new 40/40/20 weights

## Decisions Made
- RSI uses inverted scoring: low RSI (oversold) maps to high score (buying opportunity for swing traders)
- MA scoring uses a 50-point baseline with contributions from MA200 (+/-40), MA50 (+/-20), and golden/death cross (+/-10)
- OBV scored by percentage change over 60-day lookback (not absolute value) to normalize across different stock capitalizations
- MACD histogram normalized to -5/+5 range for 0-100 mapping
- ADX normalized 0-50 to 0-100 (values above 50 are extremely rare in practice)
- assert isinstance() used after _is_missing() guard for mypy type narrowing

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated handler test assertion for new weights**
- **Found during:** Task 2 (full test suite regression check)
- **Issue:** test_score_handler_events.py asserted composite=68.0 using old swing weights (35/40/25)
- **Fix:** Updated assertion to 69.0 matching new 40/40/20 weights, updated comments
- **Files modified:** tests/unit/test_score_handler_events.py
- **Verification:** Full test suite passes (658/658)
- **Committed in:** b4c2c2f (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug from weight change)
**Impact on plan:** Expected consequence of TECH-03 weight update. No scope creep.

## Issues Encountered
- mypy could not narrow types after custom _is_missing() function. Fixed with assert isinstance() after early return guards. This is a known mypy limitation with custom type guard functions.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- TechnicalScoringService ready to wire into ScoreSymbolHandler (Plan 07-02)
- TechnicalIndicatorAdapter ready to replace _estimate_technical_score in handler
- CLI score command can display sub-score breakdown once handler produces it (Plan 07-02)

---
*Phase: 07-technical-scoring-engine*
*Completed: 2026-03-12*
