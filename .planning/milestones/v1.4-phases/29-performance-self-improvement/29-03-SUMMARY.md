---
phase: "29"
plan: "03"
subsystem: dashboard-backend-integration
tags: [fastapi, dashboard, bff, sse, alpaca, approval, pipeline]
dependency_graph:
  requires: [bootstrap, pipeline-handlers, approval-handlers, alpaca-adapter]
  provides: [portfolio-api, pipeline-control-api, approval-api, review-api, sse-events]
  affects: [commercial-api, dashboard-bff]
tech_stack:
  added: []
  patterns: [proxy-bff, sse-bridge, dashboard-secret-auth]
key_files:
  created:
    - commercial/api/routers/portfolio.py
    - commercial/api/routers/pipeline_ctrl.py
    - commercial/api/routers/approval_ctrl.py
    - commercial/api/routers/review_ctrl.py
    - commercial/api/routers/events.py
    - dashboard/src/app/api/v1/dashboard/_proxy.ts
    - dashboard/src/app/api/v1/dashboard/review/route.ts
    - dashboard/src/app/api/v1/dashboard/review/[id]/approve/route.ts
    - dashboard/src/app/api/v1/dashboard/review/[id]/reject/route.ts
  modified:
    - commercial/api/main.py
    - commercial/api/dependencies.py
    - commercial/api/config.py
    - dashboard/src/app/api/v1/dashboard/overview/route.ts
    - dashboard/src/app/api/v1/dashboard/risk/route.ts
    - dashboard/src/app/api/v1/dashboard/pipeline/route.ts
    - dashboard/src/app/api/v1/dashboard/pipeline/run/route.ts
    - dashboard/src/app/api/v1/dashboard/approval/create/route.ts
    - dashboard/src/app/api/v1/dashboard/approval/suspend/route.ts
    - dashboard/src/app/api/v1/dashboard/approval/resume/route.ts
    - dashboard/src/app/api/v1/dashboard/events/route.ts
decisions:
  - DASHBOARD_SECRET bearer token for internal BFF-to-FastAPI auth (no JWT needed)
  - Proxy pattern with shared _proxy.ts helper for all BFF routes
  - Pipeline run executes in background thread, returns immediately
  - SSE bridge subscribes to domain event bus and relays events
metrics:
  duration: 4min
  completed: "2026-03-18T03:39:30Z"
---

# Phase 29 Plan 03: Dashboard Backend Integration Summary

Full-stack wiring of dashboard BFF to real trading backend via 5 new FastAPI routers and shared proxy helper.

## What Was Built

### FastAPI Routers (5 new files)

1. **portfolio.py** -- GET /portfolio/overview (Alpaca positions + scores), GET /portfolio/risk (drawdown + regime)
2. **pipeline_ctrl.py** -- POST /pipeline/run (background execution), GET /pipeline/status, POST /pipeline/daemon/start
3. **approval_ctrl.py** -- POST /approval/create, GET /approval/status, POST /approval/revoke, POST /approval/resume
4. **review_ctrl.py** -- GET /review/queue, POST /review/{id}/approve, POST /review/{id}/reject
5. **events.py** -- GET /events SSE stream bridging domain bus events with 15s keep-alive

### Dashboard BFF Updates

- Created `_proxy.ts` shared helper with `proxyGet`/`proxyPost` functions
- Replaced all 8 stub BFF routes with real backend proxies
- Created 3 new review queue BFF routes (list, approve, reject)
- Fixed SSE events route URL path from `/v1/events` to `/api/v1/events`

### Auth Pattern

- Added `DASHBOARD_SECRET` to ApiSettings (default: "dashboard-internal")
- `verify_dashboard_secret` FastAPI dependency checks Bearer token
- BFF proxy helper sends DASHBOARD_SECRET as Authorization header

## Deviations from Plan

None -- plan executed exactly as written.

## Verification

- ruff check: PASS (0 errors)
- mypy: PASS (0 new errors; 2 pre-existing errors in unrelated files)
- TypeScript: PASS (tsc --noEmit, 0 errors)

## Commits

| Hash | Message |
|------|---------|
| 4dd82b6 | feat(dashboard): wire real trading backend -- pipeline, approval, portfolio, review, SSE |

## Self-Check: PASSED

- All 9 created files exist on disk
- All 11 modified files verified
- Commit 4dd82b6 verified in git log
