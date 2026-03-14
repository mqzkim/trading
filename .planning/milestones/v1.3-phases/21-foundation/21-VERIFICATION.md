---
phase: 21-foundation
verified: 2026-03-14T10:30:00Z
status: passed
score: 20/20 must-haves verified
re_verification: false
---

# Phase 21: Foundation Verification Report

**Phase Goal:** Developer can run the Next.js dashboard alongside FastAPI and all data flows through the BFF proxy
**Verified:** 2026-03-14T10:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | GET /api/v1/dashboard/overview returns JSON with portfolio KPIs, positions, equity curve, regime periods | VERIFIED | api_routes.py:57 calls OverviewQueryHandler; test confirms total_value/positions/equity_curve/regime_periods keys |
| 2  | GET /api/v1/dashboard/signals returns JSON with scores and signals, supporting sort parameters | VERIFIED | api_routes.py:68 calls SignalsQueryHandler with sort/desc params; test confirms scores/signals keys |
| 3  | GET /api/v1/dashboard/risk returns JSON with drawdown, sector weights, position count, regime (no Plotly JSON) | VERIFIED | api_routes.py:78 strips gauge_json/donut_json; test confirms plotly keys absent |
| 4  | GET /api/v1/dashboard/pipeline returns JSON with pipeline runs, approval status, budget, review queue | VERIFIED | api_routes.py:90 calls PipelineQueryHandler; test confirms all 4 keys |
| 5  | POST /api/v1/dashboard/pipeline/run accepts JSON body and triggers pipeline execution | VERIFIED | api_routes.py:101 uses PipelineRunRequest BaseModel; spawns daemon thread |
| 6  | POST /api/v1/dashboard/approval/create accepts JSON body and creates a strategy approval | VERIFIED | api_routes.py:131 uses ApprovalCreateRequest BaseModel; calls approval_handler.create |
| 7  | POST /api/v1/dashboard/approval/suspend accepts JSON body and suspends the active approval | VERIFIED | api_routes.py:154 uses ApprovalActionRequest; calls approval_handler.revoke |
| 8  | POST /api/v1/dashboard/approval/resume accepts JSON body and resumes a suspended approval | VERIFIED | api_routes.py:170 uses ApprovalActionRequest; calls approval_handler.resume |
| 9  | POST /api/v1/dashboard/review/approve accepts JSON body and approves a queued trade | VERIFIED | api_routes.py:186 calls mark_reviewed(id, approved=True); test asserts call args |
| 10 | POST /api/v1/dashboard/review/reject accepts JSON body and rejects a queued trade | VERIFIED | api_routes.py:197 calls mark_reviewed(id, approved=False); test asserts call args |
| 11 | GET /api/v1/dashboard/events streams SSE events with raw JSON payloads (no HTML partials) | VERIFIED | api_routes.py:213 returns EventSourceResponse with json.dumps(payload); route confirmed in runtime check (11 routes) |
| 12 | Running npm run dev in dashboard/ starts the Next.js app at localhost:3000 | VERIFIED | package.json: "dev": "next dev"; build succeeds confirming valid project |
| 13 | Visiting localhost:3000/ renders the Overview page stub | VERIFIED | dashboard/src/app/(dashboard)/page.tsx exists; npm run build reports route / as static |
| 14 | Visiting localhost:3000/signals renders the Signals page stub | VERIFIED | dashboard/src/app/(dashboard)/signals/page.tsx exists; build reports /signals as static |
| 15 | Visiting localhost:3000/risk renders the Risk page stub | VERIFIED | dashboard/src/app/(dashboard)/risk/page.tsx exists; build reports /risk as static |
| 16 | Visiting localhost:3000/pipeline renders the Pipeline page stub | VERIFIED | dashboard/src/app/(dashboard)/pipeline/page.tsx exists; build reports /pipeline as static |
| 17 | Browser requests to /api/* on localhost:3000 are proxied to FastAPI at localhost:8000 | VERIFIED | next.config.ts rewrites: source /api/:path* -> http://127.0.0.1:8000/api/:path* |
| 18 | When FastAPI is not running, pages show a backend connection error message | VERIFIED | All 4 page stubs have .catch(err => setError(err.message)) and render "Backend connection failed - Start FastAPI first" |
| 19 | Biome lint and format commands work (npm run lint, npm run format) | VERIFIED | package.json lint: "biome check ."; format: "biome format --write ."; npm run lint: 0 errors on 12 files |
| 20 | npm run build succeeds with zero TypeScript errors | VERIFIED | build output: 5 static routes generated, 0 errors |

**Score:** 20/20 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/dashboard/presentation/api_routes.py` | JSON REST API router with 4 GET + 6 POST + 1 SSE endpoints, exports api_router | VERIFIED | 230 lines; api_router confirmed to have 11 routes at runtime |
| `tests/unit/test_dashboard_json_api.py` | Unit tests for all JSON API endpoints (min 80 lines) | VERIFIED | 266 lines; 14 tests; 14/14 pass |
| `src/dashboard/presentation/app.py` | Mounts api_router via include_router | VERIFIED | Line 14: imports api_router; line 84: app.include_router(api_router) |
| `dashboard/package.json` | Next.js project configuration with Biome scripts | VERIFIED | next@16.1.6; scripts: lint (biome check), format (biome format --write) |
| `dashboard/next.config.ts` | API proxy rewrites to FastAPI | VERIFIED | rewrites() with source /api/:path* -> http://127.0.0.1:8000/api/:path* |
| `dashboard/biome.json` | Linter and formatter configuration | VERIFIED | $schema biomejs.dev/schemas/2.4.7; linter, formatter, javascript sections present |
| `dashboard/src/app/(dashboard)/page.tsx` | Overview page stub fetching /api/v1/dashboard/overview | VERIFIED | fetch('/api/v1/dashboard/overview') in useEffect; error/loading/data states |
| `dashboard/src/app/(dashboard)/layout.tsx` | Dashboard navigation layout | VERIFIED | Link hrefs to /, /signals, /risk, /pipeline with "Overview" text |
| `dashboard/src/app/(dashboard)/signals/page.tsx` | Signals page stub fetching /api/v1/dashboard/signals | VERIFIED | fetch('/api/v1/dashboard/signals') in useEffect |
| `dashboard/src/app/(dashboard)/risk/page.tsx` | Risk page stub fetching /api/v1/dashboard/risk | VERIFIED | fetch('/api/v1/dashboard/risk') in useEffect |
| `dashboard/src/app/(dashboard)/pipeline/page.tsx` | Pipeline page stub fetching /api/v1/dashboard/pipeline | VERIFIED | fetch('/api/v1/dashboard/pipeline') in useEffect |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/dashboard/presentation/api_routes.py` | `src/dashboard/application/queries.py` | QueryHandler instantiation and .handle() calls | WIRED | Lines 20-25 import all 4 handlers; each GET endpoint instantiates its handler and calls .handle() |
| `src/dashboard/presentation/app.py` | `src/dashboard/presentation/api_routes.py` | app.include_router(api_router) | WIRED | Line 14 imports api_router; line 84 calls app.include_router(api_router) |
| `src/dashboard/presentation/api_routes.py` | `src/dashboard/infrastructure/sse_bridge.py` | request.app.state.sse_bridge.stream() | WIRED | api_routes.py:219: bridge = request.app.state.sse_bridge; bridge.stream() called in async generator |
| `dashboard/src/app/(dashboard)/page.tsx` | `/api/v1/dashboard/overview` | fetch() in useEffect | WIRED | Line 9: fetch('/api/v1/dashboard/overview'); response handled via .then(setData)/.catch(setError) |
| `dashboard/next.config.ts` | `http://127.0.0.1:8000` | rewrites() destination | WIRED | Line 3: FASTAPI_URL defaults to 'http://127.0.0.1:8000'; line 10: destination = `${FASTAPI_URL}/api/:path*` |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SETUP-01 | 21-02-PLAN.md | Next.js 16 프로젝트를 trading 프로젝트 내에 생성하고 개발 환경이 동작한다 | SATISFIED | Next.js 16.1.6 in dashboard/; npm run build passes; dev script confirmed |
| SETUP-02 | 21-02-PLAN.md | Next.js rewrites로 FastAPI API 요청을 프록시할 수 있다 | SATISFIED | next.config.ts rewrites /api/:path* to http://127.0.0.1:8000/api/:path* |
| SETUP-03 | 21-01-PLAN.md | FastAPI에 JSON API 엔드포인트를 추가하여 기존 query handler 데이터를 JSON으로 응답한다 | SATISFIED | 11 JSON endpoints in api_routes.py; 14/14 unit tests pass; mounted in app.py |

All 3 Phase 21 requirements (SETUP-01, SETUP-02, SETUP-03) are satisfied and marked [x] in REQUIREMENTS.md. No orphaned requirements.

---

## Anti-Patterns Found

No anti-patterns found in phase files.

- No TODO/FIXME/PLACEHOLDER comments in api_routes.py, app.py, test file, or page stubs
- No empty implementations (return null, return {}, stub handlers)
- No fetch() calls without response handling
- No conflicting root src/app/page.tsx (deleted per plan)
- ESLint config absent (removed per plan)
- No Plotly.js, shadcn/ui, TanStack Query installed in Next.js project

**Pre-existing mypy issue (out of scope):** `src/pipeline/application/handlers.py:126` has a union-attr error introduced in commit `e0c1c06` (Phase gap-closure) which predates Phase 21. The SUMMARY explicitly documents this as a pre-existing issue not caused by Phase 21 changes. `api_routes.py` itself passes mypy with no errors. `ruff check src/dashboard/presentation/api_routes.py` passes with 0 errors.

---

## Human Verification Required

### 1. BFF Proxy End-to-End Data Flow

**Test:** Run `cd /home/mqz/workspace/trading && python3 -m uvicorn src.dashboard.presentation.app:create_dashboard_app --factory --port 8000` and separately `cd /home/mqz/workspace/trading/dashboard && npm run dev`. Visit localhost:3000/ in a browser.
**Expected:** Overview page displays raw JSON from FastAPI (total_value, positions, equity curve, regime_periods). Navigating to /signals, /risk, /pipeline each shows their respective JSON.
**Why human:** Requires both processes running simultaneously; tests only verify build and static structure.

### 2. Backend Offline Error State

**Test:** Start Next.js (`npm run dev`) without FastAPI running. Visit localhost:3000.
**Expected:** Page shows "Backend connection failed - Start FastAPI first: ..." in red text.
**Why human:** Code path verified statically (error handler present in all 4 stubs), but browser rendering of the error state requires runtime confirmation.

### 3. SSE Stream Through Proxy

**Test:** With both servers running, open browser DevTools Network tab, navigate to localhost:3000/pipeline. Trigger a pipeline run via the FastAPI app to emit an SSE event.
**Expected:** EventStream visible in Network tab at /api/v1/dashboard/events with JSON payloads (not HTML).
**Why human:** SSE proxy behavior through next.config.ts rewrites cannot be verified without a live connection.

---

## Gaps Summary

No gaps. All 20 observable truths verified, all 11 artifacts substantive and wired, all 5 key links confirmed, all 3 requirements satisfied.

**Test execution results:**
- 14/14 JSON API unit tests pass (tests/unit/test_dashboard_json_api.py)
- 29/29 HTMX regression tests pass (tests/unit/test_dashboard_web.py) — zero regression
- npm run build: 5 routes, 0 TypeScript errors
- npm run lint: 0 errors on 12 files (Biome)
- ruff check src/dashboard/presentation/api_routes.py: All checks passed
- Runtime: api_router confirmed 11 routes at import time

---

_Verified: 2026-03-14T10:30:00Z_
_Verifier: Claude (gsd-verifier)_
