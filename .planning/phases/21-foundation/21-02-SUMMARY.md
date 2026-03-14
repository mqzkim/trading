---
phase: 21-foundation
plan: 02
subsystem: ui
tags: [nextjs, react, biome, tailwind, bff-proxy, typescript]

# Dependency graph
requires:
  - phase: 20
    provides: FastAPI dashboard backend with query handlers
provides:
  - Next.js 16 project scaffold in dashboard/
  - Biome 2.4.7 linter/formatter replacing ESLint
  - API proxy rewrites from /api/* to FastAPI at 127.0.0.1:8000
  - 4 page stubs (Overview, Signals, Risk, Pipeline) with fetch and error handling
  - Dashboard route group layout with navigation
affects: [22-design-system, 23-signals-risk-pipeline, 24-realtime]

# Tech tracking
tech-stack:
  added: [next@16.1.6, react@19.2.3, react-dom@19.2.3, "@biomejs/biome@2.4.7", tailwindcss@4, "@tailwindcss/postcss@4"]
  patterns: [App Router route groups, BFF proxy via next.config.ts rewrites, client components with useEffect fetch]

key-files:
  created:
    - dashboard/package.json
    - dashboard/biome.json
    - dashboard/next.config.ts
    - dashboard/tsconfig.json
    - dashboard/src/app/layout.tsx
    - dashboard/src/app/(dashboard)/layout.tsx
    - dashboard/src/app/(dashboard)/page.tsx
    - dashboard/src/app/(dashboard)/signals/page.tsx
    - dashboard/src/app/(dashboard)/risk/page.tsx
    - dashboard/src/app/(dashboard)/pipeline/page.tsx
  modified: []

key-decisions:
  - "Biome 2.x config uses assist.actions.source.organizeImports instead of top-level organizeImports"
  - "files.includes whitelist instead of files.ignore to exclude auto-generated next-env.d.ts"
  - "Moved app/ into src/app/ for standard project structure matching plan expectations"

patterns-established:
  - "Route group pattern: (dashboard)/ directory does not add /dashboard to URL"
  - "Client component fetch pattern: useEffect + fetch + error/loading/data states"
  - "Error display pattern: red text with 'Backend connection failed - Start FastAPI first' message"
  - "Biome as single tool for lint + format (no ESLint, no Prettier)"

requirements-completed: [SETUP-01, SETUP-02]

# Metrics
duration: 5min
completed: 2026-03-14
---

# Phase 21 Plan 02: Next.js Dashboard Setup Summary

**Next.js 16 project with Biome linting, BFF proxy rewrites to FastAPI, and 4 page stubs fetching from /api/v1/dashboard/* endpoints**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-14T09:53:13Z
- **Completed:** 2026-03-14T09:58:58Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Next.js 16 project initialized in dashboard/ with TypeScript, Tailwind CSS v4, and App Router
- ESLint replaced with Biome 2.4.7 for linting and formatting (single-quote, semicolons, 100 line width)
- API proxy configured: /api/* requests routed to FastAPI at http://127.0.0.1:8000
- 4 page stubs created with fetch, loading states, and backend-offline error messages
- Route group (dashboard) layout with navigation between Overview, Signals, Risk, Pipeline

## Task Commits

Each task was committed atomically:

1. **Task 1: Initialize Next.js project and configure Biome** - `0150e54` (feat)
2. **Task 2: Configure API proxy and create page stubs** - `67fc6c0` (feat)

## Files Created/Modified
- `dashboard/package.json` - Next.js project config with Biome scripts (lint, format)
- `dashboard/biome.json` - Biome 2.4.7 config (single-quote, semicolons, 100 line width, import organization)
- `dashboard/tsconfig.json` - TypeScript config with src/ path alias
- `dashboard/next.config.ts` - API proxy rewrites to FastAPI
- `dashboard/src/app/layout.tsx` - Root layout with Inter font
- `dashboard/src/app/globals.css` - Minimal Tailwind v4 import
- `dashboard/src/app/(dashboard)/layout.tsx` - Dashboard nav layout with dark theme
- `dashboard/src/app/(dashboard)/page.tsx` - Overview page stub (fetches /api/v1/dashboard/overview)
- `dashboard/src/app/(dashboard)/signals/page.tsx` - Signals page stub
- `dashboard/src/app/(dashboard)/risk/page.tsx` - Risk page stub
- `dashboard/src/app/(dashboard)/pipeline/page.tsx` - Pipeline page stub

## Decisions Made
- **Biome 2.x config migration:** `organizeImports` moved to `assist.actions.source.organizeImports` and `files.ignore` replaced with `files.includes` whitelist in Biome 2.x. Plan's config was from Biome 1.x documentation.
- **files.includes whitelist approach:** Using includes whitelist instead of ignore to prevent auto-generated `next-env.d.ts` from being checked by Biome.
- **src/ directory structure:** Moved generated `app/` into `src/app/` and updated tsconfig paths to match plan expectations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Biome 2.x config schema differences**
- **Found during:** Task 1 (Biome configuration)
- **Issue:** Plan's biome.json used Biome 1.x keys (`organizeImports`, `files.ignore`) that are invalid in Biome 2.4.7
- **Fix:** Used `assist.actions.source.organizeImports` and `files.includes` whitelist
- **Files modified:** dashboard/biome.json
- **Verification:** `npm run lint` passes, `npx biome format src/` shows no fixes needed
- **Committed in:** 67fc6c0 (Task 2 commit, along with biome.json refinement)

**2. [Rule 3 - Blocking] create-next-app generated app/ without src/ directory**
- **Found during:** Task 1 (Project initialization)
- **Issue:** `npx create-next-app@latest dashboard --yes` created `app/` at root instead of `src/app/`
- **Fix:** Moved `app/` into `src/app/` and updated tsconfig.json paths from `"./*"` to `"./src/*"`
- **Files modified:** dashboard/tsconfig.json, moved dashboard/app/ to dashboard/src/app/
- **Verification:** `npm run build` succeeds, all routes resolve correctly
- **Committed in:** 0150e54 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes were necessary to match plan's expected structure and tooling version. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Next.js project ready for Phase 22 (Design System & Overview Page)
- Biome tooling configured and passing
- API proxy configured and ready to forward requests to FastAPI
- Route structure established for all 4 dashboard pages
- Phase 22 can add shadcn/ui, TanStack Query, zustand, next-themes, and TradingView charts

## Self-Check: PASSED

- All 11 created files verified present
- Commit 0150e54 (Task 1) verified in git log
- Commit 67fc6c0 (Task 2) verified in git log

---
*Phase: 21-foundation*
*Completed: 2026-03-14*
