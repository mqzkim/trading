---
phase: 24-real-time-and-integration
plan: 01
subsystem: ui
tags: [sse, eventsource, tanstack-query, react, real-time]

# Dependency graph
requires:
  - phase: 23-signals-risk-pipeline
    provides: TanStack Query hooks (useOverview, useRisk, useSignals, usePipeline) with query keys
provides:
  - useSSE hook mapping 5 backend SSE event types to TanStack Query invalidations
  - SSEListener component in Providers for app-wide EventSource connection
affects: [25-cleanup]

# Tech tracking
tech-stack:
  added: []
  patterns: [EventSource-to-query-invalidation, provider-level SSE mounting]

key-files:
  created: [dashboard/src/hooks/use-sse.ts]
  modified: [dashboard/src/app/providers.tsx]

key-decisions:
  - "No new npm dependencies -- browser-native EventSource API"
  - "SSEListener placed inside QueryClientProvider (before ThemeProvider) for useQueryClient access"

patterns-established:
  - "EventSource event-to-query mapping: declarative EVENT_QUERY_MAP constant for easy extension"
  - "Provider-level hook mounting: internal SSEListener component renders null, calls hook for side effects"

requirements-completed: [RT-01]

# Metrics
duration: 1min
completed: 2026-03-14
---

# Phase 24 Plan 01: Real-Time SSE Integration Summary

**useSSE hook wiring 5 backend SSE event types (OrderFilled, DrawdownAlert, RegimeChanged, PipelineCompleted, PipelineHalted) to TanStack Query cache invalidation via browser-native EventSource API**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-14T12:05:42Z
- **Completed:** 2026-03-14T12:06:51Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created useSSE hook with declarative EVENT_QUERY_MAP mapping 5 SSE event types to query key invalidations
- Mounted SSEListener in Providers for a single persistent EventSource connection across all dashboard pages
- Zero new dependencies -- uses browser-native EventSource API with auto-reconnect per SSE spec

## Task Commits

Each task was committed atomically:

1. **Task 1: Create useSSE hook** - `6509711` (feat)
2. **Task 2: Mount SSEListener in Providers** - `1bb8a15` (feat)

## Files Created/Modified
- `dashboard/src/hooks/use-sse.ts` - useSSE hook: EventSource connection, 5 event type listeners, query invalidation mapping
- `dashboard/src/app/providers.tsx` - Added SSEListener component inside QueryClientProvider for app-wide SSE

## Decisions Made
- No new npm dependencies -- browser-native EventSource API provides auto-reconnect, named event listeners, and cleanup via close()
- SSEListener placed inside QueryClientProvider but before ThemeProvider -- needs useQueryClient() access from QueryClientProvider ancestor

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None -- no external service configuration required.

## Next Phase Readiness
- Real-time SSE integration complete, all 5 event types wired to query invalidations
- Phase 25 can proceed to remove HTMX/Jinja2 legacy dashboard code
- No blockers

## Self-Check: PASSED

- [x] dashboard/src/hooks/use-sse.ts -- FOUND
- [x] dashboard/src/app/providers.tsx -- FOUND
- [x] Commit 6509711 -- FOUND
- [x] Commit 1bb8a15 -- FOUND

---
*Phase: 24-real-time-and-integration*
*Completed: 2026-03-14*
