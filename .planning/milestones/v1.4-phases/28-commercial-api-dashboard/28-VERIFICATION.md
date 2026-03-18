---
phase: 28-commercial-api-dashboard
verified: 2026-03-18T00:00:00Z
status: human_needed
score: 12/12 must-haves verified
human_verification:
  - test: "Open http://localhost:3000/signals, click a table row, confirm ScoreBreakdownPanel expands below the row showing F/T/S axis scores"
    expected: "Row expands inline with Fundamental/Technical/Sentiment scores. Sentiment shows 'Sentiment data unavailable' when confidence is NONE."
    why_human: "Row expansion is React runtime behavior — getExpandedRowModel and onClick are wired in code but visual toggle cannot be confirmed without a browser."
  - test: "Open http://localhost:3000/risk, confirm the Market Regime card shows horizontal probability bars for Bull/Bear/Sideways/Crisis when regime data exists"
    expected: "Four horizontal Progress bars. Dominant regime row has ring border and bold text."
    why_human: "RegimeProbabilities component renders conditionally on live data; empty state vs. populated state requires backend data."
  - test: "Open http://localhost:3000/performance, confirm the page renders KPI cards, Brinson-Fachler section, Equity Curve section, and Strategy Scorecard — all showing empty state"
    expected: "Four KPI cards (Sharpe/Sortino/Win Rate/Max Drawdown) showing '--', Brinson-Fachler and Equity Curve sections showing 'No performance data yet', Signal IC and Kelly Efficiency showing '--'"
    why_human: "Page shell is present in code; visual layout correctness requires browser render."
  - test: "Confirm dashboard navigation shows exactly 5 links: Overview, Signals, Risk, Pipeline, Performance"
    expected: "All 5 links visible and clickable in the navigation bar"
    why_human: "Navigation structure verified in code but visual rendering and link click behavior requires browser."
---

# Phase 28: Commercial API Dashboard Verification Report

**Phase Goal:** Three commercial API products serve real 3-axis scoring data behind authentication and rate limiting, and the dashboard displays all new scoring and regime data
**Verified:** 2026-03-18
**Status:** human_needed — all automated checks passed; 4 visual checks require browser
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET /api/v1/quantscore/{ticker} returns technical_sub_scores and sentiment_sub_scores lists with SubScoreEntry | VERIFIED | `SubScoreEntry` class at line 11 of score.py; router builds typed lists at lines 48-60 of quantscore.py |
| 2 | GET /api/v1/quantscore/{ticker} returns sentiment_confidence field (never omitted) | VERIFIED | `sentiment_confidence: Optional[str] = None` in schema; handler sets it at line 198 of handlers.py |
| 3 | GET /api/v1/regime/current returns regime_probabilities dict with 4 regimes | VERIFIED | `regime_probabilities` field in regime.py schema; `_compute_regime_probabilities` helper in regime.py router at line 26, called at lines 66 and 82 |
| 4 | GET /api/v1/signals/{ticker} returns methodology_votes as reasoning trace | VERIFIED | `methodology_votes: Optional[list[MethodologyVote]]` already in SignalResponse; test_api_v1_signals.py TestSignalReasoningTrace verified; 34/34 tests pass |
| 5 | All API responses include disclaimer field | VERIFIED | `disclaimer: str = DISCLAIMER` present in score.py line 33, regime.py lines 23 and 41 |
| 6 | Requests without JWT are rejected with 401/403 | VERIFIED | `Depends(get_current_user)` on quantscore router at line 25; auth dependency unchanged from Phase 27 |
| 7 | Dashboard signals endpoint returns F/T/S sub-scores per symbol | VERIFIED | `find_all_latest_with_details` wired in queries.py line 410; fundamental_score, technical_score, sentiment_score at lines 422+ |
| 8 | Dashboard risk endpoint returns regime_probabilities dict | VERIFIED | `_compute_regime_probabilities` in queries.py line 31; wired into RiskQueryHandler return dict at lines 544-545 |
| 9 | Signals table rows expand to show F/T/S breakdown panel | VERIFIED (code) | `getExpandedRowModel` in data-table.tsx line 7; `renderSubComponent` prop wired; `ScoreBreakdownPanel` imported and passed in signals page.tsx line 42; HUMAN VERIFY needed |
| 10 | Sentiment unavailable state shown when confidence is NONE | VERIFIED (code) | `Sentiment data unavailable` label at score-breakdown-panel.tsx line 63; conditional on `sentiment_confidence === 'NONE'` |
| 11 | Risk page shows regime probability bars with dominant highlighted | VERIFIED (code) | `RegimeProbabilities` imported and rendered in risk/page.tsx lines 6 and 77-82; `ring-1 ring-primary font-bold` for dominant at regime-probabilities.tsx line 30; HUMAN VERIFY needed |
| 12 | Performance page at /performance with required sections | VERIFIED (code) | File exists; contains "No performance data yet", "Brinson-Fachler Attribution", "Signal IC", "Kelly Efficiency"; HUMAN VERIFY needed |
| 13 | Dashboard navigation has 5 links | VERIFIED | layout.tsx: Overview(/), Signals, Risk, Pipeline, Performance — all 5 present |

**Score:** 12/12 truths verified (4 with human verification pending for visual rendering)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `commercial/api/schemas/score.py` | SubScoreEntry, technical/sentiment sub-scores, sentiment_confidence | VERIFIED | `class SubScoreEntry` at line 11; all 3 new fields present |
| `commercial/api/schemas/regime.py` | regime_probabilities field | VERIFIED | `regime_probabilities: Optional[dict[str, float]] = None` at line 22 |
| `src/scoring/application/handlers.py` | sentiment_sub_scores and sentiment_confidence in result dict | VERIFIED | Both added at lines 198-205 |
| `commercial/api/routers/quantscore.py` | Maps typed sub-score lists from handler result | VERIFIED | SubScoreEntry imported; sentiment_sub_scores_typed built at lines 56-60; wired into response at lines 71-74 |
| `commercial/api/routers/regime.py` | _compute_regime_probabilities helper | VERIFIED | Defined at line 26; called in both success and fallback paths |
| `src/scoring/domain/repositories.py` | find_all_latest_with_details abstract method | VERIFIED | Abstract method at line 23 |
| `src/scoring/infrastructure/sqlite_repo.py` | find_all_latest_with_details implementation | VERIFIED | Concrete implementation at line 119 |
| `src/dashboard/application/queries.py` | Extended SignalsQueryHandler + RiskQueryHandler | VERIFIED | find_all_latest_with_details called at line 410; regime_probabilities/confidence at lines 529-545 |
| `dashboard/src/types/api.ts` | Extended ScoreRow, RiskData with regime_probabilities, PerformanceData | VERIFIED | fundamental_score at line 64; regime_probabilities at line 92; PerformanceData interface at line 104 |
| `dashboard/src/components/signals/score-breakdown-panel.tsx` | ScoreBreakdownPanel with NONE state | VERIFIED | Exported at line 26; "Sentiment data unavailable" at line 63 |
| `dashboard/src/components/ui/data-table.tsx` | getExpandedRowModel, renderSubComponent prop | VERIFIED | Both present; row expansion logic fully wired |
| `dashboard/src/components/risk/regime-probabilities.tsx` | RegimeProbabilities with dominant highlight | VERIFIED | Exported at line 18; ring-1 ring-primary at line 30 |
| `dashboard/src/app/(dashboard)/performance/page.tsx` | Performance page shell | VERIFIED | All 4 required sections present |
| `dashboard/src/app/(dashboard)/layout.tsx` | 5-link navigation | VERIFIED | Overview/Signals/Risk/Pipeline/Performance all present |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `commercial/api/routers/quantscore.py` | `src/scoring/application/handlers.py` | handler result dict `sentiment_sub_scores` | WIRED | Router reads `data.get("sentiment_sub_scores")` and maps to typed SubScoreEntry list |
| `commercial/api/routers/regime.py` | `commercial/api/schemas/regime.py` | `RegimeCurrentResponse.regime_probabilities` | WIRED | `_compute_regime_probabilities` called and result passed to RegimeCurrentResponse in both paths |
| `src/dashboard/application/queries.py` | `src/scoring/infrastructure/sqlite_repo.py` | `score_repo.find_all_latest_with_details()` | WIRED | Called at line 410 of queries.py; implementation in sqlite_repo.py returns sub-score columns |
| `src/dashboard/application/queries.py` | regime domain | `regime_repo.find_latest().confidence` | WIRED | regime_obj.confidence used at line 532; regime_probabilities computed and returned |
| `dashboard/src/app/(dashboard)/signals/page.tsx` | `score-breakdown-panel.tsx` | ScoreBreakdownPanel rendered in renderSubComponent | WIRED | Import at line 4; renderSubComponent prop at line 42 |
| `dashboard/src/app/(dashboard)/risk/page.tsx` | `regime-probabilities.tsx` | RegimeProbabilities with data.regime_probabilities | WIRED | Import at line 6; rendered at lines 77-82 with data.regime_probabilities |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| API-01 | 28-01 | QuantScore endpoint returns composite score with sub-component breakdown | SATISFIED | SubScoreEntry, technical_sub_scores, sentiment_sub_scores in schema and router |
| API-02 | 28-01 | RegimeRadar endpoint returns current regime with probability and indicators | SATISFIED | regime_probabilities field; _compute_regime_probabilities helper wired |
| API-03 | 28-01 | SignalFusion endpoint returns consensus signal with reasoning trace | SATISFIED | methodology_votes verified in TestSignalReasoningTrace; 34 tests pass |
| API-04 | 28-01 | JWT authentication with API key management | SATISFIED | `Depends(get_current_user)` on all commercial endpoints; unchanged from Phase 27 foundation |
| API-05 | 28-01 | Rate limiting per tier (free/basic/pro) | SATISFIED | Rate limiting from Phase 27 foundation preserved; 34 tests pass including rate limit tests |
| API-06 | 28-01 | Legal disclaimer auto-included in all responses | SATISFIED | `disclaimer: str = DISCLAIMER` in score.py, regime.py; DISCLAIMER imported from common.py |
| API-07 | 28-01 | OpenAPI/Swagger documentation auto-generated | SATISFIED | FastAPI auto-generates OpenAPI from Pydantic schemas; new fields automatically documented |
| DASH-01 | 28-02, 28-03 | Technical and sentiment sub-scores visible on Signals page | SATISFIED (code) | Backend returns sub-scores; ScoreBreakdownPanel renders them in expandable rows |
| DASH-02 | 28-03 | Performance attribution page added to dashboard | SATISFIED (code) | /performance page exists with KPI/Brinson/equity/scorecard sections |
| DASH-03 | 28-02, 28-03 | Real data displayed across all pages (no empty states when data exists) | SATISFIED | Backend now returns fundamental/technical/sentiment scores; frontend renders them when non-null |
| DASH-04 | 28-02, 28-03 | Regime detection enhanced view with HMM probabilities | SATISFIED (code) | regime_probabilities returned by backend; RegimeProbabilities component renders horizontal bars |

All 11 requirements covered. No orphaned requirements found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `dashboard/src/components/signals/score-breakdown-panel.tsx` | 53-58 | Technical sub-score bars (RSI/MACD/MA/ADX/OBV) hardcoded as `value={null}` placeholders | Info | By design — backend does not expose per-indicator sub-scores yet; F/T/S axis scores ARE real data; documented in plan and summary |
| `dashboard/src/components/signals/score-breakdown-panel.tsx` | 68-71 | Sentiment sub-score bars (News/Insider/Institutional/Analyst) hardcoded as `value={null}` placeholders | Info | Same rationale — axis score real, per-indicator placeholders intentional for Phase 29+ |

No blockers. The two info-level items are intentional per the plan: "The panel structure is ready to consume them when the backend adds per-indicator detail."

### Human Verification Required

#### 1. Signals Page Expandable Rows

**Test:** Start the dashboard backend (`python3 -m src.dashboard.presentation.run`) and frontend (`cd dashboard && npm run dev`), open http://localhost:3000/signals, click any row.
**Expected:** Row expands inline below the clicked row, showing F/T/S axis scores in a grid. If sentiment_confidence is NONE, the Sentiment section is grayed out with "Sentiment data unavailable" italic label.
**Why human:** Row expansion depends on React state (`row.toggleExpanded()`) which is runtime behavior. Code wiring is complete but visual toggle cannot be confirmed programmatically.

#### 2. Risk Page Regime Probability Bars

**Test:** Open http://localhost:3000/risk after scoring has run at least once (regime data exists in SQLite).
**Expected:** Market Regime card shows RegimeBadge plus four horizontal Progress bars labeled Bull/Bear/Sideways/Crisis. The dominant regime bar has a ring border and bold text. Percentages display correctly (e.g., Bull 82%).
**Why human:** RegimeProbabilities renders conditionally on `data.regime_probabilities` being non-empty. With no regime data in DB, the component shows fallback text — visual verification of the populated state requires live data.

#### 3. Performance Page Empty State

**Test:** Open http://localhost:3000/performance.
**Expected:** Page renders with title "Performance Attribution", four KPI cards (Sharpe/Sortino/Win Rate/Max Drawdown showing "--"), Brinson-Fachler Attribution card with "No performance data yet" message, Equity Curve card with same message, Strategy Scorecard with Signal IC and Kelly Efficiency showing "--".
**Why human:** Performance page uses usePerformance hook that fetches /api/v1/dashboard/performance (404 until Phase 29). Visual confirmation of the fallback render and layout is required.

#### 4. Navigation 5-Link Bar

**Test:** Observe the navigation bar at the top of any dashboard page.
**Expected:** Five visible links in order: Overview, Signals, Risk, Pipeline, Performance. All links navigate to their respective pages.
**Why human:** Link rendering and layout correctness requires visual confirmation.

### Gaps Summary

No gaps. All automated checks passed:
- 34/34 commercial API unit tests pass
- 17/17 dashboard backend unit tests pass
- biome lint reports no errors on all 9 modified dashboard files
- All key artifacts exist, are substantive, and are wired
- All 11 requirements (API-01 through API-07, DASH-01 through DASH-04) are covered by implemented code
- 2 intentional placeholder patterns noted as Info-only (by design, documented in plan)

The status is `human_needed` because 4 visual/runtime behaviors require browser verification. All code paths are present and correct.

---

_Verified: 2026-03-18_
_Verifier: Claude (gsd-verifier)_
