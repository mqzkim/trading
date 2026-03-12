# Project Research Summary

**Project:** Intrinsic Alpha Trader v1.2 — Production Trading & Dashboard
**Domain:** Automated trading pipeline, live execution, strategy/budget approval workflow, web dashboard
**Researched:** 2026-03-13
**Confidence:** HIGH

## Executive Summary

This milestone transitions an already-functional v1.1 system (manual CLI-driven scoring, regime detection, signal fusion, paper trading, and a commercial FastAPI REST API) into a production-grade automated trading platform. The core engineering challenge is not building capabilities from scratch — almost every domain handler and data store already exists — but rather wiring them together safely for automated, real-money operation. The system already knows how to score symbols, detect regimes, generate signals, and submit paper orders; v1.2 is about having those steps run daily without a human typing each CLI command, and having them execute real orders with appropriate safeguards.

The recommended approach across all four research dimensions converges on a single, unified process: a FastAPI application that hosts the commercial REST API, the personal web dashboard, and an embedded APScheduler daemon — all sharing the same DDD handlers, SQLite stores, and async event bus. This in-process architecture eliminates inter-process communication overhead, avoids an entire infrastructure layer (Redis, Celery, message queues), and leverages the `AsyncEventBus` that was built in v1.0 but never had a real consumer. HTMX + Jinja2 (no React, no Node.js) provides the dashboard UI through the same FastAPI process. Only two new pip packages are required: APScheduler and Plotly.

The primary risk is transitioning from paper to live trading without adequate safeguards. Research identified seven critical pitfalls specific to this codebase — including a hardcoded `paper=True` flag that can be toggled without any safety gate, a silent mock-fallback pattern that can mask real order failures with phantom fills, missing cooldown persistence for the drawdown defense, and no state reconciliation between the system's SQLite records and the broker's actual positions. These are not theoretical risks; they are concrete code patterns already in `src/execution/infrastructure/alpaca_adapter.py` and `personal/risk/drawdown.py` that must be corrected before any live execution begins.

## Key Findings

### Recommended Stack

The v1.2 stack requires only two new pip packages on top of the existing v1.1 installation: `APScheduler>=3.11.2` for cron-based pipeline scheduling, and `plotly>=6.5.0` for interactive financial charts in the web dashboard. Everything else is already installed. FastAPI 0.135.1 includes native SSE support (`from fastapi.sse import EventSourceResponse`) that eliminates the need for `sse-starlette`. Jinja2 3.1.2 is already a FastAPI dependency. HTMX 2.0.x is delivered as a CDN script tag — no npm, no webpack, no Node.js. `alpaca-py 0.43.2` already supports live trading via `TradingClient(paper=False)` and real-time order streaming via `TradingStream`.

**Core technologies:**
- **APScheduler 3.11.2:** Daily cron scheduling with SQLite-backed job persistence — use `AsyncIOScheduler` with `SQLAlchemyJobStore`; run in-process alongside FastAPI's event loop. Do NOT use v4.0 alpha (unstable API).
- **HTMX 2.0.x (CDN):** Hypermedia-driven UI without a JavaScript framework — enables interactive dashboard from Jinja2 templates with zero build toolchain; HTMX SSE extension bridges to FastAPI's native SSE stream.
- **Plotly 6.5.x:** Generates standalone interactive chart HTML from Python — candlestick, equity curve, sector pie charts; embeds directly in Jinja2 partials; no separate chart server needed.
- **FastAPI native SSE:** Already available in installed FastAPI 0.135.1 — used for real-time dashboard push of order fills, pipeline stage events, drawdown alerts.
- **Alpaca TradingStream:** Already in installed `alpaca-py 0.43.2` — subscribes to `wss://api.alpaca.markets/stream` for live order fill events.

### Expected Features

**Must have (table stakes for v1.2):**
- Daily cron pipeline: data ingest -> regime -> score -> signal -> trade plan, running with market-calendar awareness (skip weekends, NYSE holidays)
- Market calendar guard on pipeline execution — no orders on holidays, outside trading hours, or on early-close days
- Strategy/budget approval entity: approve trading rules (score threshold, regime allow-list, max per-trade %) with mandatory expiration date
- Daily budget cap enforced per pipeline run with spent-vs-remaining tracking
- Live trading mode guard: explicit `EXECUTION_MODE=live` required (cannot be triggered by credentials alone)
- Separate API key pairs for paper and live Alpaca accounts (never share keys)
- Post-order status polling until terminal state (filled, rejected, cancelled)
- Bracket leg verification after fill (stop-loss and take-profit legs confirmed active)
- Portfolio reconciliation at pipeline start: compare SQLite position records with Alpaca `get_positions()`
- Persistent cooldown state for drawdown defense (30-day cooling period survives process restarts)
- Pipeline run log per execution (stages completed, counts, errors, next scheduled run)
- Web dashboard: portfolio overview, P&L chart, signal results, risk indicators, approval control panel, pipeline status
- Kill switch: cancel all open orders + halt pipeline immediately

**Should have (differentiators):**
- Alpaca TradingStream WebSocket for real-time fill notifications (replaces polling)
- Regime-conditional auto-execution ("auto in Bull/Sideways, manual in Bear, halt in Crisis")
- Drawdown-triggered approval suspension (tier 2+ auto-suspends strategy approval)
- Dashboard approval form (approve strategy from browser instead of CLI only)
- Pipeline dry-run mode (full run without order submission for validation)
- Per-stage retry with exponential backoff (yfinance timeouts do not abort entire pipeline)
- Equity curve chart with regime overlay
- Score evolution chart per symbol over 90 days

**Defer (v2+):**
- Mobile-responsive dashboard
- Multi-user dashboard with login (personal tool, single user)
- React/Next.js frontend (HTMX is sufficient for single-user personal tool)
- KIS live trading (Korean market; paper trading exists, live is a separate milestone)
- Multi-broker simultaneous execution
- Options/derivatives integration

### Architecture Approach

The v1.2 architecture adds one new bounded context (`scheduler`), one new presentation layer (`dashboard`), and significant modifications to two existing contexts (`execution` for live trading + approval workflow, `portfolio` for real-time monitoring). The existing `AsyncEventBus` — built in v1.0 but never used in production — becomes the backbone: the scheduler publishes `PipelineStartedEvent`/`StageCompletedEvent`/`PipelineCompletedEvent`, the execution context publishes `OrderExecutedEvent`/`OrderFailedEvent`, and the dashboard subscribes to all of them for SSE-based real-time updates.

**Major components:**
1. **`scheduler` bounded context (NEW)** — `PipelineOrchestratorService` chains existing DDD handlers (ingest -> regime -> score -> signal -> plan -> budget check -> auto-execute); `APSchedulerAdapter` triggers via cron with SQLite job persistence; `StrategyApproval` and `DailyBudget` value objects define approved execution parameters; pipeline run history persisted in SQLite.
2. **`execution` context (MODIFIED)** — `SafeExecutionService` wraps `IBrokerAdapter` with pre-execution safety checks (circuit breaker, budget enforcement, position limits); `BudgetEnforcementService` tracks daily capital deployment; `CircuitBreakerService` implements daily loss halt; `AlpacaOrderMonitor` polls order status in background; live mode gated by `EXECUTION_MODE` setting.
3. **`dashboard` presentation layer (NEW)** — FastAPI routes under `/dashboard/` serving Jinja2 templates; HTMX for partial page updates with zero build toolchain; SSE endpoint `/dashboard/stream` pushes all domain events from `AsyncEventBus` to browser; Plotly.py generates chart fragments embedded in templates.
4. **`AsyncEventBus` (ACTIVATED)** — existing shared infrastructure, now wired as the real-time backbone: scheduler publishes stage events, execution publishes order events, dashboard subscribes all for live push.

### Critical Pitfalls

1. **One-boolean live trading switch with no safety gate** — `AlpacaExecutionAdapter` currently hardcodes `paper=True`; making it configurable via credentials-present logic is catastrophic. Fix: add explicit `EXECUTION_MODE` enum setting (defaults to `paper`); `paper=False` requires BOTH valid live credentials AND `EXECUTION_MODE=live`; startup banner logs mode unambiguously. Phase: Live Trading (first task).

2. **Silent mock fallback masks real order failures** — `_real_bracket_order()` catches ALL exceptions and returns a mock `OrderResult(status="filled")`, creating phantom positions. In live mode, this means the system believes it holds stocks it never bought. Fix: separate `LiveAlpacaAdapter` that raises on any error in live mode; `OrderResult` must carry `is_mock: bool` flag; pipeline halts if mock result received in live mode. Phase: Live Trading (adapter refactor, before first live order).

3. **Automated pipeline running outside market hours** — no market calendar check exists anywhere in the codebase; orders submitted on holidays either reject or queue as GTC, filling at an unknown price. Fix: use `exchange_calendars` library; schedule by US/Eastern timezone; use `TimeInForce.DAY` for all automated orders; log every skip with reason. Phase: Automated Pipeline (scheduler setup, mandatory first task).

4. **No reconciliation between SQLite state and broker state** — system's portfolio records diverge from Alpaca reality through partial fills, stop-loss triggers, and manual interventions. Drawdown calculations use fictional data. Fix: `ReconciliationService` at pipeline start comparing `position_repo.find_all_open()` with `adapter.get_positions()`; `peak_value` synced from Alpaca at each pipeline run. Phase: Live Trading (post-order flow).

5. **Drawdown cooldown not persisted across restarts** — `cooldown_days_remaining` defaults to 0; the 30-day cooling period after a 20% drawdown is lost on any process restart. Fix: `CooldownState` table in SQLite with `start_date`/`end_date`/`trigger_drawdown_pct`; pipeline checks this at startup before allowing any execution. Phase: Live Trading (risk engine, hard prerequisite).

6. **Strategy approval with no expiration** — open-ended approvals allow stale strategies to execute in changed market conditions. Fix: `valid_until` field mandatory on all approvals; pipeline halts if no valid approval exists; `RegimeChangedEvent` triggers approval suspension. Phase: Strategy Approval (design first).

7. **SQLite concurrent access from dashboard + pipeline** — default journal mode blocks dashboard reads during pipeline writes, causing "database is locked" errors. Fix: enable WAL mode (`PRAGMA journal_mode=WAL`) on all SQLite connections; use read-only connections for dashboard; set `PRAGMA busy_timeout=5000`. Phase: Automated Pipeline (infrastructure setup).

## Implications for Roadmap

Based on research, the four v1.2 capabilities have clear implementation dependencies that dictate phase order. Safety infrastructure must precede live execution. The pipeline orchestrator must work correctly in paper mode before any live money is at risk. The approval workflow must be designed before the automated pipeline is enabled, because it defines what the pipeline is allowed to do.

### Phase 1: Safety Infrastructure and Live Trading Adapter

**Rationale:** The most dangerous pitfalls (silent mock fallback, one-boolean live switch, missing cooldown persistence, no reconciliation) all live in the execution and portfolio layers. These must be corrected before any automated pipeline is built on top, because the automated pipeline inherits whatever bugs exist in execution. Real money loss is irreversible — safety first.

**Delivers:** Production-safe execution adapter with explicit `EXECUTION_MODE` setting; separate paper/live adapter classes with no mock fallback in live mode; persistent `CooldownState` for drawdown defense; `ReconciliationService` that runs at pipeline startup; SQLite WAL mode enabled across all repositories; separate API key configuration for paper vs live; kill switch implementation.

**Features from FEATURES.md:** Live trading mode guard, separate API key pairs, kill switch, persistent cooldown, post-order status polling, bracket leg verification.

**Pitfalls addressed:** Pitfalls 1, 2, 4, 5 (one-boolean switch, silent fallback, no reconciliation, cooldown not persisted).

**Research flag:** Standard patterns. Well-documented Alpaca API. Existing code already reviewed at line level. No deeper research needed.

### Phase 2: Automated Pipeline Scheduler (Paper Mode)

**Rationale:** Build and validate the pipeline orchestrator in paper mode first. Requires Phase 1 (safe execution adapter) and existing handlers (already built). Market calendar guard is a mandatory first task within this phase. Pipeline must be idempotent and handle stage failures before any live money depends on it.

**Delivers:** `scheduler` bounded context with `PipelineOrchestratorService`; APScheduler integration with SQLite job persistence and `misfire_grace_time=3600`; market calendar check (skip weekends, NYSE holidays); pipeline run log in SQLite; stage-level retry with exponential backoff; regime-aware pipeline gating (Crisis + tier 2+ drawdown blocks plan creation); pipeline dry-run mode; concurrent scoring for universe of 400+ symbols.

**Uses from STACK.md:** APScheduler 3.11.2 with `AsyncIOScheduler` + `SQLAlchemyJobStore`; `exchange_calendars` for NYSE trading day awareness; existing DDD handlers wired as pipeline stages.

**Implements from ARCHITECTURE.md:** `PipelineOrchestratorService`, `APSchedulerAdapter`, `PipelineRun` entity, `ScheduleConfig` value object, `StageCompletedEvent` published to `AsyncEventBus`.

**Pitfalls addressed:** Pitfall 3 (market calendar), Pitfall 7 (SQLite WAL for concurrent dashboard access).

**Research flag:** Standard patterns. APScheduler is well-documented with official guides. Market calendar is a standard integration. No deeper research needed.

### Phase 3: Strategy and Budget Approval Workflow

**Rationale:** The approval workflow gates what the automated pipeline can do — it must be designed before automated execution is enabled, because the approval model determines the execution boundaries. Two-tier model: approve rules (strategy parameters) + approve capital (daily budget). Trades auto-execute within those approved constraints. Must exist before Phase 4 switches to live trading.

**Delivers:** `StrategyApproval` and `DailyBudget` value objects in `scheduler/domain/`; `BudgetEnforcementService` in `execution/domain/`; `ApproveStrategyCommand` and `SetBudgetCommand` with CLI entry points; approval expiration enforcement; regime-change approval suspension wired to existing `RegimeChangedEvent`; approval audit log in SQLite; budget spent-vs-remaining tracking per day; `TradePlanStatus.BUDGET_CHECK` and `AUTO_APPROVED` state extensions.

**Implements from ARCHITECTURE.md:** `StrategyApproval` lifecycle (DRAFT -> APPROVED -> EXPIRED/REVOKED/SUSPENDED), `DailyBudget` with daily reset at market open, budget enforcement before order submission.

**Pitfalls addressed:** Pitfall 6 (bad approval model — expiration, regime-gating, per-trade constraints all required).

**Research flag:** Standard patterns. State machine is straightforward. Main design decision is granularity (approve rules, not individual trades — confirmed correct approach).

### Phase 4: Live Trading Activation

**Rationale:** Only after Phase 1 (safe adapter), Phase 2 (validated automated pipeline in paper mode), and Phase 3 (approval workflow) is it safe to switch to `EXECUTION_MODE=live`. Progressive migration: paper automated first, then live with 25% capital allocation, increase as reliability is demonstrated.

**Delivers:** `EXECUTION_MODE=live` configuration in production; `SafeExecutionService` wrapping live adapter with circuit breaker + budget enforcement; live API key configuration and startup banner; `AlpacaOrderMonitor` background task for real-time order status tracking; `TradingStream` WebSocket subscription for fill events; gradual capital deployment ramp-up (start at 25% max deployment); circuit breaker pattern (3 consecutive failures halts live trading).

**Avoids:** All pitfalls that cause real money loss — Pitfalls 1, 2, 4, 5 resolved in Phase 1; Pitfall 6 resolved in Phase 3; live activation validates them all together.

**Research flag:** Needs careful validation. Start with 25% capital, monitor for 2-4 weeks before increasing. Watch for slippage divergence between paper and live fills. PDT rule check (accounts under $25K: max 3 day trades per 5 business days) must be verified before enabling live with smaller accounts.

### Phase 5: Web Dashboard

**Rationale:** The dashboard is the operational control panel for the automated system. It becomes essential once live trading is active — the operator needs visibility into pipeline status, portfolio state, and risk metrics without running CLI commands. Can be built incrementally but must be complete before leaving live trading unattended.

**Delivers:** FastAPI routes under `/dashboard/` with Jinja2 templates; HTMX 2.0.x for partial updates (no Node.js/React); SSE endpoint consuming `AsyncEventBus` for real-time updates; Plotly.py charts (equity curve, sector allocation, drawdown gauge); approval control panel (view/set strategy approval from browser); pipeline status widget (last run, next run, stage results, counts); portfolio overview with per-position P&L; prominent paper/live mode banner (red for live, green for paper); tiered alert notifications (INFO daily summary, CRITICAL for drawdown tier 2+).

**Uses from STACK.md:** HTMX 2.0.4 (CDN), htmx-ext-sse 2.2.2 (CDN), Plotly 6.5.x, FastAPI native SSE, Jinja2 (already installed), Starlette StaticFiles (already installed).

**Security tasks (from PITFALLS.md):** Restrict `allow_origins=["*"]` in `commercial/api/main.py` to dashboard origin; fail startup if JWT secret key matches dev default; dashboard auth if exposed on network (bind to localhost if personal-only).

**Research flag:** Standard patterns. HTMX + FastAPI is well-documented with multiple tutorials and benchmarks. Plotly.py financial chart documentation is comprehensive. Main risk is SSE event bus wiring under concurrent pipeline runs — verify no event loss.

### Phase Ordering Rationale

- Safety infrastructure before automation: real money loss is irreversible; executing on buggy code in production cannot be undone
- Paper automated before live: validates orchestration correctness, stage error handling, and reconciliation service without financial risk
- Approval workflow before live activation: the approval model defines execution boundaries; build the gate before opening it
- Dashboard after live activation: valuable for operational visibility but not a safety prerequisite; can be partially built alongside Phase 4

### Research Flags

Phases needing deeper research during planning:
- **Phase 4 (Live Trading Activation):** Progressive capital deployment strategy; paper-to-live slippage comparison methodology; PDT rule interaction with automated trading for accounts under $25K; specific Alpaca live account requirements and verification timeline (may have lead time).

Phases with standard patterns (skip research-phase):
- **Phase 1 (Safety Infrastructure):** Direct code fixes in known files; code references are specific (file, line number); patterns are clear from pitfalls research.
- **Phase 2 (Pipeline Scheduler):** APScheduler well-documented with official 3.x user guide; existing handlers already work; market calendar is a well-known integration.
- **Phase 3 (Approval Workflow):** State machine is simple; persistence patterns match existing SQLite repositories; approval model is design, not research.
- **Phase 5 (Dashboard):** HTMX + FastAPI pattern is well-documented; Plotly.py has comprehensive financial charting docs; SSE is native to installed FastAPI.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against PyPI and installed packages on 2026-03-13. Only 2 new packages (APScheduler, Plotly) both mature and production-proven. HTMX is CDN-only. No version conflicts. |
| Features | HIGH | Based on direct codebase analysis of existing 20K+ LOC system plus official Alpaca documentation. Existing capabilities clearly identified; v1.2 additions precisely scoped against what is already built. |
| Architecture | HIGH | Direct codebase analysis confirmed component boundaries, existing event bus, SQLite repository patterns, and Alpaca adapter structure. Architecture patterns are idiomatic extensions of the existing DDD structure. |
| Pitfalls | HIGH | All 7 critical pitfalls identified from direct line-level analysis of existing source files with specific file paths and line numbers. Alpaca behavior confirmed from official docs. Recovery costs assessed. |

**Overall confidence:** HIGH

### Gaps to Address

- **`exchange_calendars` vs `pandas_market_calendars`:** Both were mentioned in pitfalls research for NYSE trading day awareness. Confirm which to use during Phase 2 planning. Both cover NYSE; `exchange_calendars` is more widely cited in recent (2025-2026) literature, but check if either is already installed.
- **Dashboard authentication scope:** Research noted personal dashboard may not need auth if bound to localhost only. Confirm deployment plan (local-only vs. network-accessible, VPN-protected, etc.) before Phase 5 auth decisions. If any network exposure exists, JWT auth is mandatory.
- **Plotly.py chart generation performance:** Plotly generates standalone HTML/JS fragments. For large OHLCV datasets (400+ symbols, 2 years of daily data), verify DuckDB query time for chart data is acceptable before settling on chart update frequency. If slow, pre-generate charts at pipeline completion and cache.
- **`AsyncEventBus` under concurrent load:** The event bus was built in v1.0 but never used in production. Verify it handles concurrent publishers (pipeline scheduler + order monitor) and a subscriber (SSE stream) without event loss during high-activity pipeline runs. Add integration test before Phase 4.
- **Alpaca live account lead time:** Live Alpaca brokerage account requires identity verification and funding. If the account is not already open, verify the timeline (can be same-day, but varies). This may gate Phase 4 start.

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis of `/home/mqz/workspace/trading/` — all 7 pitfalls verified against specific files and line numbers: `src/execution/infrastructure/alpaca_adapter.py` (line 44 hardcoded `paper=True`, line 127 mock fallback), `personal/risk/drawdown.py` (`cooldown_days_remaining=0` default), `src/portfolio/domain/aggregates.py` (`peak_value` only updated on property access), `src/portfolio/infrastructure/sqlite_portfolio_repo.py` (no WAL mode), `commercial/api/main.py` (CORS wildcard line 27), `commercial/api/config.py` (JWT default key), `src/settings.py` (no `TRADING_MODE` setting)
- [APScheduler PyPI](https://pypi.org/project/APScheduler/) v3.11.2, Dec 2025, verified 2026-03-13
- [APScheduler 3.x User Guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) — AsyncIOScheduler, SQLAlchemyJobStore, CronTrigger, misfire_grace_time
- [FastAPI SSE Docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/) — native SSE in 0.135.0+, EventSourceResponse, ServerSentEvent
- [Alpaca-py PyPI](https://pypi.org/project/alpaca-py/) v0.43.2, Nov 2025, confirmed
- [Alpaca Trading SDK Docs](https://alpaca.markets/sdks/python/trading.html) — TradingClient paper param, TradingStream WebSocket
- [Alpaca WebSocket Streaming](https://alpaca.markets/docs/api-references/trading-api/streaming/) — trade_updates events, live/paper endpoints
- [Paper Trading - Alpaca Docs](https://docs.alpaca.markets/docs/paper-trading) — paper vs. live differences (fills, slippage, dividends)
- [Alpaca Common API Errors](https://alpaca.markets/learn/how-to-fix-common-trading-api-errors-at-alpaca) — rejection reasons, PDT rule
- [Plotly.py PyPI](https://pypi.org/project/plotly/) v6.5.2, Jan 2026, verified 2026-03-13
- [Systemic Failures in Algorithmic Trading (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8978471/) — academic source on pitfall patterns

### Secondary (MEDIUM confidence)
- [HTMX + FastAPI Patterns 2025](https://johal.in/htmx-fastapi-patterns-hypermedia-driven-single-page-applications-2025/) — SSR performance benchmarks (~45ms vs ~650ms for React hydration)
- [Realtime Dashboard: FastAPI, Streamlit, Next.js comparison](https://jaehyeon.me/blog/2025-03-04-realtime-dashboard-3/) — architecture comparison for dashboard technology choice
- [Human-in-the-Loop Architecture](https://www.agentpatterns.tech/en/architecture/human-in-the-loop-architecture) — two-tier approval model (approve rules, auto-execute within rules)
- [5 Common Algorithmic Trading Mistakes (Intrinio)](https://intrinio.com/blog/5-common-mistakes-to-avoid-when-using-automated-trading-systems) — domain pitfall validation
- [Weaponizing Real Time: WebSocket/SSE with FastAPI](https://blog.greeden.me/en/2025/10/28/weaponizing-real-time-websocket-sse-notifications-with-fastapi-connection-management-rooms-reconnection-scale-out-and-observability/) — SSE pattern for dashboard

---
*Research completed: 2026-03-13*
*Ready for roadmap: yes*
