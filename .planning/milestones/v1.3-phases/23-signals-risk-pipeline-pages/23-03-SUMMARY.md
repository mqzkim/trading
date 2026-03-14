---
phase: 23-signals-risk-pipeline-pages
plan: 03
subsystem: ui
tags: [react, tanstack-query, shadcn, pipeline, approval, review-queue, dashboard]

requires:
  - phase: 23-signals-risk-pipeline-pages
    provides: TypeScript types (PipelineData, ApprovalStatus, ReviewItem), TanStack Query hooks (usePipeline, mutations), shadcn form components
provides:
  - PipelineRunForm component with symbol input and dry run checkbox
  - PipelineHistory table with status badges and next scheduled display
  - ApprovalControls with create form (5 fields) and status/suspend/resume view
  - ReviewQueue with approve/reject icon buttons
  - Fully assembled Pipeline page with loading/error/data states
affects: [24-final-integration]

tech-stack:
  added: []
  patterns: [mutation-form-with-isPending-disabled, conditional-form-vs-status-display, dual-useReviewAction-hooks]

key-files:
  created:
    - dashboard/src/components/pipeline/pipeline-run-form.tsx
    - dashboard/src/components/pipeline/pipeline-history.tsx
    - dashboard/src/components/pipeline/approval-controls.tsx
    - dashboard/src/components/pipeline/review-queue.tsx
  modified:
    - dashboard/src/app/(dashboard)/pipeline/page.tsx
    - dashboard/src/hooks/use-pipeline.ts

key-decisions:
  - "Approval create form uses expires_in_days (integer) matching backend contract, not expires_at (string)"
  - "ApprovalControls conditionally renders create form vs status view based on approval null check"
  - "ReviewQueue uses two separate useReviewAction hooks (approve/reject) for independent isPending states"

patterns-established:
  - "Conditional form/status pattern: null check determines create form vs display + action buttons"
  - "Dual mutation hooks: separate hook instances for approve/reject to track isPending independently"
  - "Pipeline page 2-column top grid: Run form + Approval side by side, History + Review full-width below"

requirements-completed: [PIPE-01, PIPE-02, PIPE-03, PIPE-04]

duration: 3min
completed: 2026-03-14
---

# Phase 23 Plan 03: Pipeline Page Summary

**Pipeline page with run form, history table, approval create/suspend/resume controls, and trade review queue with approve/reject actions**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-14T11:42:21Z
- **Completed:** 2026-03-14T11:45:13Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Built 4 pipeline components: run form with symbol parsing and dry run toggle, history table with status badges, approval controls with conditional create/status views, and review queue with approve/reject buttons
- Assembled Pipeline page with 2-column layout (run form + approval) and full-width sections (history + review queue)
- Fixed useApprovalCreate hook to use expires_in_days (integer) matching backend POST contract instead of expires_at (string)

## Task Commits

Each task was committed atomically:

1. **Task 1: Build pipeline run form, history table, and approval controls** - `b2a3290` (feat)
2. **Task 2: Build review queue and assemble Pipeline page** - `220d9b3` (feat)

## Files Created/Modified
- `dashboard/src/components/pipeline/pipeline-run-form.tsx` - Form with symbol input, dry run checkbox, mutation submit with isPending disabled
- `dashboard/src/components/pipeline/pipeline-history.tsx` - Table with run ID (truncated), started/completed dates, status badges, next scheduled
- `dashboard/src/components/pipeline/approval-controls.tsx` - Create form (5 fields with defaults) or status display with suspend/resume buttons
- `dashboard/src/components/pipeline/review-queue.tsx` - Table with symbol, strategy, score, reason, date, approve/reject icon buttons
- `dashboard/src/app/(dashboard)/pipeline/page.tsx` - Full Pipeline page replacing stub, with loading skeleton and error state
- `dashboard/src/hooks/use-pipeline.ts` - Fixed useApprovalCreate mutation body type (expires_in_days)

## Decisions Made
- Approval create form uses `expires_in_days` (integer) to match backend POST contract, not `expires_at` (string) -- fixed the hook accordingly
- ApprovalControls conditionally renders create form (when approval is null) vs status display with suspend/resume (when approval exists)
- ReviewQueue uses two separate `useReviewAction` hook instances (one for 'approve', one for 'reject') so isPending states are tracked independently

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed useApprovalCreate mutation body type to match backend contract**
- **Found during:** Task 1 (Approval controls)
- **Issue:** useApprovalCreate hook accepted `expires_at: string` but backend POST /approval/create expects `expires_in_days: number`
- **Fix:** Changed hook mutation body type from `expires_at: string` to `expires_in_days: number`
- **Files modified:** dashboard/src/hooks/use-pipeline.ts
- **Verification:** `npx tsc --noEmit` passes, form submits correct shape
- **Committed in:** b2a3290 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed biome formatting (import ordering, line wrapping)**
- **Found during:** Tasks 1 and 2
- **Issue:** Biome flagged import ordering and JSX line wrapping in new components
- **Fix:** Auto-fixed via `biome check --write` on pipeline component files
- **Files modified:** pipeline-run-form.tsx, pipeline-history.tsx, approval-controls.tsx, review-queue.tsx
- **Verification:** `npx biome check .` passes with 0 errors on pipeline files
- **Committed in:** b2a3290 (Task 1), 220d9b3 (Task 2)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Hook type fix essential for correctness. Formatting fixes are standard biome compliance. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 3 dashboard pages complete (Signals, Risk, Pipeline)
- Pipeline page fully functional with forms, tables, and mutation-driven controls
- Ready for Phase 24 (final integration/testing)

## Self-Check: PASSED

All 6 created/modified files verified present. Both task commits (b2a3290, 220d9b3) verified in git log.

---
*Phase: 23-signals-risk-pipeline-pages*
*Completed: 2026-03-14*
