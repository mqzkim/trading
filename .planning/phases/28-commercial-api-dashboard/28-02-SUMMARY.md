---
phase: 28-commercial-api-dashboard
plan: 02
subsystem: api
tags: [dashboard, scoring, regime, sub-scores, fastapi, sqlite]

requires:
  - phase: 27-scoring-expansion
    provides: "Technical/sentiment scoring VOs, composite score storage with sub-score columns"
provides:
  - "find_all_latest_with_details score repo method returning sub-score breakdown"
  - "SignalsQueryHandler with fundamental_score, technical_score, sentiment_score, sentiment_confidence"
  - "RiskQueryHandler with regime_probabilities dict and regime_confidence float"
affects: [28-03-dashboard-frontend, dashboard-ui]

tech-stack:
  added: []
  patterns: ["_compute_regime_probabilities helper for 4-regime distribution from dominant regime + confidence"]

key-files:
  created: []
  modified:
    - src/scoring/domain/repositories.py
    - src/scoring/infrastructure/sqlite_repo.py
    - src/scoring/infrastructure/in_memory_repo.py
    - src/dashboard/application/queries.py
    - tests/unit/test_dashboard_json_api.py

key-decisions:
  - "Regime probabilities computed from dominant regime + confidence split across 4 regimes (Bull/Bear/Sideways/Crisis)"
  - "sentiment_confidence defaults to NONE when not stored in score repo"

patterns-established:
  - "find_all_latest_with_details returns list[dict] for rich score data (not VO-only)"

requirements-completed: [DASH-01, DASH-03, DASH-04]

duration: 3min
completed: 2026-03-17
---

# Phase 28 Plan 02: Dashboard Sub-Scores and Regime Probabilities Summary

**Extended dashboard signals endpoint with F/T/S sub-score breakdown and risk endpoint with 4-regime probability distribution**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-17T19:19:24Z
- **Completed:** 2026-03-17T19:22:28Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Score repository gained find_all_latest_with_details method reading fundamental/technical/sentiment scores from SQLite
- SignalsQueryHandler now returns per-symbol sub-score breakdown for expandable row rendering
- RiskQueryHandler now returns regime_probabilities (4-regime distribution) and regime_confidence for HMM probability bars
- All 17 dashboard tests pass (3 new tests added)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add find_all_latest_with_details and extend SignalsQueryHandler**
   - `183f770` (test: failing test for sub-score fields)
   - `5838bd2` (feat: implementation with sub-score fields in signals)

2. **Task 2: Extend RiskQueryHandler with regime probability distribution**
   - `fb2cacd` (test: failing tests for regime probabilities)
   - `e0991be` (feat: regime probabilities and confidence in risk endpoint)

_TDD tasks have RED/GREEN commit pairs._

## Files Created/Modified
- `src/scoring/domain/repositories.py` - Added find_all_latest_with_details abstract method to IScoreRepository
- `src/scoring/infrastructure/sqlite_repo.py` - Implemented find_all_latest_with_details reading sub-score columns
- `src/scoring/infrastructure/in_memory_repo.py` - Added stub implementation for InMemoryScoreRepository
- `src/dashboard/application/queries.py` - Extended SignalsQueryHandler and RiskQueryHandler, added _compute_regime_probabilities helper
- `tests/unit/test_dashboard_json_api.py` - Added 3 new tests for sub-scores and regime probabilities

## Decisions Made
- Regime probabilities computed by assigning dominant regime's confidence as its probability, splitting remaining (1-confidence) equally across other 3 regimes
- sentiment_confidence defaults to "NONE" string when not stored, matching existing SentimentConfidence enum convention

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dashboard backend now provides all data needed for frontend expandable signal rows and regime probability bars
- Ready for 28-03 dashboard frontend implementation

## Self-Check: PASSED

All 5 files verified present. All 4 commit hashes verified in git log.

---
*Phase: 28-commercial-api-dashboard*
*Completed: 2026-03-17*
