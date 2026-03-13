---
phase: 17-sse-realtime-event-wiring
plan: 01
subsystem: dashboard
tags: [sse, htmx, fastapi, event-bus, real-time]

# Dependency graph
requires:
  - phase: 16-web-dashboard
    provides: SSEBridge, dashboard templates, /dashboard/events endpoint
  - phase: 15-live-trading-activation
    provides: AlpacaOrderMonitor, TradingStreamAdapter, OrderFilledEvent
provides:
  - SSE event name alignment across all dashboard templates
  - Bus.publish calls for PipelineCompletedEvent and PipelineHaltedEvent
  - Bus-wired PortfolioManagerHandler publishing DrawdownAlertEvent
  - Persistent order monitor lifecycle managed by dashboard app
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dashboard lifespan context manager for monitor/stream lifecycle"
    - "Domain event publishing in application handlers via bus param"

key-files:
  created:
    - tests/unit/test_sse_event_wiring.py
  modified:
    - src/dashboard/presentation/templates/overview.html
    - src/dashboard/presentation/templates/partials/regime_badge.html
    - src/dashboard/presentation/templates/partials/drawdown_gauge.html
    - src/dashboard/presentation/templates/partials/pipeline_status.html
    - src/dashboard/presentation/templates/partials/kpi_cards.html
    - src/pipeline/application/handlers.py
    - src/portfolio/application/handlers.py
    - src/bootstrap.py
    - src/execution/infrastructure/order_monitor.py
    - src/pipeline/domain/services.py
    - src/dashboard/presentation/app.py
    - tests/unit/test_order_monitor.py

key-decisions:
  - "Monitor/stream lifecycle moved from _run_execute to dashboard app lifespan"
  - "PortfolioManagerHandler receives bus as optional param for backward compatibility"
  - "Order monitor waits on empty queue instead of exiting -- persistent loop"

patterns-established:
  - "Application handlers publish domain events to bus after repository save"
  - "Dashboard lifespan manages background thread lifecycle"

requirements-completed: [DASH-07]

# Metrics
duration: 7min
completed: 2026-03-13
---

# Phase 17 Plan 01: SSE Event Wiring Summary

**Fixed 4 SSE gaps: 6 template event name mismatches, 2 missing bus.publish calls, and order monitor persistent lifecycle via dashboard lifespan**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-13T16:09:51Z
- **Completed:** 2026-03-13T16:16:48Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- All 6 template sse-swap attributes now use exact Python event class names (OrderFilledEvent, RegimeChangedEvent, DrawdownAlertEvent, PipelineCompletedEvent)
- RunPipelineHandler publishes PipelineCompletedEvent/PipelineHaltedEvent to event bus after pipeline run
- PortfolioManagerHandler pulls domain events and publishes DrawdownAlertEvent to bus after portfolio save
- AlpacaOrderMonitor runs persistently -- lifecycle managed by dashboard app startup/shutdown, not per-pipeline-run
- Structural test prevents future sse-swap name mismatches

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix SSE event name mismatches in templates + create test scaffold** - `2ef712f` (fix)
2. **Task 2: Wire missing bus.publish calls and fix order monitor lifecycle** - `b586a12` (feat)

## Files Created/Modified
- `tests/unit/test_sse_event_wiring.py` - 5 tests: template name match, pipeline event publish, halted event publish, drawdown event publish, monitor persistence
- `src/dashboard/presentation/templates/overview.html` - Fixed KpiUpdated -> OrderFilledEvent, OrderFilled -> OrderFilledEvent
- `src/dashboard/presentation/templates/partials/regime_badge.html` - Fixed RegimeChanged -> RegimeChangedEvent
- `src/dashboard/presentation/templates/partials/drawdown_gauge.html` - Fixed DrawdownTierChanged -> DrawdownAlertEvent
- `src/dashboard/presentation/templates/partials/pipeline_status.html` - Fixed PipelineStatusChanged -> PipelineCompletedEvent
- `src/dashboard/presentation/templates/partials/kpi_cards.html` - Fixed PipelineStatusChanged -> PipelineCompletedEvent
- `src/pipeline/application/handlers.py` - Added _publish_pipeline_event method after notification
- `src/portfolio/application/handlers.py` - Added bus param, pull_domain_events after save
- `src/bootstrap.py` - Wired bus into PortfolioManagerHandler
- `src/execution/infrastructure/order_monitor.py` - Changed break to wait+continue on empty queue
- `src/pipeline/domain/services.py` - Removed monitor/stream start/stop from _run_execute
- `src/dashboard/presentation/app.py` - Added lifespan context manager for monitor/stream lifecycle
- `tests/unit/test_order_monitor.py` - Updated test_monitor_stops_when_empty to test_monitor_persists_when_empty

## Decisions Made
- Monitor/stream lifecycle moved from _run_execute finally block to dashboard app lifespan -- ensures persistent monitoring across multiple pipeline runs
- PortfolioManagerHandler receives bus as optional keyword param (bus=None default) for backward compatibility with existing tests
- Order monitor waits on empty queue with _stop_event.wait(poll_interval) instead of breaking -- allows tracking new orders added after queue empties

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing test_monitor_stops_when_empty test**
- **Found during:** Task 2
- **Issue:** Existing test in test_order_monitor.py asserted old behavior (monitor exits on empty queue)
- **Fix:** Renamed to test_monitor_persists_when_empty, updated assertions to verify persistent behavior
- **Files modified:** tests/unit/test_order_monitor.py
- **Verification:** All 1085 tests pass
- **Committed in:** b586a12 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Test update was necessary consequence of behavior change. No scope creep.

## Issues Encountered
- Pre-existing test failures in test_api_routes.py (version mismatch 1.0.0 vs 1.1.0, 404 on score endpoint) -- unrelated to SSE changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All SSE wiring gaps from v1.2 milestone audit are now closed
- Dashboard receives real-time updates for all 4 event types
- No further phases planned after this gap closure

---
*Phase: 17-sse-realtime-event-wiring*
*Completed: 2026-03-13*
