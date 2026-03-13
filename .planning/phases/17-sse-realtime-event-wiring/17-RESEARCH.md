# Phase 17: SSE Real-Time Event Wiring - Research

**Researched:** 2026-03-14
**Domain:** SSE event bus wiring, HTMX SSE integration, domain event publishing
**Confidence:** HIGH

## Summary

Phase 17 is a gap closure phase that fixes 4 specific, well-defined issues preventing the dashboard from receiving real-time SSE updates. The audit (`v1.2-MILESTONE-AUDIT.md`) identifies exactly what is broken: (1) SSE event name mismatches between HTMX templates and Python class names, (2) RunPipelineHandler never publishes PipelineCompletedEvent to the event bus, (3) PortfolioManagerHandler never calls `pull_domain_events()` so DrawdownAlertEvent never reaches the bus, and (4) AlpacaOrderMonitor lifecycle is scoped to `_run_execute()` instead of being persistent.

All infrastructure is already in place: SSEBridge, SyncEventBus, event class definitions, template partials, and the `/dashboard/events` endpoint. This phase requires surgical fixes to existing files -- no new libraries, no new bounded contexts, no architectural changes.

**Primary recommendation:** Fix the 4 identified gaps in-place. No new infrastructure needed. Estimated 1 plan, touching 4-5 files.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DASH-07 | Dashboard receives real-time updates via SSE for order fills, pipeline events, and alerts | All 4 gaps identified below directly enable this requirement |
</phase_requirements>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| sse-starlette | (installed) | EventSourceResponse for SSE endpoint | Already wired |
| HTMX | (CDN) | `hx-ext="sse"`, `sse-connect`, `sse-swap` | Already in base.html |
| SyncEventBus | (internal) | Synchronous event bus for CLI/pipeline context | Already in bootstrap |
| SSEBridge | (internal) | Bridges SyncEventBus to async SSE consumers | Already wired to 5 event types |

### No New Dependencies Required

This phase adds zero new packages. All changes are wiring fixes within existing code.

## Architecture Patterns

### Current SSE Architecture (Working)
```
SyncEventBus ──publish──> SSEBridge._on_event() ──fan-out──> asyncio.Queue(s)
                                                                    │
                                                              SSE endpoint
                                                              /dashboard/events
                                                                    │
                                                            HTMX sse-swap
                                                        (matches event name)
```

### The 4 Gaps (With Exact Locations)

#### Gap 1: SSE Event Name Mismatches (3 templates)

SSEBridge emits `event.__class__.__name__` (Python class name). HTMX `sse-swap` must match exactly.

| Template | Current sse-swap | Server Emits | Fix |
|----------|-----------------|--------------|-----|
| `overview.html` line 10 | `sse-swap="OrderFilled"` | `OrderFilledEvent` | Change to `OrderFilledEvent` |
| `partials/regime_badge.html` line 1 | `sse-swap="RegimeChanged"` | `RegimeChangedEvent` | Change to `RegimeChangedEvent` |
| `partials/drawdown_gauge.html` line 2 | `sse-swap="DrawdownTierChanged"` | `DrawdownAlertEvent` | Change to `DrawdownAlertEvent` |
| `pipeline.html` line 7 | `sse-swap="PipelineCompletedEvent"` | `PipelineCompletedEvent` | Already correct |
| `partials/pipeline_status.html` line 1 | `sse-swap="PipelineStatusChanged"` | `PipelineCompletedEvent` | Change to `PipelineCompletedEvent` |
| `partials/kpi_cards.html` line 17 | `sse-swap="PipelineStatusChanged"` | `PipelineCompletedEvent` | Change to `PipelineCompletedEvent` |
| `overview.html` line 6 | `sse-swap="KpiUpdated"` | No such event | Remove or change to `OrderFilledEvent` |

**Note:** `_render_partial()` in routes.py already dispatches correctly by Python class name. The fix is only in HTMX template attributes.

#### Gap 2: RunPipelineHandler Never Publishes PipelineCompletedEvent

**Location:** `src/pipeline/application/handlers.py` -- `RunPipelineHandler.handle()`

**Current behavior:** After `orchestrator.run()` completes, handler saves to repo and sends notification, but never publishes to event bus.

**Fix:** RunPipelineHandler needs a `bus` reference. After save + notify, publish `PipelineCompletedEvent` (or `PipelineHaltedEvent`) to the bus.

**Implementation:**
```python
# In RunPipelineHandler.__init__:
self._bus = handlers.get("bus")

# After line 94 (self._send_notification(run)):
if self._bus is not None and run.status == PipelineStatus.COMPLETED:
    from src.pipeline.domain.events import PipelineCompletedEvent
    self._bus.publish(PipelineCompletedEvent(
        run_id=run.run_id,
        duration_seconds=run.duration.total_seconds() if run.duration else 0.0,
        symbols_succeeded=run.symbols_succeeded,
        mode=run.mode.value,
    ))
elif self._bus is not None and run.status == PipelineStatus.HALTED:
    from src.pipeline.domain.events import PipelineHaltedEvent
    self._bus.publish(PipelineHaltedEvent(
        run_id=run.run_id,
        halt_reason=run.halt_reason or "",
        regime_type="",
        drawdown_level="",
    ))
```

**DDD Note:** The bus reference comes from `handlers` dict (which is the bootstrap ctx). RunPipelineHandler already receives `handlers: dict` in its constructor. Accessing `handlers["bus"]` is consistent with existing patterns (e.g., `_run_execute` accesses `handlers.get("order_monitor")`).

#### Gap 3: PortfolioManagerHandler Never Calls pull_domain_events()

**Location:** `src/portfolio/application/handlers.py` -- `PortfolioManagerHandler.open_position()`

**Current behavior:** `Portfolio.add_position()` correctly calls `self.add_domain_event(DrawdownAlertEvent(...))` when drawdown is elevated. But `open_position()` never calls `portfolio.pull_domain_events()` and never publishes them to the bus.

**Fix:** After saving portfolio, pull events and publish to bus. Handler needs a `bus` parameter.

**Implementation:**
```python
# In PortfolioManagerHandler.__init__:
def __init__(self, portfolio_repo, position_repo, bus=None, ...):
    self._bus = bus

# After line 98 (self._portfolio_repo.save(portfolio)):
if self._bus is not None:
    for event in portfolio.pull_domain_events():
        self._bus.publish(event)
```

**Bootstrap change:** Pass `bus=bus` to `PortfolioManagerHandler(...)` in `bootstrap.py`.

#### Gap 4: AlpacaOrderMonitor Lifecycle Not Persistent

**Location:** `src/pipeline/domain/services.py` -- `PipelineOrchestrator._run_execute()`

**Current behavior:** Lines 432-433 start monitor, lines 503-507 stop it in `finally` block. Monitor only runs during `_run_execute()`, then stops. Fill events outside pipeline window are lost.

**Fix:** Move monitor start/stop to application lifecycle (FastAPI startup/shutdown) instead of per-pipeline-run. The monitor should run persistently when the dashboard app is running.

**Implementation approach:**
1. Remove `order_monitor.start()` / `order_monitor.stop()` from `_run_execute()`
2. Keep `order_monitor.track(order_id)` calls in `_run_execute()` (still need to register new orders)
3. Start monitor in `create_dashboard_app()` on startup, stop on shutdown
4. The `_monitor_loop` currently exits when `order_ids` is empty (line 88: `break`). Change to: continue looping (wait for new orders) instead of breaking when empty.

**Critical detail:** The monitor's `_monitor_loop` has `if not order_ids: break` -- this means even if started persistently, it exits immediately if no orders are tracked. Must change to a `wait` pattern instead of `break`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE event streaming | Custom WebSocket or polling | Existing SSEBridge + sse-starlette | Already built and tested |
| Event bus | New async bus | Existing SyncEventBus | Dashboard uses sync bus via SSEBridge |
| HTMX live updates | JavaScript EventSource manually | HTMX `sse` extension | Already wired in base.html |

## Common Pitfalls

### Pitfall 1: SSE Event Name Must Be Exact String Match
**What goes wrong:** HTMX `sse-swap="OrderFilled"` will never trigger if server sends `event: OrderFilledEvent`
**Why it happens:** SSEBridge uses `event.__class__.__name__` which includes the full class name
**How to avoid:** Always use the Python class name verbatim in `sse-swap` attributes
**Warning signs:** Dashboard loads fine on refresh but never updates in real-time

### Pitfall 2: Monitor Thread Exits on Empty Queue
**What goes wrong:** AlpacaOrderMonitor starts but exits immediately because no orders are tracked yet
**Why it happens:** `_monitor_loop` has `if not order_ids: break` on line 88
**How to avoid:** Replace `break` with `self._stop_event.wait(self._poll_interval)` to keep looping
**Warning signs:** Monitor thread "starts" but immediately ends

### Pitfall 3: Domain Events Accumulate If Not Pulled
**What goes wrong:** Portfolio aggregate accumulates `_domain_events` but they are never published
**Why it happens:** DDD pattern requires explicit `pull_domain_events()` + bus.publish loop
**How to avoid:** Always pull and publish domain events after saving an aggregate
**Warning signs:** Events exist in aggregate's internal list but bus subscribers never fire

### Pitfall 4: SyncEventBus vs AsyncEventBus
**What goes wrong:** Using wrong bus type causes SSEBridge to not receive events
**Why it happens:** Bootstrap creates SyncEventBus. SSEBridge subscribes to SyncEventBus. If someone uses AsyncEventBus, SSEBridge won't see those events.
**How to avoid:** All event publishing in this phase MUST use the SyncEventBus from ctx["bus"]
**Warning signs:** Events are published but SSE endpoint never sends them

### Pitfall 5: TradingStream Lifecycle Separate from Monitor
**What goes wrong:** TradingStream (WebSocket) is also started/stopped in _run_execute()
**Why it happens:** Same lifecycle issue as the monitor
**How to avoid:** Move TradingStream lifecycle to app startup/shutdown alongside monitor. Only for LIVE mode.
**Warning signs:** WebSocket fills only captured during pipeline execution window

## Code Examples

### Fix 1: Template sse-swap attributes
```html
<!-- overview.html - holdings table -->
<div id="holdings-table" class="bg-white rounded-lg shadow p-4 mb-6" sse-swap="OrderFilledEvent">

<!-- partials/regime_badge.html -->
<div class="bg-white rounded-lg shadow p-4" sse-swap="RegimeChangedEvent">

<!-- partials/drawdown_gauge.html -->
<div id="drawdown-chart-container" sse-swap="DrawdownAlertEvent">

<!-- partials/pipeline_status.html -->
<div sse-swap="PipelineCompletedEvent">
```

### Fix 2: Publish PipelineCompletedEvent in RunPipelineHandler
```python
# In RunPipelineHandler.handle(), after self._send_notification(run):
bus = self._handlers.get("bus")
if bus is not None:
    if run.status == PipelineStatus.COMPLETED:
        from src.pipeline.domain.events import PipelineCompletedEvent
        bus.publish(PipelineCompletedEvent(
            run_id=run.run_id,
            duration_seconds=run.duration.total_seconds() if run.duration else 0.0,
            symbols_succeeded=run.symbols_succeeded,
            mode=run.mode.value,
        ))
    elif run.status == PipelineStatus.HALTED:
        from src.pipeline.domain.events import PipelineHaltedEvent
        bus.publish(PipelineHaltedEvent(
            run_id=run.run_id,
            halt_reason=run.halt_reason or "",
        ))
```

### Fix 3: Pull and publish domain events in PortfolioManagerHandler
```python
# In PortfolioManagerHandler.open_position(), after self._portfolio_repo.save(portfolio):
if self._bus is not None:
    for event in portfolio.pull_domain_events():
        self._bus.publish(event)
```

### Fix 4: Persistent monitor loop
```python
# In AlpacaOrderMonitor._monitor_loop(), replace:
#   if not order_ids: break
# With:
if not order_ids:
    self._stop_event.wait(self._poll_interval)
    continue
```

## Files to Modify (Complete List)

| File | Change | Lines |
|------|--------|-------|
| `src/dashboard/presentation/templates/overview.html` | Fix `sse-swap` values (2 attrs) | ~2 lines |
| `src/dashboard/presentation/templates/partials/regime_badge.html` | Fix `sse-swap` value | 1 line |
| `src/dashboard/presentation/templates/partials/drawdown_gauge.html` | Fix `sse-swap` value | 1 line |
| `src/dashboard/presentation/templates/partials/pipeline_status.html` | Fix `sse-swap` value | 1 line |
| `src/dashboard/presentation/templates/partials/kpi_cards.html` | Fix `sse-swap` value | 1 line |
| `src/pipeline/application/handlers.py` | Publish PipelineCompleted/HaltedEvent after run | ~15 lines |
| `src/portfolio/application/handlers.py` | Add bus param, pull+publish domain events | ~8 lines |
| `src/bootstrap.py` | Pass bus= to PortfolioManagerHandler | 1 line |
| `src/execution/infrastructure/order_monitor.py` | Change empty-queue break to wait+continue | 2 lines |
| `src/pipeline/domain/services.py` | Remove monitor.start()/stop() from _run_execute | ~10 lines removed |
| `src/dashboard/presentation/app.py` | Add startup/shutdown for monitor+stream lifecycle | ~15 lines |
| `tests/unit/test_dashboard_sse.py` | Add tests for event name matching + bus publishing | ~50 lines |

**Total:** ~12 files, ~100 lines changed. Single plan.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio |
| Config file | `pytest.ini` (or pyproject.toml) |
| Quick run command | `pytest tests/unit/test_dashboard_sse.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-07a | SSE event names match between templates and server | unit | `pytest tests/unit/test_sse_event_wiring.py::test_event_names_match -x` | Wave 0 |
| DASH-07b | PipelineCompletedEvent published to bus after pipeline run | unit | `pytest tests/unit/test_sse_event_wiring.py::test_pipeline_completed_event_published -x` | Wave 0 |
| DASH-07c | DrawdownAlertEvent reaches bus via pull_domain_events | unit | `pytest tests/unit/test_sse_event_wiring.py::test_drawdown_event_published -x` | Wave 0 |
| DASH-07d | OrderMonitor persists beyond single pipeline run | unit | `pytest tests/unit/test_sse_event_wiring.py::test_monitor_persistent_loop -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_sse_event_wiring.py tests/unit/test_dashboard_sse.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_sse_event_wiring.py` -- covers DASH-07 (all 4 sub-behaviors)

## Open Questions

1. **Overview KPI cards sse-swap="KpiUpdated"**
   - What we know: There is no `KpiUpdatedEvent` in any domain. The `sse-swap` will never fire.
   - What's unclear: Whether KPI cards should update on OrderFilledEvent (holdings changed) or PipelineCompletedEvent (new scores), or both.
   - Recommendation: Wire to `OrderFilledEvent` since KPI cards show portfolio value which changes on fills. Can add `PipelineCompletedEvent` later if needed.

2. **TradingStream lifecycle**
   - What we know: TradingStream is also started/stopped within `_run_execute()`. Same lifecycle issue as monitor.
   - What's unclear: Whether TradingStream should also be persistent (only relevant in LIVE mode).
   - Recommendation: Move to app lifecycle alongside monitor, but only start for LIVE mode. This aligns with the existing conditional creation in bootstrap.

## Sources

### Primary (HIGH confidence)
- `v1.2-MILESTONE-AUDIT.md` -- exact gap descriptions with root causes
- Source code analysis of all affected files (SSEBridge, routes, templates, handlers, bootstrap)

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Event name mismatches | HIGH | Direct comparison of template sse-swap values vs Python class names |
| Missing bus.publish | HIGH | Read RunPipelineHandler.handle() -- no bus reference, no publish call |
| Missing pull_domain_events | HIGH | Read PortfolioManagerHandler.open_position() -- no pull call |
| Monitor lifecycle | HIGH | Read _run_execute() lines 432-507 -- explicit start/stop in finally |

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries, all existing
- Architecture: HIGH - surgical fixes to identified gaps
- Pitfalls: HIGH - gaps are concrete and verified by code reading

**Research date:** 2026-03-14
**Valid until:** Indefinite (code-specific findings, not library-version dependent)
