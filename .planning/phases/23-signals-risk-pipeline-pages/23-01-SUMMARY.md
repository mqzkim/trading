---
phase: 23-signals-risk-pipeline-pages
plan: 01
subsystem: ui
tags: [react, tanstack-table, tanstack-query, shadcn, signals, dashboard]

requires:
  - phase: 22-design-system-overview-page
    provides: shadcn component library, page layout pattern, formatters, existing types
provides:
  - TypeScript types for SignalsData, RiskData, PipelineData matching FastAPI response shapes
  - TanStack Query hooks for signals, risk, pipeline with mutation support
  - Generic DataTable component with TanStack Table sorting
  - 5 shadcn form components (progress, input, label, checkbox, select)
  - Signals page with sortable scoring table and signal recommendation cards
affects: [23-02-risk-page, 23-03-pipeline-page]

tech-stack:
  added: ["@tanstack/react-table"]
  patterns: [generic-data-table-with-sorting, column-definitions-outside-component, signal-badge-variant-mapping]

key-files:
  created:
    - dashboard/src/types/api.ts (extended with ScoreRow, SignalItem, SignalsData, RiskData, PipelineData types)
    - dashboard/src/hooks/use-signals.ts
    - dashboard/src/hooks/use-risk.ts
    - dashboard/src/hooks/use-pipeline.ts
    - dashboard/src/components/ui/data-table.tsx
    - dashboard/src/components/ui/progress.tsx
    - dashboard/src/components/ui/input.tsx
    - dashboard/src/components/ui/label.tsx
    - dashboard/src/components/ui/checkbox.tsx
    - dashboard/src/components/ui/select.tsx
    - dashboard/src/components/signals/columns.tsx
    - dashboard/src/components/signals/signal-cards.tsx
  modified:
    - dashboard/src/app/(dashboard)/signals/page.tsx
    - dashboard/package.json

key-decisions:
  - "Column definitions declared outside component to avoid recreation on each render"
  - "Strength indicator uses aria-hidden decorative bar with visible percentage text for accessibility"
  - "Badge variant mapping: BUY=default (primary), SELL=destructive, HOLD/--=secondary"

patterns-established:
  - "DataTable generic component: reusable with any ColumnDef array and typed data"
  - "Sortable column pattern: ghost Button with ArrowUpDown icon, toggleSorting on click"
  - "Signal direction variant mapping: shared between columns.tsx and signal-cards.tsx"

requirements-completed: [SGNL-01, SGNL-02, SGNL-03]

duration: 3min
completed: 2026-03-14
---

# Phase 23 Plan 01: Signals Page Summary

**Sortable scoring table and signal recommendation cards with shared types, hooks, and DataTable component for all 3 dashboard pages**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-14T11:34:51Z
- **Completed:** 2026-03-14T11:38:00Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments
- Established shared data layer (TypeScript types + TanStack Query hooks) for all 3 pages (Signals, Risk, Pipeline)
- Built generic DataTable component with TanStack Table sorting, reusable across all pages
- Delivered Signals page with sortable composite/risk-adjusted scoring table and signal recommendation cards with BUY/SELL/HOLD badges and strength indicators

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies, add shadcn components, create shared types and hooks** - `c61f00c` (feat)
2. **Task 2: Build DataTable component and Signals page with sortable scoring table and signal cards** - `34232ec` (feat)

## Files Created/Modified
- `dashboard/src/types/api.ts` - Extended with ScoreRow, SignalItem, SignalsData, RiskData, PipelineData and related types
- `dashboard/src/hooks/use-signals.ts` - TanStack Query hook for GET /api/v1/dashboard/signals
- `dashboard/src/hooks/use-risk.ts` - TanStack Query hook for GET /api/v1/dashboard/risk
- `dashboard/src/hooks/use-pipeline.ts` - TanStack Query hook + mutations for pipeline/approval/review actions
- `dashboard/src/components/ui/data-table.tsx` - Generic DataTable with TanStack Table sorting support
- `dashboard/src/components/ui/progress.tsx` - shadcn Progress component
- `dashboard/src/components/ui/input.tsx` - shadcn Input component
- `dashboard/src/components/ui/label.tsx` - shadcn Label component
- `dashboard/src/components/ui/checkbox.tsx` - shadcn Checkbox component
- `dashboard/src/components/ui/select.tsx` - shadcn Select component
- `dashboard/src/components/signals/columns.tsx` - Sortable column definitions for scoring table
- `dashboard/src/components/signals/signal-cards.tsx` - Signal recommendation cards with badges and strength bars
- `dashboard/src/app/(dashboard)/signals/page.tsx` - Full Signals page replacing stub

## Decisions Made
- Column definitions declared outside component to avoid recreation on each render (performance pattern from TanStack Table docs)
- Strength indicator bar uses `aria-hidden="true"` with visible percentage text instead of ARIA meter role for cleaner accessibility
- Badge variant mapping shared between scoring table columns and signal cards: BUY=default (primary color), SELL=destructive, HOLD/--=secondary

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed biome import ordering and ARIA accessibility lint errors**
- **Found during:** Task 2 (DataTable and Signals page)
- **Issue:** Biome flagged unsorted imports and aria-label on plain div without role
- **Fix:** Auto-fixed import ordering via `biome check --write`, replaced aria-label with aria-hidden decorative approach
- **Files modified:** dashboard/src/components/ui/data-table.tsx, dashboard/src/app/(dashboard)/signals/page.tsx, dashboard/src/components/signals/signal-cards.tsx
- **Verification:** `npx biome check .` passes with 0 errors
- **Committed in:** 34232ec (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor lint compliance fix. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Shared types (RiskData, PipelineData) and hooks (useRisk, usePipeline) ready for Plans 02 and 03
- DataTable component ready for reuse in Risk page
- Pipeline mutations (usePipelineRun, useApprovalCreate/Suspend/Resume, useReviewAction) ready for Pipeline page
- All shadcn form components (progress, input, label, checkbox, select) available for Pipeline page forms

## Self-Check: PASSED

All 13 created/modified files verified present. Both task commits (c61f00c, 34232ec) verified in git log.

---
*Phase: 23-signals-risk-pipeline-pages*
*Completed: 2026-03-14*
