---
phase: 28-commercial-api-dashboard
plan: 01
subsystem: api
tags: [fastapi, pydantic, scoring, regime, sub-scores, sentiment]

requires:
  - phase: 27-scoring-expansion
    provides: 3-axis scoring with sentiment sub-scores and SentimentConfidence VO
provides:
  - SubScoreEntry Pydantic model for typed sub-score lists
  - QuantScore API with technical_sub_scores, sentiment_sub_scores, sentiment_confidence
  - RegimeRadar API with regime_probabilities distribution
  - Handler result dict includes sentiment_sub_scores and sentiment_confidence
affects: [28-02, 28-03, dashboard]

tech-stack:
  added: []
  patterns: [_compute_regime_probabilities helper for probability distribution from confidence]

key-files:
  created: []
  modified:
    - commercial/api/schemas/score.py
    - commercial/api/schemas/regime.py
    - commercial/api/routers/quantscore.py
    - commercial/api/routers/regime.py
    - src/scoring/application/handlers.py
    - tests/unit/test_api_v1_quantscore.py
    - tests/unit/test_api_v1_regime.py
    - tests/unit/test_api_v1_signals.py

key-decisions:
  - "regime_probabilities computed from confidence: dominant regime gets confidence value, remaining 1-confidence split equally across other 3 regimes"
  - "SubScoreEntry has name/value/raw_value (no explanation) to keep API response clean; legacy sub_scores dict preserved for backward compat"

patterns-established:
  - "Typed sub-score list pattern: SubScoreEntry model instead of raw dicts in API responses"
  - "Regime probability distribution: _compute_regime_probabilities(regime_type, confidence) -> dict[str, float]"

requirements-completed: [API-01, API-02, API-03, API-04, API-05, API-06, API-07]

duration: 4min
completed: 2026-03-17
---

# Phase 28 Plan 01: Commercial API Extended Schemas Summary

**Extended 3 commercial API endpoints with typed sub-score breakdowns, sentiment confidence, and regime probability distributions**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-17T19:19:27Z
- **Completed:** 2026-03-17T19:23:00Z
- **Tasks:** 1 (TDD: RED + GREEN + REFACTOR)
- **Files modified:** 8

## Accomplishments
- QuantScore API returns typed technical_sub_scores and sentiment_sub_scores lists with SubScoreEntry model
- QuantScore API includes sentiment_confidence field (NONE/LOW/MEDIUM/HIGH, never omitted)
- RegimeRadar API returns regime_probabilities dict with Bull/Bear/Sideways/Crisis summing to ~1.0
- SignalFusion methodology_votes verified as reasoning trace (name/direction/score per methodology)
- Scoring handler result dict extended with sentiment_sub_scores and sentiment_confidence from SentimentScore VO
- All 34 tests pass (6 new + 28 existing)

## Task Commits

Each task was committed atomically (TDD cycle):

1. **Task 1 RED: Failing tests** - `f2e4cc5` (test)
2. **Task 1 GREEN: Implementation** - `eaae4ac` (feat)
3. **Task 1 REFACTOR: Lint fix** - `5311af4` (refactor)

## Files Created/Modified
- `commercial/api/schemas/score.py` - Added SubScoreEntry model, technical_sub_scores, sentiment_sub_scores, sentiment_confidence fields
- `commercial/api/schemas/regime.py` - Added regime_probabilities field to RegimeCurrentResponse
- `commercial/api/routers/quantscore.py` - Map typed sub-score lists and sentiment_confidence from handler result
- `commercial/api/routers/regime.py` - Added _compute_regime_probabilities helper, wired into both success and fallback paths
- `src/scoring/application/handlers.py` - Extended result dict with sentiment_sub_scores and sentiment_confidence
- `tests/unit/test_api_v1_quantscore.py` - Added TestQuantScoreSubScores class (4 tests)
- `tests/unit/test_api_v1_regime.py` - Added TestRegimeProbabilities class (3 tests)
- `tests/unit/test_api_v1_signals.py` - Added TestSignalReasoningTrace class (1 test)

## Decisions Made
- regime_probabilities computed from confidence: dominant regime gets confidence value, remaining (1-confidence) split equally across other 3 regimes
- SubScoreEntry model has name/value/raw_value only (no explanation field) to keep API clean; explanation stays in legacy sub_scores dict for backward compat

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused Limiter import**
- **Found during:** Task 1 REFACTOR
- **Issue:** ruff flagged unused `from slowapi import Limiter` after rewriting quantscore.py
- **Fix:** Removed the unused import
- **Files modified:** commercial/api/routers/quantscore.py
- **Verification:** ruff check passes
- **Committed in:** 5311af4

---

**Total deviations:** 1 auto-fixed (1 lint fix)
**Impact on plan:** Minor cleanup, no scope change.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 3 commercial API endpoints now serve full scoring data for dashboard consumption
- Ready for 28-02 (dashboard implementation) and 28-03 (integration)

---
*Phase: 28-commercial-api-dashboard*
*Completed: 2026-03-17*
