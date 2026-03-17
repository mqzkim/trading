---
phase: 28-commercial-api-dashboard
plan: 03
subsystem: ui
tags: [dashboard, react, nextjs, tanstack-table, expandable-rows, regime-bars, performance-page]

requires:
  - phase: 28-02
    provides: Dashboard backend returning sub-scores, sentiment_confidence, regime_probabilities
provides:
  - Expandable signal table rows with F/T/S score breakdown panel
  - Regime probability horizontal bars with dominant highlight
  - Performance Attribution page shell (empty state)
  - 5-link dashboard navigation
affects: [29-performance-self-improvement]

tech-stack:
  added: []
  patterns: [renderSubComponent pattern for DataTable row expansion, graceful 404 fallback in usePerformance hook]

key-files:
  created:
    - dashboard/src/components/signals/score-breakdown-panel.tsx
    - dashboard/src/components/risk/regime-probabilities.tsx
    - dashboard/src/hooks/use-performance.ts
    - dashboard/src/app/(dashboard)/performance/page.tsx
  modified:
    - dashboard/src/types/api.ts
    - dashboard/src/components/ui/data-table.tsx
    - dashboard/src/app/(dashboard)/signals/page.tsx
    - dashboard/src/app/(dashboard)/risk/page.tsx
    - dashboard/src/app/(dashboard)/layout.tsx

key-decisions:
  - "DataTable renderSubComponent pattern: generic expansion support via optional prop rather than signals-specific logic"
  - "usePerformance returns fallback data on 404 since endpoint does not exist until Phase 29"
  - "RegimeProbabilities uses existing shadcn Progress component (base-ui backed) for horizontal bars"

patterns-established:
  - "DataTable row expansion: pass renderSubComponent prop to enable clickable expandable rows"
  - "Graceful endpoint fallback: hooks return default data on non-ok response for pages awaiting backend"

requirements-completed: [DASH-01, DASH-02, DASH-03, DASH-04]

duration: 3min
completed: 2026-03-17
---

# Phase 28 Plan 03: Dashboard Frontend Components Summary

**Expandable signal rows with F/T/S score breakdown, regime probability bars, and Performance Attribution page shell with KPI/Brinson/equity/scorecard sections**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-17T19:25:39Z
- **Completed:** 2026-03-17T19:28:58Z
- **Tasks:** 2 auto + 1 checkpoint (auto-approved)
- **Files modified:** 9

## Accomplishments
- Signals page table rows expand on click to show ScoreBreakdownPanel with F/T/S axis scores and sub-score bar placeholders
- Sentiment unavailable state grayed out with "Sentiment data unavailable" label when confidence is NONE
- Risk page shows horizontal regime probability bars with dominant regime highlighted via ring border
- Performance Attribution page at /performance with KPI cards (Sharpe/Sortino/Win Rate/Max Drawdown), Brinson-Fachler table area, equity curve area, and strategy scorecard (Signal IC/Kelly Efficiency) -- all empty state
- Dashboard navigation updated to 5 links: Overview, Signals, Risk, Pipeline, Performance

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend types + score breakdown panel + expandable DataTable + Signals page** - `938c03f` (feat)
2. **Task 2: RegimeProbabilities + Risk page + Performance page shell + navigation** - `624228b` (feat)
3. **Task 3: Visual verification** - auto-approved (no commit, checkpoint only)

## Files Created/Modified
- `dashboard/src/types/api.ts` - Extended ScoreRow with sub-scores, RiskData with regime_probabilities, added PerformanceData/PerformanceKPI
- `dashboard/src/components/signals/score-breakdown-panel.tsx` - F/T/S axis scores + sub-score bar placeholders with sentiment unavailable state
- `dashboard/src/components/ui/data-table.tsx` - Added getExpandedRowModel and renderSubComponent for generic row expansion
- `dashboard/src/app/(dashboard)/signals/page.tsx` - Wired ScoreBreakdownPanel into expandable rows
- `dashboard/src/components/risk/regime-probabilities.tsx` - Horizontal Progress bars with dominant regime highlight
- `dashboard/src/app/(dashboard)/risk/page.tsx` - Added RegimeProbabilities below RegimeBadge
- `dashboard/src/hooks/use-performance.ts` - Query hook with graceful 404 fallback
- `dashboard/src/app/(dashboard)/performance/page.tsx` - Full page shell with KPI cards, Brinson table, equity curve, strategy scorecard
- `dashboard/src/app/(dashboard)/layout.tsx` - Added Performance as 5th navigation link

## Decisions Made
- DataTable renderSubComponent pattern: generic expansion support via optional prop rather than signals-specific logic
- usePerformance returns fallback data on 404 since endpoint does not exist until Phase 29
- RegimeProbabilities uses existing shadcn Progress component (base-ui backed) for horizontal bars

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dashboard frontend complete for Phase 28 scope
- Performance page ready to be populated when Phase 29 creates the /api/v1/dashboard/performance endpoint
- Sub-score bars (RSI, MACD, News, etc.) show placeholders -- ready to consume per-indicator detail when backend adds it

---
*Phase: 28-commercial-api-dashboard*
*Completed: 2026-03-17*
