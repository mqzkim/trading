# Phase 21: Foundation - Research

**Researched:** 2026-03-14
**Domain:** Next.js 16 project setup, FastAPI JSON API endpoints, BFF proxy architecture
**Confidence:** HIGH

## Summary

Phase 21 establishes the foundation for the v1.3 Bloomberg Dashboard by doing three things: (1) creating a Next.js 16 project inside `trading/dashboard/`, (2) adding JSON API endpoints to the existing FastAPI backend that expose the same data the HTMX routes already serve, and (3) connecting the two via `next.config.ts` rewrites so that all `/api/*` requests from the Next.js dev server are transparently proxied to FastAPI at localhost:8000.

The existing Python backend has four `QueryHandler` classes (`OverviewQueryHandler`, `SignalsQueryHandler`, `RiskQueryHandler`, `PipelineQueryHandler`) that already return Python dicts. These dicts are currently fed into Jinja2 templates. The new JSON API simply calls the same handlers and returns the dicts as JSON responses. Additionally, five POST endpoints (pipeline run, approval create/suspend/resume, review approve/reject) need JSON equivalents that accept JSON body instead of HTML form data. The SSE endpoint (`/dashboard/events`) needs to be included in the rewrite rules for later phases.

The Next.js project should be minimal in this phase: the app must boot, serve a basic page, and demonstrate that the proxy works by fetching data from FastAPI. UI design, components, and styling are Phase 22 scope.

**Primary recommendation:** Use `next.config.ts` rewrites (not `proxy.ts`) for the API proxy because it is simpler, proven, and matches the CONTEXT.md decision. Create a new `api_routes.py` file in the Python backend with a `APIRouter(prefix="/api/v1/dashboard")` that wraps existing query handlers. Verify the full round-trip: Next.js page -> fetch `/api/v1/dashboard/overview` -> rewrite to FastAPI -> JSON response -> rendered in browser.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- JSON API 응답 구조: 기존 QueryHandler가 반환하는 Python dict를 그대로 JSON으로 반환. 별도 Pydantic DTO 변환 없음.
- 엔드포인트 URL: `/api/v1/dashboard/overview`, `/api/v1/dashboard/signals`, `/api/v1/dashboard/risk`, `/api/v1/dashboard/pipeline`
- 새 `APIRouter(prefix="/api/v1/dashboard")` 추가 -- 기존 `/dashboard/` HTML 라우트와 공존
- 기존 HTMX 라우트는 그대로 유지 (Phase 25 Cleanup에서 제거)
- 조회(GET) API + 변경(POST) API 모두 Phase 21에서 구현 (pipeline run, approval CRUD, review approve/reject)
- 터미널 2개 별도 실행: 터미널 1에서 FastAPI(8000), 터미널 2에서 Next.js(3000). 통합 스크립트 없음.
- Next.js 프로젝트 위치: `trading/dashboard/` (기존 Python `src/dashboard/`와 별도)
- 패키지 매니저: npm (시스템의 npm 10.9.4 사용)
- App Router 4개 페이지 플랫 구조: `app/(dashboard)/page.tsx` (Overview), `app/(dashboard)/signals/page.tsx`, `app/(dashboard)/risk/page.tsx`, `app/(dashboard)/pipeline/page.tsx`
- `next.config.ts` rewrites로 `/api/*` 요청을 `http://localhost:8000`으로 프록시
- SSE 프록시도 Phase 21에서 설정 (`/api/v1/dashboard/events` 경로 포함)
- FastAPI 미실행 시: "백엔드 연결 불가 - FastAPI를 먼저 실행하세요" 에러 메시지 표시

### Claude's Discretion
- Next.js 프로젝트 초기화 세부 설정 (tsconfig, biome 설정 등)
- JSON API 라우터 내부 구현 방식 (동일 QueryHandler 재사용 vs 래퍼)
- 에러 메시지 UI 컴포넌트 디자인
- TypeScript 타입 정의 방식

### Deferred Ideas (OUT OF SCOPE)
- None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SETUP-01 | Next.js 16 프로젝트를 trading 프로젝트 내에 생성하고 개발 환경이 동작한다 | `npx create-next-app@latest dashboard` with `--yes` flag creates project with TypeScript, Tailwind, ESLint, App Router, Turbopack. Node.js 22.x satisfies the 20.9+ requirement. Biome 2.4.7 replaces ESLint. |
| SETUP-02 | Next.js rewrites로 FastAPI API 요청을 프록시할 수 있다 | `next.config.ts` `rewrites()` confirmed working in Next.js 16.1.6 for external URL proxying. SSE streams pass through rewrites without buffering in dev mode. |
| SETUP-03 | FastAPI에 JSON API 엔드포인트를 추가하여 기존 query handler 데이터를 JSON으로 응답한다 | Existing `OverviewQueryHandler`, `SignalsQueryHandler`, `RiskQueryHandler`, `PipelineQueryHandler` return JSON-serializable dicts. New `APIRouter(prefix="/api/v1/dashboard")` wraps these handlers. POST endpoints convert from `Form()` to JSON body. |
</phase_requirements>

## Standard Stack

### Core (Phase 21 only)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.1.6 | React meta-framework with App Router | Latest stable. Turbopack default for fast dev. `rewrites()` proven for API proxying. |
| React | 19.x (bundled) | UI rendering | Bundled with Next.js 16. React Compiler stable. |
| TypeScript | 5.x (bundled) | Type safety | Default with `create-next-app`. Catches API contract mismatches early. |
| Tailwind CSS | 4.x (bundled) | Utility CSS | Default with `create-next-app`. CSS-first config in v4. |
| @biomejs/biome | 2.4.7 | Lint + format | Next.js 16 removed `next lint`. Biome is 35x faster than ESLint, handles both lint and format. |
| FastAPI | 0.135.1 (existing) | Python backend | Already running. New JSON router added alongside existing HTMX routes. |

### Not Yet Needed (Later Phases)

| Library | Phase | Purpose |
|---------|-------|---------|
| lightweight-charts | 22 | TradingView financial charts |
| @tanstack/react-query | 22 | Server state management |
| zustand | 22 | Client state management |
| next-themes | 22 | Dark/light theme toggle |
| shadcn/ui | 22 | Accessible UI components |

**Installation (Phase 21):**

```bash
# Step 1: Create Next.js project
cd /home/mqz/workspace/trading
npx create-next-app@latest dashboard --yes
# --yes uses defaults: TypeScript, Tailwind, ESLint, App Router, Turbopack

# Step 2: Replace ESLint with Biome
cd dashboard
npm uninstall eslint eslint-config-next @eslint/eslintrc
npm install -D --save-exact @biomejs/biome
npx biome init

# Step 3: Update package.json scripts
# Replace "lint": "next lint" with "lint": "biome check ."
# Add "format": "biome format --write ."
```

## Architecture Patterns

### Recommended Project Structure (Phase 21 scope only)

```
trading/
  dashboard/                    # NEW: Next.js 16 project
    src/
      app/
        (dashboard)/            # Route group (no URL segment)
          page.tsx              # Overview page (/)
          signals/
            page.tsx            # Signals page (/signals)
          risk/
            page.tsx            # Risk page (/risk)
          pipeline/
            page.tsx            # Pipeline page (/pipeline)
          layout.tsx            # Dashboard layout wrapper
        layout.tsx              # Root layout (html, body)
    next.config.ts              # Rewrites for API proxy + SSE
    biome.json                  # Linter/formatter config
    tsconfig.json               # TypeScript config (auto-generated)
    package.json
  src/
    dashboard/
      presentation/
        api_routes.py           # NEW: JSON REST API endpoints
        app.py                  # MODIFIED: mount api_routes router
        routes.py               # UNCHANGED: HTMX routes (kept)
      application/
        queries.py              # UNCHANGED: QueryHandlers reused
      infrastructure/
        sse_bridge.py           # UNCHANGED: SSE bridge
```

### Pattern 1: next.config.ts Rewrites for API Proxy

**What:** All browser requests to `/api/*` are transparently rewritten to `http://127.0.0.1:8000/api/*`. The browser never contacts FastAPI directly.

**Why rewrites over proxy.ts:** The CONTEXT.md locks this decision. Rewrites are simpler (declarative config), proven (stable since Next.js 10), and sufficient for this use case (no conditional logic needed). `proxy.ts` is the renamed `middleware.ts` in Next.js 16 -- use it only if you need programmatic request inspection (auth headers, A/B tests). For a single-user dashboard with static proxy rules, rewrites are correct.

```typescript
// dashboard/next.config.ts
import type { NextConfig } from 'next';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${FASTAPI_URL}/api/:path*`,
      },
      {
        source: '/api/v1/dashboard/events',
        destination: `${FASTAPI_URL}/api/v1/dashboard/events`,
      },
    ];
  },
};

export default nextConfig;
```

**Note:** The `/api/v1/dashboard/events` SSE rewrite is explicitly listed even though it matches the `/api/:path*` wildcard. This ensures it is documented and testable. In dev mode, Next.js rewrites do NOT buffer SSE streams -- they pass through transparently.

### Pattern 2: JSON API Routes Wrapping Existing QueryHandlers

**What:** A new `APIRouter(prefix="/api/v1/dashboard")` in `api_routes.py` that calls the exact same `QueryHandler` classes used by the HTMX routes, but returns JSON instead of HTML templates.

**Why this works:** The existing query handlers already return Python dicts. The HTMX routes feed these dicts into Jinja2 templates. The JSON routes just return the dicts directly (FastAPI auto-serializes to JSON). Zero business logic duplication.

```python
# src/dashboard/presentation/api_routes.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.dashboard.application.queries import (
    OverviewQueryHandler,
    PipelineQueryHandler,
    RiskQueryHandler,
    SignalsQueryHandler,
)

api_router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard-json"])


@api_router.get("/overview")
def api_overview(request: Request):
    ctx = request.app.state.ctx
    handler = OverviewQueryHandler(ctx)
    data = handler.handle()
    # Remove Plotly chart JSON -- frontend renders its own charts
    data.pop("equity_curve_chart_json", None)
    return data


@api_router.get("/signals")
def api_signals(request: Request, sort: str = "composite", desc: bool = True):
    ctx = request.app.state.ctx
    handler = SignalsQueryHandler(ctx)
    return handler.handle(sort_by=sort, sort_desc=desc)


@api_router.get("/risk")
def api_risk(request: Request):
    ctx = request.app.state.ctx
    handler = RiskQueryHandler(ctx)
    data = handler.handle()
    # Remove Plotly chart JSON -- frontend renders its own charts
    data.pop("gauge_json", None)
    data.pop("donut_json", None)
    return data


@api_router.get("/pipeline")
def api_pipeline(request: Request):
    ctx = request.app.state.ctx
    handler = PipelineQueryHandler(ctx)
    return handler.handle()
```

### Pattern 3: POST Endpoints Accept JSON Body (not Form data)

**What:** The existing HTMX POST endpoints use `Form(...)` parameters because HTMX submits HTML forms. The new JSON API must accept JSON request bodies for the React frontend to use `fetch()` with `Content-Type: application/json`.

**Key change:** Replace `Form(...)` with Pydantic models or plain function parameters for JSON body parsing.

```python
# POST endpoints in api_routes.py
from pydantic import BaseModel


class PipelineRunRequest(BaseModel):
    symbols: list[str] = []
    dry_run: bool = False


class ApprovalCreateRequest(BaseModel):
    score_threshold: float = 70.0
    allowed_regimes: list[str] = ["Bull", "Accumulation"]
    max_per_trade_pct: float = 8.0
    daily_budget_cap: float = 10000.0
    expires_in_days: int = 30


class ReviewActionRequest(BaseModel):
    review_id: int


class ApprovalActionRequest(BaseModel):
    approval_id: str | None = None


@api_router.post("/pipeline/run")
def api_pipeline_run(request: Request, body: PipelineRunRequest):
    # Same logic as existing route but with JSON body
    ...
    return {"status": "running", "symbols": body.symbols, "dry_run": body.dry_run}
```

### Pattern 4: Minimal Page Stubs for Round-Trip Verification

**What:** Phase 21 pages are skeleton stubs that demonstrate the proxy works. They fetch data from FastAPI and display raw JSON or minimal UI. Real UI components are Phase 22+.

```typescript
// dashboard/src/app/(dashboard)/page.tsx
'use client';

import { useEffect, useState } from 'react';

export default function OverviewPage() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/v1/dashboard/overview')
      .then((res) => {
        if (!res.ok) throw new Error(`Backend error: ${res.status}`);
        return res.json();
      })
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="p-8 text-red-500">
        Backend connection failed - Start FastAPI first: {error}
      </div>
    );
  }

  if (!data) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Overview</h1>
      <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}
```

### Anti-Patterns to Avoid

- **Importing DuckDB/SQLite in Node.js:** All data access goes through FastAPI HTTP endpoints. Never add `duckdb` or `better-sqlite3` to `package.json`. This project already had a DuckDB file lock conflict (commit `e0c1c06`).
- **Using Node.js subprocess to call Python:** CVE-2025-55182 (React2Shell, CVSS 10/10) demonstrated this is an RCE attack surface. Zero `child_process` imports in the Next.js codebase.
- **Adding Plotly.js to the frontend:** The existing charts.py uses Plotly server-side for HTMX. The React frontend uses TradingView Lightweight Charts (Phase 22). Do not add `plotly.js-dist` to `package.json` (1.2MB bundle).
- **Using proxy.ts when rewrites suffice:** `proxy.ts` (renamed middleware.ts) runs on every request and adds latency. Rewrites are declarative and only apply to matching paths.
- **Hardcoding `localhost:8000` in components:** Use environment variable `FASTAPI_URL` in `next.config.ts`. Components fetch from relative URLs (`/api/v1/dashboard/...`) which get rewritten.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API proxy | Custom Node.js proxy server | `next.config.ts` rewrites | Built into Next.js, handles headers/streaming correctly |
| JSON serialization | Manual `json.dumps()` calls | FastAPI auto-serialization | FastAPI JSONResponse handles datetime, Enum, nested dicts automatically |
| Linting + formatting | ESLint config + Prettier config | Biome 2.x single config | Next.js 16 removed `next lint`. Biome does both in one tool, 35x faster. |
| POST body parsing | Manual `request.json()` calls | Pydantic BaseModel | FastAPI validates + deserializes JSON body automatically with type safety |
| Error page for backend-down | Complex health check system | Simple try/catch on fetch | Phase 21 only needs a text message. Complex error UI is Phase 22. |

## Common Pitfalls

### Pitfall 1: SSE Endpoint Route Collision
**What goes wrong:** The CONTEXT.md specifies SSE at `/api/v1/dashboard/events`. But the existing SSE endpoint is at `/dashboard/events` (on the HTMX router). If the new JSON router also defines an SSE endpoint, both exist simultaneously during migration.
**Why it happens:** Two routers (`router` with prefix `/dashboard` and `api_router` with prefix `/api/v1/dashboard`) are mounted on the same FastAPI app.
**How to avoid:** Create a new SSE endpoint on the JSON router at `/api/v1/dashboard/events` that reuses the same `SSEBridge`. The old `/dashboard/events` stays for the HTMX dashboard. Both work simultaneously. The `next.config.ts` rewrite targets the new path.
**Warning signs:** SSE events not arriving in the Next.js app while they work in the old HTMX dashboard.

### Pitfall 2: Form Data vs JSON Body in POST Endpoints
**What goes wrong:** Existing HTMX POST endpoints use `Form(...)` parameters. If the new JSON API routes also use `Form(...)`, the React frontend must send `Content-Type: application/x-www-form-urlencoded` which is awkward with `fetch()`.
**Why it happens:** Copy-pasting the existing route code and only changing the return type.
**How to avoid:** New JSON POST endpoints accept Pydantic BaseModel bodies (JSON). Use `Body(...)` or model parameters, not `Form(...)`. React sends `JSON.stringify(body)` with `Content-Type: application/json`.
**Warning signs:** 422 Validation Error from FastAPI when the React frontend POSTs JSON to a Form-expecting endpoint.

### Pitfall 3: create-next-app Generates ESLint Config by Default
**What goes wrong:** Running `npx create-next-app@latest dashboard --yes` generates ESLint config files. If you then install Biome without removing ESLint, both linters run and produce conflicting rules.
**Why it happens:** The `--yes` flag uses defaults which include ESLint. Next.js 16 offers Biome as an option during interactive setup, but `--yes` skips the prompt and uses ESLint.
**How to avoid:** After `create-next-app`, uninstall `eslint eslint-config-next @eslint/eslintrc` and remove any `.eslintrc.*` files. Then install Biome and run `npx biome init`.
**Warning signs:** Two lint commands producing different results. `eslint.config.mjs` and `biome.json` both present.

### Pitfall 4: Route Group Parentheses in File System
**What goes wrong:** The CONTEXT.md specifies `app/(dashboard)/page.tsx` using a route group. If the parentheses are forgotten, the URL becomes `/dashboard/` which conflicts with the FastAPI HTMX route at the same path.
**Why it happens:** Route groups are a Next.js App Router feature where `(groupName)` creates a directory for organizational purposes without affecting the URL. `app/(dashboard)/page.tsx` serves `/`, not `/dashboard/`.
**How to avoid:** Ensure the directory name is literally `(dashboard)` with parentheses. Test by visiting `http://localhost:3000/` -- it should render the overview page, not `http://localhost:3000/dashboard/`.
**Warning signs:** 404 at `localhost:3000/` or unexpected routing at `localhost:3000/dashboard/`.

### Pitfall 5: Plotly Import in QueryHandler Return Data
**What goes wrong:** `RiskQueryHandler.handle()` currently returns `gauge_json` and `donut_json` fields which contain full Plotly figure JSON (generated by `charts.py` which imports `plotly`). If the JSON API returns these verbatim, the response includes ~50KB of Plotly-specific chart configuration data that the React frontend cannot use.
**Why it happens:** The Plotly chart data was generated for the HTMX dashboard's `<script>` tags.
**How to avoid:** The JSON API route should strip `gauge_json` and `donut_json` from the risk response. OR: keep them in the response (they are valid JSON) but the React frontend ignores them. Stripping is cleaner. Also strip any chart JSON from overview response.
**Warning signs:** Unexpectedly large API responses (>50KB for risk endpoint).

## Code Examples

### Example 1: Mounting the JSON API Router

```python
# In src/dashboard/presentation/app.py -- add 2 lines
from src.dashboard.presentation.api_routes import api_router

# Inside create_dashboard_app(), after app.include_router(router):
app.include_router(api_router)
```

### Example 2: SSE Endpoint on JSON Router

```python
# In api_routes.py
import json
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

@api_router.get("/events")
async def api_sse_events(request: Request):
    """SSE endpoint for JSON API -- sends raw JSON events (no HTML partials)."""
    bridge = request.app.state.sse_bridge

    async def event_generator():
        async for data in bridge.stream():
            if await request.is_disconnected():
                break
            event_type = data.get("type", "message")
            payload = data.get("payload", {})
            yield ServerSentEvent(
                data=json.dumps(payload),
                event=event_type,
            )

    return EventSourceResponse(event_generator())
```

### Example 3: Biome Configuration for Next.js

```json
{
  "$schema": "https://biomejs.dev/schemas/2.4.7/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "semicolons": "always"
    }
  },
  "files": {
    "ignore": [".next", "node_modules"]
  }
}
```

### Example 4: Dashboard Layout with Route Group

```typescript
// dashboard/src/app/(dashboard)/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <nav className="border-b p-4">
        <ul className="flex gap-4">
          <li><a href="/">Overview</a></li>
          <li><a href="/signals">Signals</a></li>
          <li><a href="/risk">Risk</a></li>
          <li><a href="/pipeline">Pipeline</a></li>
        </ul>
      </nav>
      <main className="p-4">{children}</main>
    </div>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `middleware.ts` | `proxy.ts` | Next.js 16 (Oct 2025) | Same functionality, renamed. Both work in 16.1.6. |
| `next lint` command | Direct ESLint/Biome CLI | Next.js 16 (Oct 2025) | `next build` no longer runs linter. Must run manually. |
| `tailwind.config.js` | CSS-first `@theme` in CSS file | Tailwind v4 (2025) | Config optional. `@import 'tailwindcss'` in CSS file. |
| Webpack bundler | Turbopack (default) | Next.js 16 (Oct 2025) | Turbopack is now default for both dev and build. |
| `next.config.js` | `next.config.ts` | Next.js 15+ | TypeScript config supported natively. |

**Key version facts (verified 2026-03-14):**
- `next@16.1.6` -- latest stable (npm registry)
- `@biomejs/biome@2.4.7` -- latest stable (npm registry)
- Node.js 22.22.1 installed on system -- satisfies Next.js 16 requirement of 20.9+
- npm 10.9.4 installed on system -- current stable

## Open Questions

1. **Plotly import in queries.py**
   - What we know: `RiskQueryHandler.handle()` calls `build_drawdown_gauge()` and `build_sector_donut()` from `charts.py`, which imports `plotly`. This import happens even for JSON API calls.
   - What is unclear: Whether to strip the chart generation entirely from the handler, or let it run and just exclude the keys from the JSON response.
   - Recommendation: Let it run (no handler modification). Strip `gauge_json` and `donut_json` in the JSON API route. This avoids modifying shared code that the HTMX dashboard still uses. Clean removal happens in Phase 25.

2. **SSE event data format**
   - What we know: The current SSEBridge sends `{"type": "EventName", "payload": {...}}`. The HTMX route handler adds HTML wrapping via `_render_partial()`. The React frontend needs raw JSON.
   - What is unclear: Whether the new SSE endpoint should send the full `{"type": ..., "payload": ...}` object, or just the payload with the event type as the SSE `event:` field.
   - Recommendation: Use SSE `event:` field for type and `data:` field for JSON payload. This matches the SSE spec (EventSource listeners use `addEventListener('EventType', ...)`) and is shown in the code example above.

3. **Route group `(dashboard)` vs flat structure**
   - What we know: CONTEXT.md specifies `app/(dashboard)/page.tsx`. Route groups add a layout boundary without affecting URLs.
   - What is unclear: Whether the dashboard layout should be at `app/(dashboard)/layout.tsx` or `app/layout.tsx`.
   - Recommendation: Put dashboard-specific layout (nav, sidebar) in `app/(dashboard)/layout.tsx`. Root `app/layout.tsx` handles only `<html>`, `<body>`, and providers. This way, if other non-dashboard pages are added later, they do not inherit the dashboard layout.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ (Python backend) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/unit/test_dashboard_web.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SETUP-01 | `npm run dev` starts Next.js at localhost:3000 | manual | `cd dashboard && npm run build` (build validates setup) | -- Wave 0 |
| SETUP-02 | Browser `/api/*` proxied to FastAPI and returns JSON | integration | `pytest tests/unit/test_dashboard_json_api.py -x -q` | -- Wave 0 |
| SETUP-03 | FastAPI serves JSON at `/api/v1/dashboard/*` endpoints | unit | `pytest tests/unit/test_dashboard_json_api.py -x -q` | -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_dashboard_json_api.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green + manual verification of `npm run dev` + proxy round-trip

### Wave 0 Gaps
- [ ] `tests/unit/test_dashboard_json_api.py` -- covers SETUP-03 (JSON API returns correct data for all 4 GET + 5 POST endpoints)
- [ ] Manual: `npm run dev` boots Next.js at localhost:3000 -- covers SETUP-01
- [ ] Manual: fetch `/api/v1/dashboard/overview` from Next.js returns FastAPI JSON -- covers SETUP-02
- [ ] `dashboard/` directory with valid `package.json` and `next.config.ts` -- covers SETUP-01

## Sources

### Primary (HIGH confidence)
- [Next.js 16.1.6 Installation Docs](https://nextjs.org/docs/app/getting-started/installation) -- create-next-app defaults, --yes flag, system requirements
- [Next.js Rewrites API Reference](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites) -- rewrite syntax, external URL proxying, path matching
- [Next.js Proxy Documentation](https://nextjs.org/docs/app/getting-started/proxy) -- proxy.ts (renamed middleware.ts), convention details
- npm registry: `next@16.1.6`, `@biomejs/biome@2.4.7` -- verified 2026-03-14
- Codebase: `src/dashboard/presentation/app.py` -- FastAPI app factory, SSE bridge wiring
- Codebase: `src/dashboard/application/queries.py` -- 4 QueryHandlers returning Python dicts
- Codebase: `src/dashboard/presentation/routes.py` -- existing HTMX routes + POST endpoints
- Codebase: `src/dashboard/infrastructure/sse_bridge.py` -- SSE event streaming
- Codebase: `tests/unit/test_dashboard_web.py` -- existing test patterns with mock ctx

### Secondary (MEDIUM confidence)
- Project research: `.planning/research/STACK.md` -- v1.3 stack decisions, version compatibility
- Project research: `.planning/research/ARCHITECTURE.md` -- BFF proxy pattern, data flow diagrams
- Project research: `.planning/research/PITFALLS.md` -- SSE buffering, DuckDB locks, chart memory leaks

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All versions verified in npm registry. Node.js/npm versions confirmed on system.
- Architecture: HIGH -- `next.config.ts` rewrites are a proven, documented Next.js feature. FastAPI query handler reuse is verified from codebase analysis.
- Pitfalls: HIGH -- Based on codebase analysis (actual file contents read), official Next.js docs, and prior project history (DuckDB lock commit).

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (30 days -- stable technologies, no breaking changes expected)
