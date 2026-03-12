# Stack Research -- v1.2 Additions

**Domain:** Automated trading pipeline, live trading, web dashboard
**Researched:** 2026-03-13
**Confidence:** HIGH
**Scope:** NEW dependencies only for v1.2 capabilities (automated scheduler, Alpaca live trading, web dashboard, real-time monitoring)

## Existing Stack (DO NOT re-add)

Everything from v1.0 and v1.1 is already installed and working. Listed for context only.

| Already Have | Version Installed | Relevant to v1.2 |
|-------------|-------------------|-------------------|
| FastAPI | 0.135.1 | Dashboard backend + existing API -- has native SSE since 0.135.0 |
| uvicorn | 0.41.0 | ASGI server for dashboard + API |
| Jinja2 | 3.1.2 | Already installed (FastAPI dep) -- use for HTML templates |
| Starlette | 0.52.1 | Already installed (FastAPI dep) -- SSE via `fastapi.sse` |
| alpaca-py | 0.43.2 | Existing Alpaca adapter -- `TradingClient(paper=True)` needs config change |
| pydantic | 2.12.5 | Data models, settings |
| pydantic-settings | 2.13.1 | Configuration management |
| SQLite | stdlib | Operational database (scores, signals, trade plans) |
| DuckDB | 1.5.0 | Analytical database (OHLCV, financials) |
| httpx | 0.28.1 | HTTP client |
| slowapi | 0.1.9 | Rate limiting (v1.1 addition) |
| PyJWT | 2.9.x | JWT auth (v1.1 addition) |

**Key existing capability:** FastAPI 0.135.1 already has built-in SSE support via `fastapi.sse.EventSourceResponse` and `ServerSentEvent`. No external SSE library needed. Jinja2 is already installed as a FastAPI dependency. This means the web dashboard can be built with zero frontend framework dependencies.

---

## New Dependencies for v1.2

### 1. Pipeline Scheduler: APScheduler

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| APScheduler | >=3.11.2 | Daily automated pipeline scheduling | Production-proven Python scheduler with cron triggers, SQLite job persistence, and asyncio support. `AsyncIOScheduler` runs alongside FastAPI's event loop without blocking. `SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')` persists job schedules across process restarts, so the daily screening pipeline resumes automatically after system reboot. 3.11.2 released Dec 2025, supports Python 3.8-3.13. | HIGH |

**Architecture integration:**

The scheduler runs as part of the same FastAPI process (not a separate daemon). The `AsyncIOScheduler` shares the asyncio event loop with uvicorn, eliminating the need for a separate process manager. Jobs trigger the existing pipeline functions:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler(
    jobstores={'default': SQLAlchemyJobStore(url='sqlite:///data/scheduler.db')},
)

# Daily screening at 7:00 AM ET (before market open)
scheduler.add_job(
    run_daily_pipeline,
    CronTrigger(hour=7, minute=0, timezone='US/Eastern'),
    id='daily_pipeline',
    replace_existing=True,
)
```

**Why APScheduler and not alternatives:**

| Alternative | Why Not |
|-------------|---------|
| Celery | Requires Redis/RabbitMQ broker. Massive infrastructure overhead for a single daily cron job. Designed for distributed task queues, not single-instance scheduling. |
| `schedule` (pip) | No job persistence (all jobs lost on restart). No asyncio support. No cron expressions. Fine for scripts, insufficient for production daemon. |
| System cron (`crontab`) | Cannot access Python process state (portfolio, approved strategies). Requires separate process management. No job persistence visibility. Cannot be managed from the web dashboard. |
| Airflow | DAG-based pipeline orchestrator. Runs its own web server, database, and scheduler as 3 separate processes. Absurd overhead for a single daily pipeline with 4 steps. |
| Prefect | Cloud-centric orchestrator. Similar to Airflow in complexity. Overkill for single-instance deployment. |

**APScheduler 4.0 note:** v4.0 is in alpha (4.0.0a1). It is an async-first ground-up redesign using AnyIO. Do NOT use it -- it is unstable and the API is not finalized. Stick with 3.11.x which is production-stable. Revisit 4.0 when it reaches stable release.

### 2. Web Dashboard: HTMX + Jinja2 (Python-Only Stack)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| HTMX | 2.0.x (CDN) | Hypermedia-driven interactive UI | Eliminates the need for React/Next.js. HTMX adds AJAX, SSE, and WebSocket capabilities to HTML via attributes. The dashboard sends HTML fragments from FastAPI, not JSON. Zero JS build toolchain (no npm, no webpack, no Node.js). Sub-50ms server-rendered updates. The existing FastAPI backend serves both the REST API and the dashboard from a single process. | HIGH |
| Plotly.py | >=6.5.0 | Interactive charts (candlesticks, P&L, allocation pie) | Generates standalone HTML/JS chart fragments that embed directly in HTMX templates. Native financial chart support (candlestick, OHLC, waterfall). plotly.js renders client-side from server-generated JSON specs. Already the standard for Python financial visualization. v6.5.2 released Jan 2026. | MEDIUM |

**HTMX is NOT a pip install.** It is a single JS file loaded via CDN `<script>` tag in the base HTML template:

```html
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
<!-- SSE extension for real-time dashboard updates -->
<script src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js"></script>
```

**Architecture integration:**

The web dashboard is a new set of FastAPI routes under `/dashboard/` that return Jinja2-rendered HTML instead of JSON. HTMX attributes on HTML elements trigger partial page updates:

```python
# commercial/api/routers/dashboard.py (or new personal/dashboard/)
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="templates")

@router.get("/portfolio")
async def portfolio_view(request: Request):
    holdings = await get_portfolio_holdings()
    return templates.TemplateResponse("portfolio.html", {"request": request, "holdings": holdings})
```

```html
<!-- templates/portfolio.html -->
<div hx-get="/dashboard/portfolio/table" hx-trigger="every 30s" hx-swap="innerHTML">
  <!-- Auto-refreshes holdings table every 30 seconds -->
  {% include "partials/holdings_table.html" %}
</div>

<!-- SSE for real-time order status updates -->
<div hx-ext="sse" sse-connect="/dashboard/stream" sse-swap="order_update">
  <!-- Live order status updates via Server-Sent Events -->
</div>
```

**Why HTMX + Jinja2 and not React/Next.js:**

| Criterion | HTMX + Jinja2 | React/Next.js |
|-----------|---------------|---------------|
| Languages needed | Python only | Python + TypeScript + JSX |
| Build toolchain | None | npm, webpack/turbopack, Node.js |
| Time to implement | Days | Weeks |
| Deployment | Same FastAPI process | Separate Node.js server or static build |
| Performance (TTI) | ~45ms (server-rendered) | ~650ms (client-side hydration) |
| Real-time updates | SSE via HTMX extension | WebSocket + React state management |
| Charting | Plotly.py generates HTML fragments | recharts/d3 (separate JS library) |
| Complexity for 1 developer | Low | High |
| SEO/public facing | N/A (personal dashboard) | N/A |

The dashboard is a personal tool for a single user (the trader), not a public web app serving thousands. HTMX eliminates an entire technology layer (Node.js/TypeScript/React) for no benefit. If the dashboard later needs to serve external users (SaaS product), React can be added then.

**Why Plotly.py and not alternatives:**

| Alternative | Why Not |
|-------------|---------|
| Matplotlib | Static images, not interactive. No zoom, no hover tooltips. Bad for financial charts. |
| Bokeh | Heavier than Plotly, less financial chart support. Requires separate Bokeh server for interactivity. |
| Chart.js (JS) | Would require writing JavaScript. Plotly.py generates the same quality charts from Python. |
| Lightweight Charts (TradingView) | JS-only library. Would need a separate JS build step or inline scripting. Good for later if pure candlestick experience needed. |
| Altair | Simpler API but less financial chart support. No native candlestick charts. |

### 3. Real-Time Monitoring: FastAPI Native SSE + Alpaca TradingStream

**No new dependencies needed.** Both capabilities exist in already-installed packages.

| Capability | Package | Already Installed | How |
|-----------|---------|-------------------|-----|
| Server-Sent Events | FastAPI 0.135.1 | Yes | `from fastapi.sse import EventSourceResponse, ServerSentEvent` |
| Alpaca order streaming | alpaca-py 0.43.2 | Yes | `from alpaca.trading.stream import TradingStream` |
| HTML templating | Jinja2 3.1.2 | Yes | `from fastapi.templating import Jinja2Templates` |

**SSE architecture for dashboard:**

```python
from fastapi.sse import EventSourceResponse, ServerSentEvent
from collections.abc import AsyncIterable

@router.get("/dashboard/stream", response_class=EventSourceResponse)
async def dashboard_stream() -> AsyncIterable[ServerSentEvent]:
    """SSE stream for real-time dashboard updates."""
    while True:
        event = await monitor.get_next_event()  # from internal event queue
        yield ServerSentEvent(
            data=event.to_json(),
            event=event.event_type,  # "order_update", "drawdown_alert", etc.
        )
```

**Alpaca TradingStream integration:**

```python
from alpaca.trading.stream import TradingStream

# Runs in background task, pushes events to internal queue
trading_stream = TradingStream(api_key, secret_key, paper=is_paper)

async def trade_update_handler(data):
    # Forward to SSE broadcast queue
    await monitor.broadcast(OrderUpdateEvent.from_alpaca(data))

trading_stream.subscribe_trade_updates(trade_update_handler)
```

The Alpaca `TradingStream` connects to `wss://paper-api.alpaca.markets/stream` (paper) or `wss://api.alpaca.markets/stream` (live) and delivers `trade_updates` events for order fills, partial fills, cancellations, and rejections.

### 4. Alpaca Live Trading: Configuration Change Only

**No new dependencies.** The existing `alpaca-py 0.43.2` supports live trading by changing `paper=True` to `paper=False` in `TradingClient`.

**Current code** (`src/execution/infrastructure/alpaca_adapter.py` line 43-44):
```python
self._client = TradingClient(
    self._api_key, self._secret_key, paper=True  # hardcoded
)
```

**Required change:** Make `paper` configurable via settings:
```python
self._client = TradingClient(
    self._api_key, self._secret_key, paper=self._paper_mode
)
```

**Alpaca live trading requirements:**
- Separate API key pair for live account (different from paper keys)
- Live account requires identity verification + funding
- Same SDK, same methods, different endpoint URLs internally
- Paper: `https://paper-api.alpaca.markets` / Live: `https://api.alpaca.markets`

**Configuration approach via pydantic-settings (already installed):**
```python
class AlpacaSettings(BaseSettings):
    api_key: str
    secret_key: str
    paper_mode: bool = True  # Default to paper, explicit opt-in for live

    model_config = SettingsConfigDict(env_prefix="ALPACA_")
```

**Safety guardrails for live trading:**
- `paper_mode` defaults to `True` -- must be explicitly set to `False`
- Daily budget limit in settings (max dollars auto-executed per day)
- Kill switch: setting to immediately halt all auto-execution
- Order confirmation logging before submission
- All live orders must pass the same risk gates (drawdown defense, position limits)

---

## Updated pyproject.toml Changes

Only additions needed (diff from current v1.1):

```toml
# ADD to [project] dependencies
dependencies = [
    # ... existing v1.0 + v1.1 deps unchanged ...

    # NEW v1.2: Pipeline scheduler
    "APScheduler>=3.11.2",

    # NEW v1.2: Interactive charts for dashboard
    "plotly>=6.5.0",
]
```

That is it. Two new pip packages. Everything else either exists already or is a CDN script tag (HTMX).

## Installation Commands

```bash
# Install new v1.2 dependencies
pip install "APScheduler>=3.11.2" "plotly>=6.5.0"

# Or update from pyproject.toml
pip install -e "."
```

---

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| Scheduler | APScheduler 3.11 | Celery + Redis | When scaling to multiple workers processing concurrent pipelines. Not needed for single daily cron. |
| Scheduler | APScheduler 3.11 | System crontab | When the job is a standalone script with no process state. Not suitable here because the scheduler needs access to approved strategies and portfolio state. |
| Dashboard | HTMX + Jinja2 | React + Next.js | When building a multi-user SaaS dashboard with complex client-side interactions. Overkill for a single-trader personal dashboard. |
| Dashboard | HTMX + Jinja2 | Streamlit | When building a quick data exploration prototype. Not suitable for production dashboard (RAM per session, session affinity, no custom layout). |
| Dashboard | HTMX + Jinja2 | Dash (Plotly) | When building a standalone analytics app with heavy Plotly integration. Adds Flask as second web framework alongside FastAPI -- redundant. |
| Real-time | Native FastAPI SSE | WebSocket | When bidirectional communication needed (e.g., interactive chat). Dashboard is server-push only (order updates, alerts), so SSE is simpler and sufficient. |
| Real-time | Native FastAPI SSE | sse-starlette | When running FastAPI < 0.135.0. We have 0.135.1, so native SSE is available. No external package needed. |
| Charts | Plotly.py | Bokeh | When you need a Bokeh server for streaming charts. Plotly generates standalone HTML that works without a separate server process. |
| Charts | Plotly.py | Matplotlib | When generating static PDF reports. Not suitable for interactive web dashboard charts. |
| Live trading | Alpaca (config change) | Alpaca + separate live wrapper | When you want a separate codebase for live trading. Unnecessary -- same SDK, same interface, just `paper=False`. |

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| React / Next.js / TypeScript | Adds entire Node.js toolchain for a single-user personal dashboard. HTMX achieves the same result in pure Python. | HTMX + Jinja2 + Plotly.py |
| Celery + Redis | Massive infrastructure for a single daily cron job. Redis is another process to manage. | APScheduler with SQLite jobstore |
| sse-starlette | Redundant. FastAPI 0.135.0+ has native SSE support via `fastapi.sse`. | `from fastapi.sse import EventSourceResponse` |
| Streamlit | Runs its own web server. Cannot integrate with existing FastAPI app. RAM scales linearly per session. | FastAPI + HTMX |
| Dash | Adds Flask as second web framework alongside FastAPI. Redundant. | Plotly.py (chart generation only, no Dash server) |
| APScheduler 4.0 | Alpha release (4.0.0a1). Unstable API, not production-ready. | APScheduler 3.11.2 (stable) |
| Redis | Not needed for v1.2. SSE replaces polling. APScheduler uses SQLite for persistence. slowapi uses in-memory storage. Redis adds infrastructure complexity for zero benefit at single-instance scale. | SQLite for persistence, in-memory for caching |
| Docker | Single-instance personal deployment. systemd or a process manager (pm2, supervisord) is sufficient. Docker adds complexity for a Python-only stack. | systemd service file or `nohup uvicorn ...` |
| Gunicorn | Single-instance with 1 worker. uvicorn alone is sufficient. Gunicorn adds process management overhead when we only need 1 process (scheduler + API + dashboard in same asyncio loop). | `uvicorn main:app --host 0.0.0.0 --port 8000` |

---

## Integration Points with Existing Stack

### Pipeline Scheduler + Existing Code

The scheduler calls functions that already exist:

| Pipeline Step | Existing Function/Handler | Trigger |
|---------------|--------------------------|---------|
| Data ingestion | `DataPipeline.ingest_universe()` | Cron 7:00 AM ET |
| Regime detection | `DetectRegimeHandler.handle()` | After data ingestion |
| Scoring | `ScoreSymbolHandler.handle()` | After regime detection |
| Signal generation | `GenerateSignalHandler.handle()` | After scoring |
| Auto-execution | `AlpacaExecutionAdapter.submit_bracket_order()` | After signal, within approved budget |

The scheduler is an orchestration layer on top of existing handlers -- no new business logic needed.

### Web Dashboard + Existing Repositories

The dashboard reads from the same SQLite/DuckDB stores that the CLI reads:

| Dashboard View | Data Source | Repository |
|----------------|-------------|------------|
| Portfolio holdings | SQLite `positions` | `SqlitePositionRepository` |
| Scoring results | SQLite `composite_scores` | `SqliteScoreRepository` |
| Signal history | SQLite `signals` | `SqliteSignalRepository` |
| Trade plans | SQLite `trade_plans` | `SqliteTradePlanRepository` |
| Regime status | SQLite `market_regimes` | `SqliteRegimeRepository` |
| OHLCV charts | DuckDB `ohlcv` | `DuckDBStore` |

No new data stores needed. The dashboard is a read-only presentation layer over existing repositories.

### Alpaca Live Trading + Existing Adapter

The change is confined to `src/execution/infrastructure/alpaca_adapter.py`:

1. Add `paper: bool` parameter to `__init__`
2. Pass `paper=self._paper` to `TradingClient`
3. Add `TradingStream` for real-time order updates
4. Add budget enforcement (daily limit check before order submission)

The rest of the execution pipeline (risk gates, position sizing, drawdown defense) remains unchanged.

### SSE + Existing Event System

The existing `AsyncEventBus` in `src/shared/infrastructure/event_bus.py` can be wired to feed SSE streams:

1. Domain events (ScoreUpdatedEvent, RegimeChangedEvent, etc.) published to AsyncEventBus
2. SSE subscriber listens to AsyncEventBus, forwards events to SSE broadcast queue
3. Dashboard clients receive events via `/dashboard/stream` SSE endpoint

This is the first real consumer of the event bus that was built in v1.0 but never used.

---

## Version Compatibility

| Package | Version | Compatible With | Notes |
|---------|---------|-----------------|-------|
| APScheduler 3.11.2 | Python 3.8-3.13 | Python 3.12 (project) | Uses SQLAlchemy internally for SQLite jobstore |
| Plotly 6.5.x | Python 3.9+ | Python 3.12 (project) | Generates standalone HTML/JS, no server-side deps |
| HTMX 2.0.x | Browser-side JS | Any server | CDN script, no Python dependency |
| FastAPI SSE | 0.135.0+ | FastAPI 0.135.1 (installed) | Native, no extra package |
| Alpaca TradingStream | alpaca-py 0.43.x | alpaca-py 0.43.2 (installed) | Same package, different class |

**No version conflicts.** APScheduler uses SQLAlchemy internally for its jobstore, which is a separate concern from the project's direct SQLite usage via `sqlite3` stdlib. They do not conflict -- APScheduler manages its own `scheduler.db` file.

---

## Stack Patterns by Variant

**If you need the scheduler to survive process crashes (recommended for live trading):**
- Use `SQLAlchemyJobStore(url='sqlite:///data/scheduler.db')` for persistent job schedules
- Use `misfire_grace_time=3600` so missed jobs (e.g., reboot during market hours) run when process restarts
- Run uvicorn via systemd with `Restart=always`

**If you need horizontal scaling later (multi-instance API):**
- Replace APScheduler's SQLite jobstore with PostgreSQL
- Replace slowapi's in-memory store with Redis backend
- Add Redis pub/sub for SSE broadcast across instances
- This is a v1.3+ concern, not v1.2

**If you want TradingView-quality candlestick charts later:**
- Add `lightweight-charts` JS library alongside HTMX (CDN script tag)
- Generate chart data in Python, render with TradingView's library client-side
- This is a cosmetic enhancement, not a v1.2 blocker

---

## Dependency Summary

### Must Add (2 packages)

| Package | Version | Purpose | Risk |
|---------|---------|---------|------|
| APScheduler | >=3.11.2 | Daily pipeline scheduler with cron triggers, SQLite persistence | Low -- mature, production-proven, 10+ years of releases |
| plotly | >=6.5.0 | Interactive financial charts for web dashboard | Low -- generates standalone HTML, no server-side complexity |

### Already Have (use what is installed)

| Package | Version | v1.2 Capability | What to Use |
|---------|---------|-----------------|-------------|
| FastAPI | 0.135.1 | Native SSE for real-time monitoring | `from fastapi.sse import EventSourceResponse` |
| Jinja2 | 3.1.2 | HTML template rendering for dashboard | `from fastapi.templating import Jinja2Templates` |
| alpaca-py | 0.43.2 | Live trading + TradingStream | `TradingClient(paper=False)`, `TradingStream` |
| pydantic-settings | 2.13.1 | Live/paper mode configuration | `AlpacaSettings` with `paper_mode: bool` |
| Starlette | 0.52.1 | Static file serving for dashboard assets | `from starlette.staticfiles import StaticFiles` |

### Browser-Side Only (no pip install)

| Asset | Version | Delivery | Purpose |
|-------|---------|----------|---------|
| HTMX | 2.0.4 | CDN `<script>` tag | Interactive HTML without JavaScript frameworks |
| htmx-ext-sse | 2.2.2 | CDN `<script>` tag | SSE extension for live dashboard updates |
| Plotly.js | (bundled with plotly.py) | Embedded in chart HTML | Client-side chart rendering |

### Do NOT Add

| Package | Reason |
|---------|--------|
| React / Next.js / TypeScript | Entire Node.js toolchain for single-user dashboard. HTMX achieves same result. |
| sse-starlette | Redundant. FastAPI 0.135.0+ has native SSE. |
| Celery / Redis | Massive overhead for single daily cron job. |
| Streamlit / Dash | Separate web servers. Cannot integrate with existing FastAPI. |
| APScheduler 4.0 | Alpha. Unstable API. Use 3.11.2. |
| Gunicorn | Single-instance. uvicorn alone sufficient. |
| Docker | Single-instance personal deployment. systemd sufficient. |

---

## Key Stack Decisions for v1.2

1. **HTMX over React** -- The dashboard is a personal tool for one trader. HTMX eliminates the Node.js/TypeScript/React toolchain entirely. The same FastAPI process serves both the REST API and the dashboard. If a multi-user SaaS dashboard is needed later, React can be added as a separate frontend then.

2. **APScheduler over Celery** -- A single daily pipeline (ingest -> regime -> score -> signal -> execute) runs as a cron job within the existing FastAPI process. No message broker, no separate worker process, no Redis. SQLite jobstore provides persistence across restarts.

3. **Native FastAPI SSE over WebSocket** -- Dashboard monitoring is server-push only (order fills, alerts, pipeline status). SSE is simpler than WebSocket for unidirectional data flow. FastAPI 0.135.1 has built-in SSE support, so no external package is needed.

4. **Plotly.py over Matplotlib/Bokeh** -- Generates interactive HTML chart fragments that embed directly in HTMX templates. Native financial chart types (candlestick, OHLC). The chart HTML renders client-side via plotly.js, so no extra server-side computation after initial generation.

5. **Alpaca config change over rewrite** -- Live trading requires only changing `paper=True` to a configurable `paper=self._settings.paper_mode`. The same `TradingClient` API, same order types, same bracket orders. The safety layer (budget limits, kill switch) is application logic, not a dependency concern.

6. **Total new pip packages: 2** (APScheduler + Plotly). Everything else is already installed or is a CDN script tag. This is the minimum viable addition for the four v1.2 capabilities.

---

## Sources

- [APScheduler PyPI](https://pypi.org/project/APScheduler/) -- v3.11.2, Dec 2025, verified 2026-03-13 (HIGH confidence)
- [APScheduler 3.x User Guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) -- AsyncIOScheduler, SQLAlchemyJobStore, CronTrigger (HIGH confidence)
- [Plotly.py PyPI](https://pypi.org/project/plotly/) -- v6.5.2, Jan 2026, verified 2026-03-13 (HIGH confidence)
- [FastAPI SSE Docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/) -- Native SSE in 0.135.0+, EventSourceResponse, ServerSentEvent (HIGH confidence)
- [Alpaca-py PyPI](https://pypi.org/project/alpaca-py/) -- v0.43.2, Nov 2025, confirmed (HIGH confidence)
- [Alpaca Trading SDK Docs](https://alpaca.markets/sdks/python/trading.html) -- TradingClient paper param, TradingStream WebSocket (HIGH confidence)
- [Alpaca WebSocket Streaming](https://alpaca.markets/docs/api-references/trading-api/streaming/) -- trade_updates events, live/paper endpoints (HIGH confidence)
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) -- v3.3.2, Feb 2026 -- confirmed NOT needed since FastAPI has native SSE (HIGH confidence)
- [HTMX + FastAPI Patterns 2025](https://johal.in/htmx-fastapi-patterns-hypermedia-driven-single-page-applications-2025/) -- SSR performance benchmarks (MEDIUM confidence)
- [Realtime Dashboard: FastAPI, Streamlit, Next.js](https://jaehyeon.me/blog/2025-03-04-realtime-dashboard-3/) -- Architecture comparison (MEDIUM confidence)
- Direct codebase analysis: `src/execution/infrastructure/alpaca_adapter.py` line 43-44 confirms `paper=True` hardcoded (HIGH confidence)
- Direct codebase analysis: `pip show` confirms installed versions of FastAPI 0.135.1, Jinja2 3.1.2, Starlette 0.52.1 (HIGH confidence)

---
*Stack research for: v1.2 Production Trading & Dashboard*
*Researched: 2026-03-13*
*All versions verified against PyPI + installed packages on 2026-03-13*
