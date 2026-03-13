# Roadmap: Intrinsic Alpha Trader

## Milestones

- ✅ **v1.0 MVP** -- Phases 1-4 (shipped 2026-03-12)
- ✅ **v1.1 Stabilization & Expansion** -- Phases 5-11 (shipped 2026-03-13)
- 🚧 **v1.2 Production Trading & Dashboard** -- Phases 12-16 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) -- SHIPPED 2026-03-12</summary>

- [x] Phase 1: Data Foundation (3/3 plans) -- completed 2026-03-12
- [x] Phase 2: Analysis Core (3/3 plans) -- completed 2026-03-12
- [x] Phase 3: Decision Engine (3/3 plans) -- completed 2026-03-12
- [x] Phase 4: Execution and Interface (3/3 plans) -- completed 2026-03-12

Full details: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

</details>

<details>
<summary>✅ v1.1 Stabilization & Expansion (Phases 5-11) -- SHIPPED 2026-03-13</summary>

- [x] Phase 5: Tech Debt & Infrastructure Foundation (3/3 plans) -- completed 2026-03-12
- [x] Phase 6: Live Data Pipeline & Korean Data (3/3 plans) -- completed 2026-03-12
- [x] Phase 7: Technical Scoring Engine (3/3 plans) -- completed 2026-03-12
- [x] Phase 8: Market Regime Detection (3/3 plans) -- completed 2026-03-12
- [x] Phase 9: Multi-Strategy Signal Fusion (2/2 plans) -- completed 2026-03-12
- [x] Phase 10: Korean Broker Integration (2/2 plans) -- completed 2026-03-12
- [x] Phase 11: Commercial FastAPI REST API (3/3 plans) -- completed 2026-03-13

Full details: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)

</details>

### v1.2 Production Trading & Dashboard (In Progress)

**Milestone Goal:** Automate the full pipeline, add live trading with safety infrastructure, and provide a web dashboard for operational visibility -- transforming the CLI tool into a production trading system.

- [x] **Phase 12: Safety Infrastructure** - Production-safe execution adapters, persistent drawdown defense, position reconciliation, kill switch (completed 2026-03-13)
- [x] **Phase 13: Automated Pipeline Scheduler** - Daily cron pipeline in paper mode with market calendar, stage retry, run logging (completed 2026-03-13)
- [x] **Phase 14: Strategy and Budget Approval** - Human-approved trading rules and daily budget caps gating automated execution (completed 2026-03-13)
- [x] **Phase 15: Live Trading Activation** - Live Alpaca execution with circuit breaker, order monitoring, and WebSocket fills (completed 2026-03-13)
- [ ] **Phase 16: Web Dashboard** - HTMX dashboard with portfolio, signals, risk metrics, pipeline status, and real-time SSE updates

## Phase Details

### Phase 12: Safety Infrastructure
**Goal**: Execution layer is production-safe -- explicit mode switching, no silent failures, persistent risk state, broker reconciliation
**Depends on**: Phase 11 (existing execution adapter and DDD handlers)
**Requirements**: SAFE-01, SAFE-02, SAFE-03, SAFE-04, SAFE-05, SAFE-06, SAFE-07, SAFE-08
**Success Criteria** (what must be TRUE):
  1. System starts in paper mode by default; switching to live requires explicit EXECUTION_MODE=live setting -- credentials alone cannot trigger live trading
  2. Order failures in live mode raise errors and halt execution -- the system never creates phantom fills or silent mock fallbacks
  3. Pipeline startup compares SQLite position records against Alpaca broker positions and reports any divergences before proceeding
  4. After a 20% drawdown triggers cooldown, restarting the process preserves the 30-day cooling period -- cooldown state survives restarts
  5. User can trigger kill switch from CLI that cancels all open orders and halts the pipeline immediately
**Plans**: 3 plans

Plans:
- [x] 12-01-PLAN.md -- Domain types, settings, and cooldown persistence (ExecutionMode, CooldownState, ICooldownRepository, SqliteCooldownRepository)
- [x] 12-02-PLAN.md -- SafeExecutionAdapter with order polling and bracket leg verification (fix mock fallback, decorator adapter, bootstrap wiring)
- [x] 12-03-PLAN.md -- Position reconciliation and kill switch CLI (PositionReconciliationService, trade kill, trade sync)

### Phase 13: Automated Pipeline Scheduler
**Goal**: Full screening-to-execution pipeline runs daily after market close in paper mode, with market calendar awareness and fault tolerance
**Depends on**: Phase 12 (safe execution adapter)
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06, PIPE-07
**Success Criteria** (what must be TRUE):
  1. After market close, the pipeline automatically runs ingest through execution without human intervention -- user sees completed run log next morning
  2. Pipeline skips weekends and NYSE holidays without submitting orders -- run log shows "skipped: holiday" entries
  3. If yfinance times out during data ingest, the failed stage retries automatically and the pipeline completes -- transient failures do not abort the full run
  4. When regime is Crisis or drawdown tier >= 2, the pipeline halts before plan creation and logs the reason -- no trades generated in dangerous conditions
  5. User can run the pipeline in dry-run mode that executes everything except order submission -- validating the full chain without risk
**Plans**: 3 plans

Plans:
- [x] 13-01-PLAN.md -- Pipeline domain model, infrastructure (PipelineRun entity, StageResult, SQLite run repo, MarketCalendarService, SlackNotifier)
- [x] 13-02-PLAN.md -- PipelineOrchestrator, APScheduler integration, CLI commands (orchestrator with retry/halt, SchedulerService, trade pipeline run/status)
- [x] 13-03-PLAN.md -- Gap closure: wire _run_plan/_run_execute stubs with real handler calls, instantiate SchedulerService in bootstrap, add daemon CLI command

### Phase 14: Strategy and Budget Approval
**Goal**: Human defines trading rules and daily capital limits once; automated pipeline executes within those boundaries until approval expires or conditions change
**Depends on**: Phase 13 (automated pipeline to gate)
**Requirements**: APPR-01, APPR-02, APPR-03, APPR-04, APPR-05
**Success Criteria** (what must be TRUE):
  1. User can create a strategy approval specifying score threshold, allowed regimes, max per-trade percentage, and expiration date -- pipeline only auto-executes trades matching these parameters
  2. User sets a daily budget cap and can see how much has been spent vs remaining for the current day's pipeline run
  3. Trades that exceed the approved budget or violate strategy parameters queue for manual review instead of auto-executing
  4. When market regime changes, active strategy approval is automatically suspended until user re-approves -- stale approvals cannot execute in changed conditions
**Plans**: 2 plans

Plans:
- [x] 14-01-PLAN.md -- Approval bounded context domain layer (StrategyApproval entity, ApprovalGateService, DailyBudgetTracker, SQLite persistence)
- [x] 14-02-PLAN.md -- Application handlers, pipeline gate integration, event-driven suspension, CLI commands (approve CRUD, trade review)

### Phase 15: Live Trading Activation
**Goal**: System executes real orders through Alpaca live account within approved safety boundaries, with real-time monitoring and automatic failure protection
**Depends on**: Phase 12 (safe adapter), Phase 13 (validated pipeline), Phase 14 (approval workflow)
**Requirements**: LIVE-01, LIVE-02, LIVE-03, LIVE-04, LIVE-05, LIVE-06
**Success Criteria** (what must be TRUE):
  1. With EXECUTION_MODE=live and valid live API credentials, the system connects to Alpaca live account and submits real orders -- paper and live use separate API key pairs
  2. SafeExecutionService enforces budget limits and position constraints before every order submission -- no order bypasses pre-checks
  3. Background order monitor tracks all open orders until they reach terminal state (filled, rejected, cancelled) -- no orders left in unknown status
  4. After 3 consecutive order failures, circuit breaker halts all live trading automatically -- requires manual reset to resume
  5. Initial live deployment uses max 25% capital allocation -- system enforces this ceiling regardless of strategy approval settings
**Plans**: 2 plans

Plans:
- [x] 15-01-PLAN.md -- Circuit breaker in SafeExecutionAdapter, OrderFilledEvent, LIVE_CAPITAL_RATIO, CLI config/reset commands
- [x] 15-02-PLAN.md -- AlpacaOrderMonitor background thread, TradingStreamAdapter WebSocket, pipeline integration with circuit breaker error handling

### Phase 16: Web Dashboard
**Goal**: Operator has full visibility into portfolio, pipeline, risk, and approval status through a browser-based dashboard with real-time updates
**Depends on**: Phase 12-15 (consumes data from all prior phases)
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, DASH-07, DASH-08, DASH-09
**Success Criteria** (what must be TRUE):
  1. User opens browser dashboard and sees current holdings, per-position P&L, and allocation breakdown -- no CLI needed for portfolio overview
  2. Dashboard displays latest scoring results, signal recommendations, and trade history with entry/stop/target/fill details
  3. Risk dashboard shows live drawdown gauge, sector exposure chart, and position limit utilization -- operator sees risk posture at a glance
  4. Dashboard shows pipeline status (last run, next scheduled, stage results) and allows viewing/managing strategy approval and daily budget
  5. When an order fills or pipeline completes, dashboard updates in real-time via SSE without page refresh -- and a prominent banner shows whether system is in paper (green) or live (red) mode
**Plans**: 4 plans

Plans:
- [x] 16-01-PLAN.md -- Dashboard foundation: FastAPI app, base template with sidebar + mode banner, SSE bridge, Plotly chart utilities, test scaffold
- [x] 16-02-PLAN.md -- Overview page: KPI cards, holdings table, equity curve chart with regime overlay, trade history table
- [x] 16-03-PLAN.md -- Signals page (scoring heatmap table, signal recommendations) + Risk page (drawdown gauge, sector donut, position limits, regime badge)
- [ ] 16-04-PLAN.md -- Pipeline & Approval page (run history, approval CRUD, budget bar, review queue) + SSE real-time wiring

## Progress

**Execution Order:**
Phases execute in numeric order: 12 -> 13 -> 14 -> 15 -> 16

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Data Foundation | v1.0 | 3/3 | Complete | 2026-03-12 |
| 2. Analysis Core | v1.0 | 3/3 | Complete | 2026-03-12 |
| 3. Decision Engine | v1.0 | 3/3 | Complete | 2026-03-12 |
| 4. Execution and Interface | v1.0 | 3/3 | Complete | 2026-03-12 |
| 5. Tech Debt & Infrastructure | v1.1 | 3/3 | Complete | 2026-03-12 |
| 6. Live Data Pipeline & Korean Data | v1.1 | 3/3 | Complete | 2026-03-12 |
| 7. Technical Scoring Engine | v1.1 | 3/3 | Complete | 2026-03-12 |
| 8. Market Regime Detection | v1.1 | 3/3 | Complete | 2026-03-12 |
| 9. Multi-Strategy Signal Fusion | v1.1 | 2/2 | Complete | 2026-03-12 |
| 10. Korean Broker Integration | v1.1 | 2/2 | Complete | 2026-03-12 |
| 11. Commercial FastAPI REST API | v1.1 | 3/3 | Complete | 2026-03-13 |
| 12. Safety Infrastructure | v1.2 | 3/3 | Complete | 2026-03-13 |
| 13. Automated Pipeline Scheduler | v1.2 | 3/3 | Complete | 2026-03-13 |
| 14. Strategy and Budget Approval | v1.2 | 2/2 | Complete | 2026-03-13 |
| 15. Live Trading Activation | v1.2 | 2/2 | Complete | 2026-03-13 |
| 16. Web Dashboard | 3/4 | In Progress|  | - |
