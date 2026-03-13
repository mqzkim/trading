# Phase 16: Web Dashboard - Research

**Researched:** 2026-03-13
**Domain:** FastAPI + HTMX + Jinja2 + Tailwind CSS + SSE + Plotly (Python web dashboard)
**Confidence:** HIGH

## Summary

Phase 16 builds a browser-based dashboard for portfolio, pipeline, risk, and approval visibility. The entire stack is server-rendered: FastAPI serves Jinja2 templates styled with Tailwind CSS (Play CDN), HTMX handles partial updates, and SSE pushes real-time events. Plotly generates charts server-side (equity curve with regime overlay, drawdown gauge, sector donut). No JavaScript framework, no build step.

The project already has FastAPI 0.135.1 installed (native SSE via `EventSourceResponse` and `ServerSentEvent`), Jinja2 3.1.2 installed, and a fully wired `bootstrap.py` context with all repositories and handlers needed. The only new pip dependency is `plotly>=6.0`. Tailwind CSS loads from CDN (`<script src="https://cdn.tailwindcss.com">`). HTMX and htmx-ext-sse load from jsDelivr CDN.

**Primary recommendation:** Create a `dashboard/` bounded context under `src/` with `presentation/` (FastAPI routes + Jinja2 templates), `application/` (query handlers that aggregate data from existing repos), and `infrastructure/` (SSE bridge subscribing to SyncEventBus). No new domain layer needed -- dashboard reads from existing domains.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Sidebar + content area layout with 4 pages: Overview, Signals, Risk, Pipeline & Approval
- Paper/Live mode banner at top (DASH-09): Paper=green, Live=red
- CSS: Tailwind CSS (Play CDN, no build tools)
- Overview page: 4 hero KPIs (total assets, today P&L, drawdown %, last pipeline status) + holdings table + equity curve chart (Plotly) with regime overlay
- Signals page: sortable scoring table with heatmap-style background + strategy consensus + signal recommendations
- Risk page: semi-circular drawdown gauge (0-20%, green/yellow/red with 10/15/20% markers), sector exposure donut chart, position limit utilization, regime badge
- Pipeline & Approval page: pipeline runs table, strategy approval status/create form/suspend-resume buttons, daily budget progress bar, manual review queue with approve/reject buttons
- Trade History: table with date, ticker, buy/sell, quantity, entry price, stop, target, fill price, realized P&L, strategy source
- Single /events SSE endpoint streaming 4 event types: OrderFilled, PipelineStatusChanged, DrawdownTierChanged, RegimeChanged
- HTMX hx-ext='sse' with sse-swap for section replacement
- No authentication -- localhost:8000 only, personal tool

### Claude's Discretion
- Jinja2 template structure and inheritance patterns
- HTMX attribute details (hx-trigger, hx-swap strategy)
- Plotly chart configuration (colors, axes, layout)
- SSE event serialization format
- Sidebar icons/styling details
- FastAPI router structure (coexistence with commercial API)
- Trade History placement (in Overview or separate page)

### Deferred Ideas (OUT OF SCOPE)
- Mobile responsive layout -- DASH-10 (v2)
- Multi-user authentication -- DASH-11 (v2)
- React/Next.js migration -- DASH-12 (v2)
- Kill switch button from dashboard -- separate phase
- Per-symbol scoring history 90-day chart -- PIPE-08 (v2)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DASH-01 | Portfolio overview with holdings, P&L, allocation chart | Portfolio aggregate + PositionRepository already exist; Jinja2 template renders holdings table, Plotly for allocation |
| DASH-02 | Scoring and signal results for latest pipeline run | ScoreRepository.find_all_latest() + SignalRepository available via bootstrap ctx |
| DASH-03 | Trade history with execution details | TradePlanRepository.find_pending() + executed plans; need find_all() query method |
| DASH-04 | Risk metrics (drawdown gauge, sector exposure, position limits) | Portfolio.drawdown, sector_weight(), DrawdownLevel from portfolio domain |
| DASH-05 | Pipeline status (last run, next scheduled, stages) | PipelineRunRepository + SchedulerService.next_run_time() already exist |
| DASH-06 | Strategy approval and daily budget management | ApprovalHandler.get_status(), create(), revoke(), resume() + ReviewQueueRepository |
| DASH-07 | Real-time SSE updates for order fills, pipeline events, alerts | FastAPI native SSE (EventSourceResponse) + SyncEventBus bridge |
| DASH-08 | Equity curve chart with regime overlay | Plotly line chart + shapes for regime background colors; portfolio value history needed |
| DASH-09 | Paper/live mode banner | settings.EXECUTION_MODE already available; template conditional rendering |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.1 (installed) | Web framework, SSE, routing | Already in project, native SSE support added in 0.135.0 |
| Jinja2 | 3.1.2 (installed) | Server-side HTML templating | Already installed as FastAPI dependency |
| Plotly | 6.x (NEW -- install needed) | Charts (equity curve, gauge, donut) | Context decision: "Only 2 new pip packages: Plotly 6.5.x" |
| HTMX | 2.0.8 (CDN) | Partial page updates, SSE extension | No install -- loaded via CDN script tag |
| htmx-ext-sse | 2.2.4 (CDN) | SSE extension for HTMX | Companion to HTMX for EventSource integration |
| Tailwind CSS | Play CDN | Utility-first CSS | Context decision: "Play CDN for fast setup, no build tools" |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| plotly.js | 3.4.0 (CDN) | Client-side chart rendering | Plotly Python generates JSON config, plotly.js renders in browser |
| uvicorn | 0.24+ (installed) | ASGI server | Already used for commercial API |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plotly | Chart.js | Simpler but no built-in gauge/financial charts; Plotly is already decided |
| HTMX SSE | WebSocket | Bidirectional not needed; SSE is simpler, unidirectional server-to-client |
| Tailwind CDN | Tailwind CLI build | CDN is zero-config but larger payload; acceptable for personal localhost tool |

**Installation:**
```bash
pip install plotly>=6.0
```

Add to pyproject.toml dependencies:
```toml
"plotly>=6.0",
```

**CDN tags for base template:**
```html
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.4"></script>
<script src="https://cdn.plot.ly/plotly-3.4.0.min.js"></script>
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  dashboard/                    # New bounded context (read-only, no domain layer)
    DOMAIN.md                   # Context description
    __init__.py
    application/
      __init__.py
      queries.py                # DashboardOverviewQuery, RiskQuery, etc.
      handlers.py               # Read-only handlers aggregating from existing repos
    infrastructure/
      __init__.py
      sse_bridge.py             # SyncEventBus -> asyncio.Queue -> SSE stream
    presentation/
      __init__.py
      routes.py                 # FastAPI router: page routes + SSE endpoint + HTMX partials
      templates/
        base.html               # Layout: sidebar + content + CDN scripts + SSE connect
        overview.html            # Holdings table + KPI cards + equity curve
        signals.html             # Scoring table + signal recommendations
        risk.html                # Drawdown gauge + sector donut + limits
        pipeline.html            # Pipeline runs + approval + budget + review queue
        partials/                # HTMX swap fragments (SSE-triggered updates)
          holdings_table.html
          kpi_cards.html
          pipeline_status.html
          drawdown_gauge.html
          regime_badge.html
      static/
        css/                     # Optional custom CSS overrides (minimal)
```

### Pattern 1: SSE Bridge (SyncEventBus -> AsyncIO Queue -> SSE Stream)

**What:** The SyncEventBus publishes domain events synchronously in the CLI/pipeline thread. The dashboard SSE endpoint runs in an async FastAPI context. A bridge class subscribes to relevant events on the SyncEventBus and pushes them into an asyncio.Queue that the SSE endpoint yields from.

**When to use:** Whenever connecting synchronous domain events to async SSE streams.

**Example:**
```python
# src/dashboard/infrastructure/sse_bridge.py
import asyncio
import json
from typing import AsyncIterator
from src.shared.infrastructure.sync_event_bus import SyncEventBus

class SSEBridge:
    """Bridges SyncEventBus events to async SSE consumers."""

    def __init__(self, bus: SyncEventBus) -> None:
        self._bus = bus
        self._queues: list[asyncio.Queue] = []

    def _on_event(self, event) -> None:
        """Handler called synchronously by SyncEventBus."""
        data = {
            "type": event.__class__.__name__,
            "payload": {k: str(v) for k, v in event.__dict__.items()},
        }
        for q in list(self._queues):
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                pass  # Drop if consumer is too slow

    def subscribe_events(self, *event_types) -> None:
        """Subscribe to domain event types on the bus."""
        for et in event_types:
            self._bus.subscribe(et, self._on_event)

    async def stream(self) -> AsyncIterator[dict]:
        """Async generator yielding events for SSE endpoint."""
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.append(q)
        try:
            while True:
                data = await q.get()
                yield data
        finally:
            self._queues.remove(q)
```

### Pattern 2: Jinja2 Template Inheritance

**What:** Single base template with sidebar nav, mode banner, CDN scripts, and SSE connection. Each page extends base and fills content blocks.

**Example:**
```html
<!-- base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.4"></script>
  <script src="https://cdn.plot.ly/plotly-3.4.0.min.js"></script>
</head>
<body hx-ext="sse" sse-connect="/dashboard/events">
  <!-- Mode banner -->
  {% if execution_mode == "live" %}
  <div class="bg-red-600 text-white text-center py-1 font-bold">LIVE TRADING</div>
  {% else %}
  <div class="bg-green-600 text-white text-center py-1 font-bold">PAPER TRADING</div>
  {% endif %}

  <div class="flex">
    <!-- Sidebar -->
    <nav class="w-64 bg-gray-900 min-h-screen text-white p-4">
      <a href="/dashboard/" class="block py-2">Overview</a>
      <a href="/dashboard/signals" class="block py-2">Signals</a>
      <a href="/dashboard/risk" class="block py-2">Risk</a>
      <a href="/dashboard/pipeline" class="block py-2">Pipeline</a>
    </nav>
    <!-- Content -->
    <main class="flex-1 p-6 bg-gray-100">
      {% block content %}{% endblock %}
    </main>
  </div>
</body>
</html>
```

### Pattern 3: HTMX SSE Swap for Real-Time Updates

**What:** Child elements listen for named SSE events and swap HTML fragments.

**Example:**
```html
<!-- In overview.html, within the SSE-connected body -->
<div sse-swap="OrderFilled" hx-swap="innerHTML">
  {% include "partials/holdings_table.html" %}
</div>

<div sse-swap="PipelineStatusChanged" hx-swap="innerHTML">
  {% include "partials/kpi_cards.html" %}
</div>
```

The SSE endpoint sends named events:
```python
# In the SSE route
yield ServerSentEvent(
    data=rendered_html_fragment,
    event="OrderFilled",
)
```

### Pattern 4: Plotly Server-Side JSON Generation

**What:** Generate Plotly chart config as JSON in Python, pass to template, render with plotly.js on client.

**Example:**
```python
import plotly.graph_objects as go
import json

def build_equity_curve(values, dates, regime_periods):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=values, mode='lines', name='Equity'))

    # Regime overlay as background shapes
    for period in regime_periods:
        color = {"Bull": "rgba(0,255,0,0.1)", "Bear": "rgba(255,0,0,0.1)",
                 "Sideways": "rgba(255,255,0,0.1)", "Crisis": "rgba(128,128,128,0.2)"}
        fig.add_vrect(x0=period["start"], x1=period["end"],
                      fillcolor=color.get(period["regime"], "rgba(0,0,0,0)"),
                      layer="below", line_width=0)

    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=40, r=20, t=30, b=40))
    return json.loads(fig.to_json())
```

```html
<!-- In template -->
<div id="equity-chart"></div>
<script>
  const chartData = {{ chart_json | tojson }};
  Plotly.newPlot('equity-chart', chartData.data, chartData.layout, {responsive: true});
</script>
```

### Anti-Patterns to Avoid
- **Importing from commercial/ context:** Dashboard is a separate bounded context. Access data through bootstrap ctx repositories, not cross-context imports.
- **Writing to domain repos from dashboard:** Dashboard is READ-ONLY for data display. The only writes are approval management (create/revoke/resume) which go through existing ApprovalHandler.
- **Client-side state management:** No JavaScript state. HTMX swaps server-rendered HTML fragments. Keep logic server-side.
- **Async bootstrap:** The existing `bootstrap()` is synchronous. Do NOT create an async version. Use sync repos in FastAPI with `def` (not `async def`) route handlers, or wrap in `run_in_executor`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE protocol | Custom text/event-stream writer | FastAPI `EventSourceResponse` + `ServerSentEvent` | Handles keep-alive pings, cache headers, buffering headers automatically |
| Semi-circular gauge chart | SVG/Canvas from scratch | Plotly `go.Indicator` with gauge mode | Built-in gauge with threshold colors, reference lines |
| Donut chart | Custom SVG pie | Plotly `go.Pie` with hole parameter | Handles labels, hover, responsive sizing |
| CSS framework | Custom CSS | Tailwind CSS CDN | Utility classes eliminate need for custom stylesheets |
| Partial page updates | fetch() + DOM manipulation | HTMX `hx-get` / `sse-swap` | Declarative HTML attributes, no custom JS |
| Reconnection logic | Custom EventSource wrapper | htmx-ext-sse | Built-in exponential backoff reconnection |

**Key insight:** This dashboard has zero custom JavaScript beyond Plotly.newPlot() calls. Every interaction is HTMX declarative attributes or SSE-driven HTML swaps.

## Common Pitfalls

### Pitfall 1: Sync/Async Bridge Deadlock
**What goes wrong:** SyncEventBus handlers run in a sync thread. If they try to put events into an asyncio.Queue using `await`, it deadlocks because there's no running event loop in that thread.
**Why it happens:** FastAPI runs async but bootstrap + pipeline run synchronously.
**How to avoid:** Use `queue.put_nowait()` (not `await queue.put()`) in the sync handler. The asyncio.Queue supports `put_nowait` from any thread as long as the queue was created in the async context. Alternatively, use `loop.call_soon_threadsafe()`.
**Warning signs:** SSE endpoint connects but never receives events.

### Pitfall 2: SSE Connection Limits
**What goes wrong:** Browsers limit concurrent SSE connections per domain (typically 6 for HTTP/1.1). If dashboard opens in multiple tabs, connections exhaust.
**Why it happens:** Each tab opens its own EventSource to /events.
**How to avoid:** For a personal localhost tool this is unlikely to matter. If needed, use HTTP/2 (uvicorn with `--http h2`). Single-user usage means 1 tab = 1 connection.
**Warning signs:** Dashboard stops updating after opening several tabs.

### Pitfall 3: Template Not Found / Wrong Directory
**What goes wrong:** Jinja2Templates can't find templates because the path is relative to the wrong directory.
**Why it happens:** FastAPI's `Jinja2Templates(directory=...)` needs an absolute or correct relative path.
**How to avoid:** Use `Path(__file__).parent / "templates"` in the routes module to construct the template directory path.
**Warning signs:** 500 error with "TemplateNotFound".

### Pitfall 4: Plotly CDN Version Mismatch
**What goes wrong:** Python `plotly` library generates JSON for plotly.js v3.x but CDN loads v2.x, causing rendering errors.
**Why it happens:** `plotly-latest.min.js` CDN is frozen at v2.x (plotly deprecated the "latest" URL after v2).
**How to avoid:** Pin the CDN URL to a specific version matching the Python library: `plotly-3.4.0.min.js`.
**Warning signs:** Charts render with missing features or console errors.

### Pitfall 5: HTMX SSE Extension Not Loaded
**What goes wrong:** `sse-connect` and `sse-swap` attributes are silently ignored.
**Why it happens:** The SSE extension script must load AFTER htmx.js, and the `hx-ext="sse"` attribute must be on a parent element.
**How to avoid:** Load scripts in order: htmx.js first, then htmx-ext-sse. Place `hx-ext="sse"` on the `<body>` tag.
**Warning signs:** No EventSource connection in browser DevTools Network tab.

### Pitfall 6: FastAPI Route Ordering with Dashboard
**What goes wrong:** Dashboard routes conflict with commercial API routes or static file serving.
**Why it happens:** FastAPI matches routes in registration order. A catch-all route can shadow specific routes.
**How to avoid:** Mount dashboard router with prefix `/dashboard`. Mount static files at `/dashboard/static`. Register commercial API router first.
**Warning signs:** 404 errors or wrong page served.

## Code Examples

### FastAPI App Creation with Dashboard Router
```python
# src/dashboard/presentation/routes.py
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.sse import EventSourceResponse, ServerSentEvent

TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

from fastapi import APIRouter
router = APIRouter(prefix="/dashboard")

@router.get("/", response_class=HTMLResponse)
def overview(request: Request):
    # Gather data from bootstrap ctx (injected via app.state)
    ctx = request.app.state.ctx
    portfolio_handler = ctx["portfolio_handler"]
    positions = portfolio_handler._position_repo.find_all_open()
    # ... aggregate data
    return templates.TemplateResponse("overview.html", {
        "request": request,
        "positions": positions,
        "execution_mode": ctx["execution_mode"].value,
    })
```

### SSE Endpoint with Named Events
```python
# Source: FastAPI 0.135.0 native SSE docs
from collections.abc import AsyncIterable

@router.get("/events", response_class=EventSourceResponse)
async def sse_events(request: Request) -> AsyncIterable[ServerSentEvent]:
    bridge = request.app.state.sse_bridge
    async for event_data in bridge.stream():
        # Render HTML partial for the event type
        html = render_partial(event_data["type"], event_data["payload"])
        yield ServerSentEvent(
            data=html,
            event=event_data["type"],
        )
```

### Drawdown Gauge with Plotly
```python
import plotly.graph_objects as go
import json

def build_drawdown_gauge(current_drawdown_pct: float) -> dict:
    """Build semi-circular gauge for drawdown (0-25%)."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_drawdown_pct * 100,
        number={"suffix": "%"},
        gauge={
            "axis": {"range": [0, 25], "tickwidth": 1},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 10], "color": "rgb(34, 197, 94)"},    # green
                {"range": [10, 15], "color": "rgb(234, 179, 8)"},    # yellow
                {"range": [15, 20], "color": "rgb(239, 68, 68)"},    # red
                {"range": [20, 25], "color": "rgb(127, 29, 29)"},    # dark red
            ],
            "threshold": {
                "line": {"color": "white", "width": 2},
                "thickness": 0.75,
                "value": current_drawdown_pct * 100,
            },
        },
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=10))
    return json.loads(fig.to_json())
```

### HTMX Form Submission (Approval Create)
```html
<!-- In pipeline.html -->
<form hx-post="/dashboard/approval/create" hx-target="#approval-status" hx-swap="innerHTML">
  <input type="number" name="score_threshold" placeholder="Score threshold" step="0.1" />
  <input type="text" name="allowed_regimes" placeholder="Bull,Sideways" />
  <input type="number" name="max_per_trade_pct" placeholder="Max per-trade %" step="0.1" />
  <input type="number" name="daily_budget_cap" placeholder="Daily budget $" />
  <input type="number" name="expires_in_days" placeholder="Expires in days" value="30" />
  <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded">Create Approval</button>
</form>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| sse-starlette third-party lib | FastAPI native `EventSourceResponse` | FastAPI 0.135.0 (Jan 2025) | No extra dependency needed; built-in keep-alive, headers |
| plotly-latest.min.js CDN | Pin specific version `plotly-3.x.x.min.js` | Plotly.js v2+ (2021) | Must use exact version URL, "latest" frozen at v2 |
| HTMX v1 `hx-sse` attribute | HTMX v2 `hx-ext="sse"` extension | HTMX 2.0 (2024) | SSE moved from built-in to extension; need separate script |

**Deprecated/outdated:**
- `sse-starlette` package: Still works but unnecessary with FastAPI 0.135+ native SSE
- `hx-sse` attribute: Removed in HTMX v2; replaced by `hx-ext="sse"` + `sse-connect` + `sse-swap`
- `plotly-latest.min.js`: Frozen at v2.x, do not use

## Open Questions

1. **Equity Curve Data Source**
   - What we know: Portfolio aggregate has current value and positions, but no historical equity curve data
   - What's unclear: Where daily portfolio snapshots are stored for the time-series chart
   - Recommendation: If no snapshot table exists, either (a) create a simple SQLite table that stores daily total_value snapshots (populated by pipeline), or (b) derive from trade history for v1. The planner should allocate a task for this.

2. **Trade History Query Completeness**
   - What we know: TradePlanRepository has `find_pending()` and `find_by_symbol()` but no `find_all()` or `find_executed()` method
   - What's unclear: Whether executed trade plans persist fill price and realized P&L
   - Recommendation: May need to add `find_recent_executed(limit)` to TradePlanRepository or query the SQLite table directly. Check actual schema in implementation.

3. **FastAPI App Lifecycle**
   - What we know: No FastAPI app exists yet (CONTEXT.md says "FastAPI app does not exist -- create new")
   - What's unclear: Whether to create a single `app.py` that mounts both commercial API and dashboard, or separate apps
   - Recommendation: Single FastAPI app in `src/dashboard/presentation/app.py` that also imports and includes commercial API router. This matches the v1.2 decision: "Single FastAPI process hosts commercial API + dashboard + APScheduler."

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4+ |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/unit/test_dashboard_web.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | Overview page renders holdings and P&L | unit | `pytest tests/unit/test_dashboard_web.py::test_overview_page -x` | No -- Wave 0 |
| DASH-02 | Signals page renders scoring table | unit | `pytest tests/unit/test_dashboard_web.py::test_signals_page -x` | No -- Wave 0 |
| DASH-03 | Trade history table renders | unit | `pytest tests/unit/test_dashboard_web.py::test_trade_history -x` | No -- Wave 0 |
| DASH-04 | Risk page shows drawdown gauge and sector chart | unit | `pytest tests/unit/test_dashboard_web.py::test_risk_page -x` | No -- Wave 0 |
| DASH-05 | Pipeline status page renders runs | unit | `pytest tests/unit/test_dashboard_web.py::test_pipeline_page -x` | No -- Wave 0 |
| DASH-06 | Approval create/revoke/resume via HTMX | unit | `pytest tests/unit/test_dashboard_web.py::test_approval_actions -x` | No -- Wave 0 |
| DASH-07 | SSE endpoint streams events | unit | `pytest tests/unit/test_dashboard_sse.py -x` | No -- Wave 0 |
| DASH-08 | Equity curve chart JSON generated | unit | `pytest tests/unit/test_dashboard_charts.py -x` | No -- Wave 0 |
| DASH-09 | Mode banner shows paper/live | unit | `pytest tests/unit/test_dashboard_web.py::test_mode_banner -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_dashboard_web.py tests/unit/test_dashboard_sse.py tests/unit/test_dashboard_charts.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_dashboard_web.py` -- covers DASH-01 through DASH-06, DASH-09
- [ ] `tests/unit/test_dashboard_sse.py` -- covers DASH-07
- [ ] `tests/unit/test_dashboard_charts.py` -- covers DASH-08
- [ ] `plotly>=6.0` pip install needed
- [ ] FastAPI TestClient for route testing (already available via `httpx` in dev deps)

## Sources

### Primary (HIGH confidence)
- [FastAPI SSE Tutorial](https://fastapi.tiangolo.com/tutorial/server-sent-events/) - Native SSE with EventSourceResponse, ServerSentEvent, async generators
- [HTMX SSE Extension](https://htmx.org/extensions/sse/) - sse-connect, sse-swap, event handling, CDN URLs
- [FastAPI Templates](https://fastapi.tiangolo.com/advanced/templates/) - Jinja2Templates setup
- Project codebase: `src/bootstrap.py`, `src/settings.py`, all domain repos and events

### Secondary (MEDIUM confidence)
- [Plotly.js Releases](https://github.com/plotly/plotly.js/releases) - v3.4.0 latest, CDN versioning
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) - Confirmed unnecessary with FastAPI 0.135+
- [Tailwind CSS Play CDN](https://tailwindcss.com/docs/installation/play-cdn) - Zero-config CDN approach

### Tertiary (LOW confidence)
- Plotly Python v6.x gauge/indicator API details -- verify exact API against installed version

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries confirmed installed or available via CDN; FastAPI SSE verified against official docs
- Architecture: HIGH - Pattern follows existing DDD structure; bootstrap ctx provides all needed dependencies
- Pitfalls: HIGH - Sync/async bridge is the primary technical risk; well-documented pattern
- Charts: MEDIUM - Plotly gauge/indicator API details need verification against v6.x

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable stack, no fast-moving dependencies)
