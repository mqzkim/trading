---
phase: 21-foundation
plan: 01
subsystem: api
tags: [fastapi, rest-api, json, sse, pydantic, dashboard]

# Dependency graph
requires:
  - phase: 16-dashboard-web
    provides: QueryHandlers (Overview, Signals, Risk, Pipeline), SSEBridge, FastAPI app factory
provides:
  - JSON REST API router with 4 GET + 6 POST + 1 SSE endpoints at /api/v1/dashboard/*
  - Pydantic request models for all POST endpoints (JSON bodies)
  - SSE endpoint sending raw JSON payloads (no HTML partials)
affects: [21-02-nextjs-setup, 22-overview-page, 23-signals-risk, 24-pipeline-page]

# Tech tracking
tech-stack:
  added: []
  patterns: [JSON API router alongside HTMX router, Pydantic BaseModel for POST bodies, Plotly key stripping for React frontend]

key-files:
  created:
    - src/dashboard/presentation/api_routes.py
    - tests/unit/test_dashboard_json_api.py
  modified:
    - src/dashboard/presentation/app.py

key-decisions:
  - "Reuse existing QueryHandlers directly -- no DTO layer, return dicts as JSON"
  - "Strip Plotly chart JSON keys (gauge_json, donut_json) from risk/overview responses for React frontend"
  - "POST endpoints use Pydantic BaseModel for JSON body validation (not Form data)"

patterns-established:
  - "API router pattern: APIRouter(prefix='/api/v1/dashboard') mounted on same FastAPI app as HTMX router"
  - "SSE JSON payload pattern: raw JSON payloads with event type field (no HTML partials)"

requirements-completed: [SETUP-03]

# Metrics
duration: 3min
completed: 2026-03-14
---

# Phase 21 Plan 01: JSON API Router Summary

**FastAPI JSON REST API with 11 endpoints (4 GET + 6 POST + 1 SSE) reusing existing QueryHandlers, Pydantic request models, and Plotly key stripping for React frontend consumption**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-14T09:53:18Z
- **Completed:** 2026-03-14T09:56:27Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created JSON REST API router with all 11 endpoints coexisting alongside HTMX routes
- All GET endpoints return QueryHandler dicts as JSON with Plotly chart keys stripped
- All POST endpoints accept JSON bodies via Pydantic BaseModel (not Form data)
- SSE endpoint sends raw JSON payloads for React frontend consumption
- 14 unit tests covering all endpoints with zero regression on 29 existing HTMX tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Create JSON API router and mount on FastAPI app** - `bd9f9bc` (feat)
2. **Task 2: Write unit tests for all JSON API endpoints** - `fa502db` (test)

## Files Created/Modified
- `src/dashboard/presentation/api_routes.py` - JSON API router with 4 GET, 6 POST, 1 SSE endpoint and Pydantic request models
- `src/dashboard/presentation/app.py` - Added api_router import and include_router() call
- `tests/unit/test_dashboard_json_api.py` - 14 unit tests for all JSON API endpoints

## Decisions Made
- Reuse existing QueryHandlers directly, returning their dict output as JSON (no DTO conversion)
- Strip Plotly chart JSON keys (gauge_json, donut_json, equity_curve_chart_json) from responses since React frontend uses its own charting
- POST endpoints accept JSON bodies via Pydantic BaseModel instead of Form data (mirrors HTMX Form routes but for JSON consumers)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing mypy error in `src/pipeline/application/handlers.py:126` (DuckDB union-attr) surfaced during type checking -- out of scope per deviation rules, not caused by our changes

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- JSON API endpoints ready for Plan 02 (Next.js setup) to consume via BFF proxy
- All endpoints tested and returning JSON -- React frontend can fetch from `/api/v1/dashboard/*`
- SSE endpoint at `/api/v1/dashboard/events` ready for proxy via next.config.ts rewrites

---
*Phase: 21-foundation*
*Completed: 2026-03-14*
