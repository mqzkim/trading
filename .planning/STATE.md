---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Production Trading & Dashboard
status: in-progress
stopped_at: Completed 20-02-PLAN.md (CI test debt cleanup plan 2)
last_updated: "2026-03-13T20:04:38Z"
last_activity: 2026-03-14 -- Completed 20-02 test_api_routes.py rewrite
progress:
  total_phases: 10
  completed_phases: 8
  total_plans: 20
  completed_plans: 18
  percent: 90
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-13)

**Core value:** Every recommendation must be explainable and risk-controlled -- capital preservation and positive expectancy over maximizing returns.
**Current focus:** Phase 20 -- CI Test Debt Cleanup

## Current Position

Phase: 20 of 20 (CI Test Debt Cleanup) -- ninth of 10 phases
Plan: 2 of 2 complete
Status: In Progress
Last activity: 2026-03-14 -- Completed 20-02 test_api_routes.py rewrite

Progress: [█████████ ] 90%

## Performance Metrics

**Velocity:**
- Total plans completed: 48 (v1.0: 12, v1.1: 17, v1.2: 17, cleanup: 2)
- Average duration: ~5.9 min/plan
- Total execution time: ~3.5 hours

**By Phase (v1.1):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 5. Tech Debt | 3 | 22 min | 7.3 min |
| 6. Live Data | 3 | 21 min | 7.0 min |
| 7. Technical Scoring | 3 | 18 min | 6.0 min |
| 8. Regime Detection | 3 | 15 min | 5.0 min |
| 9. Signal Fusion | 2 | 9 min | 4.5 min |
| 10. Korean Broker | 2 | 12 min | 6.0 min |
| 11. Commercial API | 3 | 19 min | 6.3 min |

**By Phase (v1.2):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 12. Safety Infrastructure | 3/3 | 12 min | 4.0 min |
| 13. Pipeline Scheduler | 3/3 | 18 min | 6.0 min |
| 14. Strategy Approval | 2/2 | 14 min | 7.0 min |
| 15. Live Trading | 2/2 | 11 min | 5.5 min |
| 16. Web Dashboard | 4/4 | 28 min | 7.0 min |
| 17. SSE Event Wiring | 1/1 | 7 min | 7.0 min |
| 18. Drawdown Defense Wiring | 1/1 | 5 min | 5.0 min |
| Phase 18 P01 | 5min | 2 tasks | 3 files |
| Phase 19 P01 | 2min | 2 tasks | 2 files |
| Phase 19 P02 | 3min | 2 tasks | 2 files |
| Phase 20 P02 | 2min | 1 task | 1 file |

## Accumulated Context

### Decisions

Full decision log in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.2 research]: Single FastAPI process hosts commercial API + dashboard + APScheduler (no separate workers)
- [v1.2 research]: HTMX + Jinja2 for dashboard (no React/Node.js)
- [v1.2 research]: Only 2 new pip packages: APScheduler 3.11.2 + Plotly 6.5.x
- [v1.2 research]: Safety fixes before automation -- real money loss is irreversible
- [v1.2 research]: Paper automated before live -- validates orchestration without financial risk
- [12-01]: CooldownState is frozen dataclass (not ValueObject) -- needs optional id for persistence
- [12-01]: Expiry checked in Python not SQL for timezone safety
- [12-01]: WAL journal mode for concurrent safety between pipeline and CLI
- [12-02]: SafeExecutionAdapter accesses inner _client for polling -- acceptable in infrastructure layer
- [12-02]: Paper mode skips polling/leg verification -- only cooldown check applies
- [12-02]: AlpacaExecutionAdapter _init_client raises on failure instead of silent mock fallback
- [12-03]: KillSwitchService extracted as infrastructure service for testability
- [12-03]: PositionRepoProtocol avoids cross-context import (DDD compliance)
- [12-03]: Mock mode kill switch still creates cooldown for emotional re-entry prevention
- [Phase 12]: SafeExecutionAdapter accesses inner _client for polling -- acceptable in infrastructure layer
- [13-01]: exchange_calendars chosen over pandas_market_calendars (resolves blocker)
- [13-01]: SqlitePipelineRunRepository uses upsert for idempotent save
- [13-01]: Notifier uses Protocol (structural typing) not ABC
- [13-01]: StageResult stores succeeded_symbols list for downstream filtering
- [13-02]: Module-level function registration for APScheduler job targets (serialization constraint)
- [13-02]: Reconciliation check is application layer responsibility (DDD compliance)
- [13-02]: DataPipeline added to bootstrap context for orchestrator ingest stage
- [13-03]: DataClient import inline in _run_plan (matches existing cross-context import pattern)
- [13-03]: Auto-approve trade plans in _run_execute (manual approval deferred to Phase 14)
- [13-03]: Bootstrap creates SchedulerService but does NOT auto-start (caller responsibility)
- [14-01]: In-memory SQLite connection cached per repository instance (avoids separate DB per _get_conn() call)
- [14-01]: suspended_reasons stored as sorted JSON array for deterministic serialization
- [14-01]: GateResult checks ordered cheapest-first: existence, effectiveness, score, regime, position %, budget
- [14-02]: CLI subgroup named 'approval' (not 'approve') to avoid conflict with existing trade plan approve command
- [14-02]: Pipeline _run_execute backward compatible: missing approval_gate = skip execution
- [14-02]: RegimeChangedEvent handler normalizes RegimeType enum via .value for string comparison
- [15-01]: Circuit breaker trips on 3rd failure, calls kill switch with liquidate=False
- [15-01]: Notifier wired into SafeExecutionAdapter after pipeline notifier creation in bootstrap
- [15-01]: safe_adapter and kill_switch added to bootstrap context dict for CLI access
- [15-02]: AlpacaOrderMonitor uses threading.Lock for thread-safe tracked_orders access
- [15-02]: TradingStreamAdapter only created for LIVE mode in bootstrap
- [15-02]: Monitor/stream lifecycle tied to _run_execute finally block for guaranteed cleanup -- SUPERSEDED by 17-01
- [16-01]: SSE test uses route registration check instead of streaming test to avoid infinite stream hang
- [16-01]: TemplateResponse uses new Starlette API (request as first param) to avoid deprecation warnings
- [16-01]: sse-starlette added as explicit dependency for EventSourceResponse support
- [16-02]: Repos (score_repo, position_repo, regime_repo, trade_plan_repo) added to bootstrap ctx for dashboard access
- [16-02]: Equity curve v1 derives from trade history P&L accumulation (no daily snapshot table)
- [16-02]: Position current_price uses entry_price as proxy (no live price feed in v1)
- [16-02]: Trade history queries SQLite directly for EXECUTED trades (repo only has find_pending/find_by_symbol)
- [16-03]: SignalsQueryHandler maps CompositeScore VOs to flat dicts for template rendering
- [16-03]: RiskQueryHandler sector weights from entry_price * quantity (no live price feed in v1)
- [16-03]: Drawdown defaults to 0.0 without Portfolio aggregate -- SSE provides real-time updates
- [16-03]: signal_repo added to bootstrap ctx dict for dashboard query access
- [16-04]: python-multipart added as dependency for FastAPI Form data support
- [16-04]: Approval section and review queue as separate partials for independent HTMX swap
- [16-04]: SSE _render_partial dispatches by event type to render appropriate HTML partial
- [16-04]: PipelineQueryHandler delegates to approval_handler.get_status() for budget data
- [17-01]: Monitor/stream lifecycle moved from _run_execute to dashboard app lifespan
- [17-01]: PortfolioManagerHandler receives bus as optional param for backward compatibility
- [17-01]: Order monitor waits on empty queue instead of exiting -- persistent loop
- [18-01]: Only tier 2+ (warning/critical) triggers approval suspension; caution is tier 1 only
- [18-01]: portfolio_repo added to bootstrap ctx dict for pipeline handler access
- [18-01]: Default drawdown_level is "normal" when no portfolio exists (safe default)
- [Phase 18]: Only tier 2+ (warning/critical) triggers approval suspension; caution is tier 1 only
- [Phase 18]: portfolio_repo added to bootstrap ctx dict for pipeline handler access
- [Phase 18]: Default drawdown_level is normal when no portfolio exists (safe default)
- [19-01]: Module-level import for uvicorn/threading/webbrowser to enable unittest.mock.patch
- [19-01]: threading.Timer(1.5s) for delayed browser open before blocking uvicorn.run
- [19-01]: webbrowser.open wrapped in try/except for WSL2/headless compatibility
- [19-02]: RiskQueryHandler stores self._ctx for portfolio access (matches OverviewQueryHandler pattern)
- [19-02]: Drawdown fraction multiplied by 100 for gauge percentage display
- [19-02]: Equity curve P&L uses take_profit_price as exit proxy (optimistic upper bound, acceptable for v1)
- [20-02]: Auth route test uses /api/v1/auth/token (actual route) instead of /register (does not exist)

### Pending Todos

None.

### Blockers/Concerns

Carried forward:
- Alpaca paper trading does NOT simulate dividends -- separate tracking needed
- python-kis KIS developer registration -- may require Korean brokerage account

New for v1.2:
- Alpaca live account lead time -- identity verification and funding may gate Phase 15
- AsyncEventBus untested under concurrent load -- verify before Phase 15
- exchange_calendars vs pandas_market_calendars -- RESOLVED: exchange_calendars chosen in 13-01

## Session Continuity

Last session: 2026-03-13T20:03:04Z
Stopped at: Completed 20-02-PLAN.md (test_api_routes.py rewrite for v1.1 API)
Resume file: None
