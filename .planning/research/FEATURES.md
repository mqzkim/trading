# Feature Research: v1.2 Production Trading & Dashboard

**Domain:** Automated trading pipeline, live execution, strategy/budget approval workflow, web dashboard
**Researched:** 2026-03-13
**Confidence:** HIGH (existing codebase verified + domain research + Alpaca docs)

**Scope:** This document covers ONLY new capabilities for v1.2. All v1.0 (fundamental scoring, valuation, basic signals, risk management, Alpaca paper trading, CLI dashboard) and v1.1 (technical scoring, regime detection, signal fusion, Korean market, commercial API) features are already built. v1.2 builds ON TOP of these, focusing on automation, live trading, approval workflows, and web visualization.

**Existing foundation this milestone depends on:**
- CLI-based scoring (fundamental + technical), regime detection, signal fusion
- Trade plan generation with entry/stop/target/size/reasoning
- Human approval workflow via CLI before order execution
- Alpaca paper trading with bracket orders (AlpacaExecutionAdapter, paper=True)
- FastAPI REST API (QuantScore, RegimeRadar, SignalFusion) with rate limiting and auth
- Risk management (Fractional Kelly 1/4, 3-tier drawdown defense at 10/15/20%)
- Monitoring alerts (stop hit, target reached, drawdown tier change)
- TradePlanHandler lifecycle: generate -> approve -> execute
- TradePlanStatus: PENDING -> APPROVED/MODIFIED/REJECTED -> EXECUTED/FAILED

---

## Capability 1: Automated Pipeline Scheduler

### What It Is

A persistent scheduler daemon that runs the full trading pipeline daily: screening -> scoring -> signal generation -> trade plan creation -> (optional) auto-execution. Currently, each step is triggered manually via CLI commands (`trading score AAPL`, `trading signal analyze AAPL`, etc.). The scheduler replaces this manual flow with an automated daily cycle that runs after market close, producing trade plans ready for review or auto-execution.

### Expected Behavior

**Standard automated trading pipeline stages (industry pattern):**

| Stage | Timing | Input | Output | Existing Code |
|-------|--------|-------|--------|---------------|
| Market data refresh | 16:30 ET (after close) | Ticker universe | Updated OHLCV + fundamentals | `data_ingest` context |
| Regime detection | 16:45 ET | VIX, S&P 500, yield curve | Current regime + confidence | `regime` context, `DetectRegimeCommand` |
| Scoring | 17:00 ET | All screened tickers | Composite scores (0-100) | `scoring` context, `ScoreSymbolCommand` |
| Signal generation | 17:30 ET | Scored symbols + regime | BUY/HOLD/SELL per symbol | `signals` context, `GenerateSignalCommand` |
| Trade plan creation | 17:45 ET | BUY signals + risk limits | Trade plans with entry/stop/target/size | `execution` context, `GenerateTradePlanCommand` |
| Execution (if auto-approved) | 18:00 ET or next open | Approved trade plans | Bracket orders submitted | `execution` context, `ExecuteOrderCommand` |

**Scheduler daemon requirements:**

| Requirement | Standard Pattern | Rationale |
|-------------|-----------------|-----------|
| Market-hours aware | Only run pipeline on trading days (skip weekends, US holidays) | Prevents wasted computation and stale data processing |
| Idempotent stages | Each stage can be re-run safely for same date | Recovery from partial failures without duplicate orders |
| Stage-level retry | Retry individual failed stages with exponential backoff | Data source timeouts should not abort entire pipeline |
| Pipeline state tracking | Record which stages completed for each run date | Audit trail and failure diagnosis |
| Configurable universe | Define which tickers to screen (S&P 500, custom watchlist, etc.) | Different users want different screening universes |
| Concurrent scoring | Score multiple symbols in parallel (thread/process pool) | 500 symbols sequentially takes hours; parallel takes minutes |

### Table Stakes

| Feature | Why Expected | Complexity | Dependency |
|---------|--------------|------------|------------|
| Cron-like daily schedule (after market close) | Every automated trading system runs on a schedule. Without this, user must manually trigger the full pipeline daily. | LOW | APScheduler or system cron |
| Market calendar awareness (skip weekends/holidays) | Running the pipeline on Saturday produces no new data. The `exchange_calendars` or `pandas_market_calendars` package provides NYSE/NASDAQ calendars. | LOW | Market calendar package |
| Full pipeline orchestration (screen -> score -> signal -> plan) | The entire value of automation: chaining existing commands without human intervention at each step. | MEDIUM | All existing bounded contexts wired together |
| Pipeline run log (which stages ran, pass/fail, duration) | Debugging pipeline failures requires knowing which stage failed and when. SQLite table with run_id, stage, status, started_at, completed_at. | LOW | SQLite (existing) |
| Configurable ticker universe (watchlist or index members) | User needs to define which stocks to screen. Currently hardcoded or passed as CLI args. Need a persistent configuration. | LOW | Config file or SQLite watchlist (existing `sqlite_watchlist_repo.py`) |
| Stage-level error handling with retry | yfinance rate limits, network timeouts, and API errors are common. A single failure should not abort the entire pipeline. Retry 3 times with backoff before marking stage as failed. | MEDIUM | Error handling wrapper |
| Pipeline health notification | After pipeline completes, user needs to know: how many symbols scored, how many signals generated, how many trade plans created, any errors. | LOW | Notification service (email, webhook, or CLI output to log file) |

### Differentiators

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| Regime-aware pipeline gating | If regime is Crisis and drawdown > 15%, skip trade plan creation entirely. Existing drawdown defense tiers already coded. Pipeline checks drawdown before generating plans. | LOW |
| Parallel scoring with progress tracking | Score 500 symbols across a thread pool. Show progress: "Scoring: 342/500 (68%)". CLI dashboard or log output. | MEDIUM |
| Pipeline dry-run mode | Run the full pipeline but stop before execution. Generate plans but do not submit orders. Useful for validation before enabling auto-execution. | LOW |
| Incremental scoring | Only re-score symbols whose data changed since last run. Skip unchanged symbols. Reduces pipeline runtime from 30min to 5min for daily runs. | MEDIUM |

### Anti-Features

| Feature | Why Problematic | Alternative |
|---------|-----------------|-------------|
| Celery/RabbitMQ distributed task queue | Massive infrastructure overhead for a single-user system. APScheduler or cron handles daily jobs perfectly. Celery is for multi-worker distributed processing. | APScheduler `BackgroundScheduler` running in the same process, or system cron triggering a CLI command. |
| Real-time continuous screening | Mid-term holding (2 weeks+) does not benefit from minute-level re-scoring. Adds data cost and API rate limit pressure. | Daily EOD pipeline is sufficient. Run once after market close. |
| Kubernetes-based pipeline orchestration (Airflow, Prefect, Dagster) | Single-developer personal system does not need distributed DAG orchestration. These tools add deployment complexity without proportional benefit. | Simple sequential stages with retry logic in a Python script. |
| Sub-minute scheduling granularity | Project constraint: no day trading. Daily granularity matches the swing/position holding period. | CronTrigger with daily schedule. |

---

## Capability 2: Alpaca Live Trading (Paper -> Live Migration)

### What It Is

Transition from paper trading (simulated, no real money) to live trading (real money, real orders). The existing `AlpacaExecutionAdapter` uses `paper=True`. Live trading changes this to `paper=False` with a different API key pair, adding safety mechanisms appropriate for real capital at risk.

### Expected Behavior

**Alpaca paper vs live -- what changes:**

| Aspect | Paper (Current) | Live (New) | Code Change |
|--------|----------------|------------|-------------|
| Base URL | `https://paper-api.alpaca.markets` | `https://api.alpaca.markets` | `paper=False` in TradingClient |
| API keys | Paper API key/secret | Live API key/secret (different pair) | Environment variable switch |
| Money | Simulated $100K | Real brokerage account balance | No code change |
| Order execution | Instant simulated fills | Real market fills with slippage/delays | Must handle async fills |
| Account approval | None needed | Requires Alpaca brokerage account (FINRA/SEC regulated) | One-time setup |
| Rate limits | Same (200 POST/min for orders) | Same | No code change |

**Required safety mechanisms for live trading (industry standard):**

| Safety Mechanism | Purpose | Implementation |
|-----------------|---------|----------------|
| Daily loss limit | Stop trading if daily losses exceed threshold (e.g., 2% of portfolio) | Check P&L before each order submission |
| Kill switch | Emergency stop that cancels all open orders and halts the pipeline | CLI command `trading kill-switch` + config flag |
| Order size cap | Maximum single order value (e.g., 8% of portfolio, already coded) | Validate against existing position limit before submission |
| Duplicate order prevention | Prevent re-ordering same symbol if position already exists | Check `get_positions()` before `submit_order()` |
| Order confirmation logging | Log every order with timestamp, price, quantity, status for audit | SQLite trade log with full order details |
| Gradual capital deployment | Start with small allocation (e.g., 25% of capital), increase over time | Configurable `max_deployment_pct` setting |
| Paper-first validation | Any new strategy must pass paper trading before live execution | Configuration flag: `live_trading_enabled: bool` |

**Order lifecycle monitoring (for real fills):**

| State | Meaning | Action |
|-------|---------|--------|
| new | Order accepted by broker | Log, wait for fill |
| partially_filled | Some shares filled, more pending | Track partial quantity, update position |
| filled | All shares filled | Update position, log filled price, verify bracket legs |
| cancelled | Order cancelled (by user or broker) | Log reason, alert user |
| expired | Order expired (time_in_force exceeded) | Log, decide whether to resubmit |
| rejected | Order rejected by broker | Log rejection reason, alert user, do NOT retry |
| replaced | Order was replaced | Update tracking with new order details |

### Table Stakes

| Feature | Why Expected | Complexity | Dependency |
|---------|--------------|------------|------------|
| Live account toggle (`paper=False`) | The entire point of this capability. Existing `AlpacaExecutionAdapter.__init__` already accepts `api_key`/`secret_key`; just need to add `paper` flag configuration. | LOW | Alpaca brokerage account + live API keys |
| Separate API key management (paper vs live) | Must never accidentally use live keys for testing or paper keys for real trading. Environment variable naming: `ALPACA_LIVE_API_KEY` vs `ALPACA_PAPER_API_KEY`. | LOW | Environment variable configuration |
| Daily loss limit with automatic halt | Real money at risk requires automatic safety gates. If intraday P&L drops below threshold (e.g., -2% of portfolio), halt all new orders for the day. | MEDIUM | Alpaca `get_account()` for current P&L + pipeline gating |
| Kill switch (cancel all orders + halt pipeline) | Emergency mechanism to stop all automated activity. SEC and FINRA increasingly expect automated systems to have manual overrides. | LOW | Alpaca `cancel_all_orders()` API + pipeline disable flag |
| Order execution logging with full audit trail | Every real-money order must be logged: symbol, direction, quantity, submitted_at, filled_at, filled_price, fees, status. Required for tax reporting and performance analysis. | MEDIUM | New SQLite table `execution_log` |
| Duplicate order prevention | Submitting a BUY for AAPL when already holding AAPL is usually a mistake. Check existing positions before order submission. | LOW | `get_positions()` check in execution handler |
| Partial fill handling | Real markets have partial fills. Must track filled_qty vs requested_qty and handle the remaining quantity (re-submit or cancel). | MEDIUM | Alpaca order status polling or WebSocket stream |
| Gradual capital deployment ramp-up | Starting live with 100% capital is reckless. Begin at 25% max deployment, increase monthly as system proves reliable. Configurable `max_deployment_pct`. | LOW | Configuration setting + position sizer integration |

### Differentiators

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| Automatic bracket leg verification | After fill, verify that stop-loss and take-profit legs are active. Alpaca bracket orders should auto-create legs, but verify they exist. | LOW |
| WebSocket order stream monitoring | Subscribe to Alpaca's trade updates WebSocket for real-time fill notifications instead of polling. Faster response to fills, cancellations, and rejections. | MEDIUM |
| Paper-live performance comparison | Run the same strategy on both paper and live simultaneously. Compare fills, slippage, and P&L to validate execution quality. | HIGH |
| Circuit breaker pattern | If 3 consecutive orders fail (rejected, error), automatically disable live trading and notify user. Prevents cascading failures. | LOW |

### Anti-Features

| Feature | Why Problematic | Alternative |
|---------|-----------------|-------------|
| Full auto-execution with no human oversight | PROJECT.md explicitly states: "Full auto-execution without any human oversight" is out of scope. Strategy/budget approval is still required. | Strategy/budget approval workflow (Capability 3) gates what the pipeline can do. |
| Margin trading / short selling | Adds leverage risk and complexity. Project constraint: capital preservation first. Margin amplifies losses. | Long-only equity positions. |
| Options/derivatives integration | Alpaca supports options, but project scope is stock-only. Options add Greeks, expiry, exercise complexity. | Defer to v2+ if ever. |
| Multi-broker live trading (Alpaca + KIS simultaneously) | Managing real money across two brokers with different APIs, currencies, and settlement rules is extremely error-prone. | Start with Alpaca live only. KIS live is a separate future milestone. |

---

## Capability 3: Strategy/Budget Approval Workflow

### What It Is

A human-in-the-loop approval system where the user approves a *strategy configuration and daily budget* rather than approving each individual trade. Once a strategy/budget is approved, the automated pipeline executes trades autonomously within those approved limits. This replaces the current per-trade CLI approval (`trading approve AAPL`) with a higher-level approval that enables hands-off operation.

### Expected Behavior

**Approval hierarchy (from most manual to most automated):**

| Level | Current (v1.0) | v1.2 Target | What Changes |
|-------|---------------|-------------|--------------|
| Per-trade approval | User approves each trade plan individually via CLI | Still available as fallback | No change, existing flow |
| Strategy approval | N/A | User approves strategy parameters (universe, regime, risk limits) | New: "I approve swing trading with max 5% per position in Bull/Sideways regimes" |
| Daily budget approval | N/A | User approves max capital deployment per day (e.g., $5,000/day) | New: "I approve up to $5,000 new positions today" |
| Full auto within approved limits | N/A | Pipeline auto-executes trades that fit within approved strategy + budget | New: trades within limits execute automatically; trades exceeding limits queue for manual approval |

**Strategy approval object (what gets approved):**

| Parameter | Description | Example | Constraint |
|-----------|-------------|---------|------------|
| `universe` | Which tickers to screen | "S&P 500" or custom watchlist | Must be a named watchlist |
| `allowed_regimes` | Which market regimes allow new positions | ["Bull", "Sideways"] | If current regime not in list, no new trades |
| `max_position_pct` | Maximum single position as % of portfolio | 5% | Must be <= 8% (hard limit from project constraints) |
| `max_daily_capital` | Maximum new capital deployed per day | $5,000 | Prevents over-deployment |
| `max_open_positions` | Maximum number of concurrent positions | 10 | Prevents over-diversification |
| `min_composite_score` | Minimum score threshold for trade plans | 70 | Below this, do not generate plans |
| `min_consensus_count` | Minimum methodology agreement for signals | 3 (out of 4) | Already coded as ConsensusThreshold |
| `valid_from` / `valid_until` | Approval window (dates) | 2026-03-13 to 2026-03-20 | Auto-expires, requires renewal |
| `approved_by` | Who approved (audit trail) | "mqz" | For logging |
| `approved_at` | When approved (timestamp) | 2026-03-13T08:00Z | For logging |

**Approval workflow states:**

```
[No Approval] -> [Strategy Proposed] -> [Strategy Approved] -> [Active]
                                    \-> [Strategy Rejected]
[Active] -> [Expired] (valid_until passed)
[Active] -> [Revoked] (user manually revokes)
[Active] -> [Suspended] (kill switch triggered)
```

**Trade execution decision matrix:**

| Condition | Action |
|-----------|--------|
| No active approval exists | Queue trade plan for per-trade manual approval (existing flow) |
| Trade fits within all approved limits | Auto-execute |
| Trade exceeds daily budget | Queue for manual approval + alert |
| Trade exceeds position limit | Reject automatically + alert |
| Regime not in allowed list | Skip trade plan creation entirely |
| Drawdown tier 1 (10%) | Tighten limits: reduce max_daily_capital by 50% |
| Drawdown tier 2 (15%) | Suspend auto-execution, require manual approval for all |
| Drawdown tier 3 (20%) | Full halt, no new positions (existing drawdown defense) |

### Table Stakes

| Feature | Why Expected | Complexity | Dependency |
|---------|--------------|------------|------------|
| Strategy approval object (persisted configuration) | The core of the workflow: a structured, validated set of trading parameters that the pipeline checks before each execution. | MEDIUM | New domain entity in `execution` context |
| Approval CLI commands (`trading approve-strategy`, `trading revoke-strategy`) | User must be able to set and revoke approvals from the terminal. Matches existing CLI workflow. | LOW | Typer commands + strategy approval repo |
| Approval expiration (time-bounded) | Open-ended approvals are dangerous. Force periodic re-approval (weekly or custom window). | LOW | `valid_until` field with automatic expiration check |
| Budget tracking (spent vs remaining today) | If daily budget is $5,000 and $3,200 has been deployed, show "$1,800 remaining". Pipeline checks before each order. | MEDIUM | Daily capital tracking in SQLite |
| Drawdown-integrated approval suspension | When drawdown hits tier 2 (15%), auto-suspend the strategy approval. User must manually re-approve after acknowledging the drawdown. | LOW | Integration with existing `assess_drawdown()` |
| Approval audit log | Every approval, revocation, suspension, and expiration must be logged with timestamp and reason. | LOW | SQLite audit table |
| Per-trade fallback for unapproved trades | If a trade exceeds approved limits, queue it for manual per-trade approval rather than silently dropping it. | LOW | Existing `TradePlanStatus.PENDING` flow |

### Differentiators

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| Regime-conditional approval | "Auto-execute in Bull and Sideways. Manual approval required in Bear. Full halt in Crisis." Existing regime detection integrates directly. | LOW |
| Approval dashboard summary | Show active approval parameters, remaining budget, trades executed today, regime compatibility in one view. | LOW |
| Multi-period budget tracking | Track daily, weekly, and monthly deployment limits. "$5K/day, $15K/week, $30K/month" prevents over-deployment even within daily limits. | MEDIUM |
| Approval notification digest | Daily summary email/notification: "Pipeline executed 3 trades ($4,200 deployed). 2 trades queued for manual review. $800 daily budget remaining." | MEDIUM |

### Anti-Features

| Feature | Why Problematic | Alternative |
|---------|-----------------|-------------|
| Fully automatic execution with no approval at all | Violates project constraint: "human-in-the-loop: requires explicit human approval before any order." Strategy/budget approval IS the human approval -- but removing it entirely is not acceptable. | Strategy/budget approval provides the human oversight layer while enabling automation within approved bounds. |
| Complex multi-user approval chains (maker/checker) | Single-user personal system. Multi-approver workflow adds complexity without value. | Single-user approval with audit log. |
| Dynamic budget adjustment based on P&L | "If up 5% today, increase budget" creates positive feedback loops that amplify losses after reversals. | Fixed daily budget that only decreases (via drawdown tiers), never increases automatically. |
| Approval via email/mobile notification | Adds notification infrastructure (SMTP, push service). For personal use, CLI is sufficient. Web dashboard approval can be added later. | CLI approval. Web dashboard approval as a v1.2 stretch goal. |

---

## Capability 4: Web Dashboard

### What It Is

A web-based visual interface that replaces or complements the existing Rich CLI dashboard. Shows portfolio overview, P&L tracking, scoring/signal results, trade history, and risk metrics in a browser. Built with Streamlit (personal dashboard) or extending the existing FastAPI server with HTML templates (if integrating with commercial API).

### Expected Behavior

**Standard trading dashboard views (industry pattern):**

| View | What It Shows | Update Frequency | Audience |
|------|---------------|------------------|----------|
| Portfolio Overview | Holdings, current value, cash, total P&L | On page load + manual refresh | Primary view |
| Position Detail | Per-position entry, current, P&L, stop/target, days held | On page load | Drill-down from portfolio |
| P&L Chart | Equity curve over time, daily/weekly/monthly returns | Daily (EOD) | Performance tracking |
| Score Dashboard | Top-scored symbols, composite score breakdown, safety filter results | After pipeline run | Signal review |
| Signal Dashboard | Per-symbol methodology results, consensus, reasoning traces | After pipeline run | Trade decision support |
| Risk Dashboard | Drawdown level, sector exposure, position concentration, daily loss | Real-time (from broker) | Risk monitoring |
| Trade History | All executed trades, fill prices, fees, realized P&L | On page load | Audit and analysis |
| Pipeline Status | Last run status, stage completion, errors, next scheduled run | After pipeline run | Operations monitoring |
| Regime Panel | Current regime, confidence, indicators, regime history chart | Daily | Market context |
| Approval Status | Active strategy approval, budget remaining, trades auto-executed today | Real-time | Control panel |

**Dashboard technology choice rationale:**

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Streamlit | All Python, fastest to build, rich chart support via Plotly, no frontend code needed, auto-refresh via `st.experimental_rerun` | Re-runs entire script on interaction, limited layout control, separate process from FastAPI | Use for personal dashboard |
| FastAPI + Jinja2 + HTMX | Integrates with existing FastAPI API, server-rendered, sub-50ms updates | More frontend code, less chart support out of the box, need to learn HTMX | Consider for commercial dashboard later |
| React/Next.js + FastAPI API | Most flexible UI, best for complex interactions | Separate frontend codebase, requires Node.js/npm, overkill for personal use | Defer to v2+ |

**Recommendation: Streamlit for v1.2 personal dashboard.** Rationale: (1) all Python, no new language; (2) Plotly charts built-in; (3) fastest to build for a single developer; (4) can call existing scoring/signal/portfolio code directly; (5) existing FastAPI commercial API remains independent for external consumers.

### Table Stakes

| Feature | Why Expected | Complexity | Dependency |
|---------|--------------|------------|------------|
| Portfolio overview (holdings, cash, total value, P&L) | The most basic view. Every trading platform shows this first. Data comes from `AlpacaExecutionAdapter.get_positions()` + `get_account()`. | LOW | Alpaca adapter (existing) |
| Per-position detail (entry, current, unrealized P&L, stop/target) | User needs to see individual position health. Existing `TradePlan` has entry/stop/target; Alpaca has current price/unrealized P&L. | LOW | Alpaca positions + trade plan repo (existing) |
| Equity curve chart (portfolio value over time) | Standard performance visualization. Plot daily portfolio values. Requires daily portfolio value snapshots stored in SQLite. | MEDIUM | New: daily portfolio snapshot persistence |
| Composite score table (top N scored symbols) | Shows pipeline output. Table of symbols with composite score, sub-scores, safety filter status. Already computed by scoring pipeline. | LOW | Scoring repo (existing) |
| Signal results table (per-symbol methodology results + consensus) | Shows which signals the pipeline generated. Table with symbol, direction, consensus count, per-methodology breakdown. | LOW | Signal repo (existing) |
| Drawdown indicator (current level, tier, visual gauge) | Risk is the primary concern. Show current drawdown %, which tier (normal/caution/danger/halt), visual progress bar. | LOW | Existing `assess_drawdown()` |
| Sector exposure chart (pie or bar chart) | Show portfolio allocation across sectors. Detect over-concentration. Existing sector limits (25% max). | LOW | Alpaca positions + sector data |
| Trade history log (executed trades with timestamps, prices, P&L) | Audit trail and performance review. Table of all executed trades sorted by date. | LOW | Execution log repo (new in Capability 2) |
| Pipeline status panel (last run, next run, stage results) | Operations monitoring. Show when the pipeline last ran, whether it succeeded, what it produced. | LOW | Pipeline run log (new in Capability 1) |

### Differentiators

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| Regime context overlay on all views | Show current regime (Bull/Bear/Sideways/Crisis) with color coding on every dashboard page. Changes interpretation of all metrics. | LOW |
| Strategy approval control panel | View/set/revoke strategy approvals directly from the dashboard. Show active approval parameters and remaining budget. | MEDIUM |
| Score evolution chart (per-symbol over time) | How has AAPL's composite score changed over the past 90 days? Trend in quality vs just point-in-time snapshot. | MEDIUM |
| One-click trade plan approval from dashboard | Instead of CLI `trading approve AAPL`, click "Approve" button next to pending trade plan in the dashboard. | MEDIUM |
| Risk dashboard with real-time drawdown tracking | Live drawdown gauge that updates as market moves. Red/yellow/green zones matching the 10/15/20% tiers. | MEDIUM |

### Anti-Features

| Feature | Why Problematic | Alternative |
|---------|-----------------|-------------|
| Real-time WebSocket price streaming on dashboard | Mid-term holding does not benefit from tick-by-tick prices. Adds data subscription cost and WebSocket complexity. Streamlit's rerun model is not designed for WebSocket push. | Manual refresh or auto-refresh every 60 seconds. Daily EOD snapshots for charts. |
| Mobile-responsive design as v1.2 priority | Streamlit's layout is somewhat responsive by default, but optimizing for mobile is scope creep. Personal dashboard is used at a desk. | Desktop-first. Mobile optimization is v2+. |
| Complex interactive charting (drawing tools, annotations) | TradingView-like charting is a product in itself. Way beyond scope. | Plotly static/interactive charts with zoom/pan. No drawing tools. |
| Multi-user dashboard with login | Personal system. Single user. Adding auth to the personal dashboard adds complexity without value. The commercial API already has auth. | No login for personal Streamlit dashboard. Bind to localhost only. |
| Dark mode / theme customization | Cosmetic feature that does not affect trading decisions. Streamlit has built-in theme support if needed later. | Default Streamlit theme. |

---

## Capability 5: Real-Time Order Monitoring and Error Recovery

### What It Is

Active monitoring of submitted orders and open positions. The existing system submits bracket orders and logs the result, but does not monitor what happens after submission. Real orders can be partially filled, cancelled by the broker, have legs expire, or fail silently. This capability adds the monitoring and recovery logic needed for live trading reliability.

### Expected Behavior

**Order monitoring lifecycle:**

| Event | Detection Method | Response |
|-------|-----------------|----------|
| Order filled | Alpaca `get_order(order_id)` status check or WebSocket | Log fill price, update position, verify bracket legs active |
| Partial fill | Order status = `partially_filled` | Track filled_qty, decide: wait for remainder or cancel unfilled portion |
| Order rejected | Order status = `rejected` | Log rejection reason, alert user, do NOT retry (usually compliance issue) |
| Order cancelled | Order status = `cancelled` | Log cancellation, check if bracket legs also cancelled |
| Order expired | Order status = `expired` (time_in_force exceeded) | Log, evaluate if market conditions still favor the trade, optionally resubmit |
| Stop-loss triggered | Stop leg filled (from bracket) | Log exit, calculate realized P&L, update portfolio |
| Take-profit triggered | Limit leg filled (from bracket) | Log exit, calculate realized P&L, update portfolio |
| Bracket leg missing | Parent filled but stop/limit leg not found | CRITICAL: manually place missing leg immediately or alert user |
| API error on submission | HTTP 4xx/5xx from Alpaca | Retry with exponential backoff (max 3 attempts). If persistent, alert user. |
| Connection timeout | No response from Alpaca | Retry once. If still no response, log as failed and alert. Do NOT resubmit blindly (might be a double-order). |

### Table Stakes

| Feature | Why Expected | Complexity | Dependency |
|---------|--------------|------------|------------|
| Post-submission order status verification | After submitting an order, poll for fill status. Must confirm the order was actually accepted and processed. | LOW | Alpaca `get_order()` API |
| Bracket leg verification | After main order fills, verify stop-loss and take-profit legs are active. Bracket orders should auto-create legs, but verify. | LOW | Alpaca `get_order()` with `legs` field |
| Failed order alerting | If an order fails (rejected, expired, API error), the user must be notified immediately. Log + CLI output + optional webhook. | LOW | Logging + notification |
| Retry logic with exponential backoff | Transient API errors (rate limits, timeouts) should retry automatically. Max 3 retries with 2/4/8 second delays. | LOW | Retry wrapper utility |
| Order execution audit log | Every order state change (submitted -> filled, submitted -> rejected) logged with timestamp. Required for live trading accountability. | MEDIUM | SQLite `order_events` table |
| Position reconciliation | Periodically verify that local position records match Alpaca's actual positions. Detect discrepancies (ghost positions, missing fills). | MEDIUM | Compare local DB with `get_positions()` |

### Differentiators

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| Alpaca WebSocket streaming for order updates | Instead of polling, subscribe to Alpaca's trade_updates WebSocket stream. Instant notification of fills, cancellations, and rejections. | MEDIUM |
| Automatic stop-loss recovery | If a stop-loss leg is cancelled (broker system issue), automatically re-create it. Never leave a position without a stop-loss. | MEDIUM |
| Execution quality analysis | Compare expected fill price (entry_price from trade plan) with actual fill price. Track slippage over time. | LOW |
| Daily reconciliation report | End-of-day report: all orders submitted, fills received, positions opened/closed, any discrepancies. | LOW |

### Anti-Features

| Feature | Why Problematic | Alternative |
|---------|-----------------|-------------|
| Sub-second order monitoring | Polling every 100ms wastes API rate limits and adds no value for daily/swing trading. | Poll every 30 seconds, or use WebSocket streaming. |
| Automatic retry of rejected orders | Rejected orders are usually rejected for a reason (insufficient funds, compliance, halted stock). Auto-retrying a rejected order is dangerous. | Log and alert. User decides whether to resubmit. |
| Complex order types (OCO, trailing stop, TWAP) | Bracket orders (entry + stop + take-profit) cover the project's needs. Adding OCO, trailing stops, or algorithmic execution types adds complexity without matching the mid-term holding strategy. | Bracket orders only. |

---

## Cross-Capability Feature Dependencies

```
[Automated Pipeline Scheduler]
    |
    +--requires--> [Market Calendar] (NYSE trading days awareness)
    +--orchestrates--> [data_ingest] -> [regime] -> [scoring] -> [signals] -> [execution]
    +--checks--> [Strategy Approval] (before generating trade plans)
    +--checks--> [Drawdown Defense] (existing, gates plan creation)
    +--produces--> [Pipeline Run Log] (consumed by Dashboard)
    |
[Alpaca Live Trading]
    |
    +--requires--> [Live API Keys] (separate from paper keys)
    +--requires--> [Kill Switch] (emergency halt mechanism)
    +--requires--> [Order Monitoring] (verify fills, detect failures)
    +--requires--> [Execution Audit Log] (every order logged)
    +--enhances--> [AlpacaExecutionAdapter] (existing, add paper=False path)
    +--feeds--> [Dashboard] (real-time position data)
    |
[Strategy/Budget Approval]
    |
    +--requires--> [Strategy Approval Entity] (new domain object)
    +--requires--> [Approval Repository] (SQLite persistence)
    +--requires--> [Budget Tracker] (daily capital deployment tracking)
    +--integrates--> [Regime Detection] (regime-conditional auto-execution)
    +--integrates--> [Drawdown Defense] (auto-suspend on tier 2)
    +--gates--> [Automated Pipeline] (execution decision matrix)
    |
[Order Monitoring & Error Recovery]
    |
    +--requires--> [Alpaca API] (order status, position sync)
    +--requires--> [Execution Audit Log] (shared with Live Trading)
    +--enables--> [Live Trading] (cannot do live without monitoring)
    +--feeds--> [Dashboard] (order status, fill notifications)
    |
[Web Dashboard]
    |
    +--consumes--> [Alpaca Positions/Account] (portfolio view)
    +--consumes--> [Scoring Repo] (score table)
    +--consumes--> [Signal Repo] (signal table)
    +--consumes--> [Pipeline Run Log] (pipeline status)
    +--consumes--> [Strategy Approval] (approval control panel)
    +--consumes--> [Execution Audit Log] (trade history)
    +--consumes--> [Regime Detection] (regime overlay)
    +--consumes--> [Drawdown Assessment] (risk dashboard)
    +--independent-of--> [Commercial API] (separate concern, different audience)
```

### Critical Dependency Notes

1. **Order Monitoring must come before Live Trading.** You cannot trade real money without monitoring fills and handling errors. Order monitoring is a prerequisite, not an add-on.

2. **Strategy/Budget Approval must come before Automated Pipeline auto-execution.** The pipeline can run without approval (dry-run mode), but auto-execution requires the approval workflow to be in place. Build approval first, then enable auto-execution.

3. **Automated Pipeline can run in dry-run mode early.** Even without live trading or approval workflow, the pipeline can run daily and produce trade plans for review. This validates the orchestration before adding real execution.

4. **Dashboard is a consumer of all other capabilities.** It does not produce data, only displays it. Can be built incrementally: start with portfolio view (needs only Alpaca adapter), add pipeline status, then scoring/signals, then approval control.

5. **Kill switch is a cross-cutting concern.** It must be able to: (a) cancel all open orders via Alpaca, (b) disable the pipeline scheduler, (c) suspend all strategy approvals, (d) show halt status on dashboard. Build it early in the live trading phase.

6. **Execution audit log is shared infrastructure.** Both live trading and order monitoring write to it. Dashboard reads from it. Design the schema before implementing either capability.

---

## MVP Definition for v1.2

### Phase 1: Pipeline Automation (Foundation)

Build first because it orchestrates all existing code into a repeatable daily cycle:

- [ ] **Pipeline orchestrator** -- sequential execution of screen -> score -> signal -> plan stages
- [ ] **APScheduler integration** -- daily cron trigger after market close (16:30 ET)
- [ ] **Market calendar awareness** -- skip weekends and US holidays
- [ ] **Pipeline run logging** -- SQLite table tracking stage completions and errors
- [ ] **Stage-level retry** -- 3 retries with exponential backoff per stage
- [ ] **Dry-run mode** -- generate trade plans without submitting orders
- [ ] **CLI commands** -- `trading pipeline run`, `trading pipeline status`, `trading pipeline schedule`

### Phase 2: Live Trading Safety Infrastructure

Build second because it establishes all safety mechanisms before real money is at risk:

- [ ] **Live account configuration** -- environment-based paper/live toggle
- [ ] **Kill switch** -- `trading kill-switch` command that cancels all orders and halts pipeline
- [ ] **Order monitoring** -- post-submission status verification and bracket leg checks
- [ ] **Execution audit log** -- SQLite table for every order state change
- [ ] **Daily loss limit** -- configurable threshold that halts new orders
- [ ] **Duplicate order prevention** -- position check before submission
- [ ] **Retry with backoff** -- transient API error handling
- [ ] **Position reconciliation** -- compare local records with broker state

### Phase 3: Strategy/Budget Approval Workflow

Build third because it bridges safety infrastructure with automated execution:

- [ ] **Strategy approval entity** -- domain object with universe, limits, regime conditions, expiry
- [ ] **Approval persistence** -- SQLite repository for approvals with status tracking
- [ ] **Budget tracker** -- daily capital deployment tracking (spent vs remaining)
- [ ] **Execution decision matrix** -- auto-execute vs queue-for-approval logic
- [ ] **Drawdown integration** -- auto-suspend approval on tier 2 (15%)
- [ ] **CLI commands** -- `trading approve-strategy`, `trading revoke-strategy`, `trading approval-status`
- [ ] **Approval audit log** -- every approval/revocation/suspension logged

### Phase 4: Web Dashboard

Build last because it is a consumer of all other capabilities:

- [ ] **Streamlit application** with multi-page navigation
- [ ] **Portfolio overview** -- holdings, cash, total P&L from Alpaca
- [ ] **Equity curve chart** -- daily portfolio value over time (requires snapshot persistence)
- [ ] **Score table** -- top-scored symbols with composite breakdown
- [ ] **Signal table** -- per-symbol methodology results and consensus
- [ ] **Risk dashboard** -- drawdown gauge, sector exposure chart, position limits
- [ ] **Trade history** -- executed trades from audit log
- [ ] **Pipeline status** -- last run, stage results, next scheduled run
- [ ] **Approval status** -- active approval parameters, remaining budget

### Defer to v1.3+

- [ ] WebSocket order streaming (replace polling with Alpaca trade_updates stream)
- [ ] Email/notification digest for pipeline results and approval requests
- [ ] One-click trade approval from web dashboard
- [ ] Paper-live parallel comparison
- [ ] Multi-period budget tracking (daily + weekly + monthly)
- [ ] Mobile-responsive dashboard design
- [ ] Dashboard for commercial API monitoring (separate from personal dashboard)

---

## Feature Prioritization Matrix

| Feature | User Value | Impl Cost | Risk Reduction | Priority |
|---------|------------|-----------|----------------|----------|
| Pipeline orchestrator (screen->score->signal->plan) | HIGH | MEDIUM | HIGH (eliminates manual step errors) | P1 |
| APScheduler daily trigger | HIGH | LOW | MEDIUM (ensures daily execution) | P1 |
| Market calendar awareness | MEDIUM | LOW | MEDIUM (prevents wasted runs) | P1 |
| Pipeline run logging | MEDIUM | LOW | HIGH (debugging and audit) | P1 |
| Kill switch (cancel all + halt) | HIGH | LOW | CRITICAL (safety mechanism) | P1 |
| Order monitoring (post-submission verify) | HIGH | MEDIUM | CRITICAL (must know fill status) | P1 |
| Execution audit log | HIGH | LOW | CRITICAL (accountability for real $) | P1 |
| Daily loss limit | HIGH | LOW | CRITICAL (capital protection) | P1 |
| Live account toggle (paper=False) | HIGH | LOW | N/A (the goal) | P1 |
| Strategy approval entity + persistence | HIGH | MEDIUM | HIGH (human oversight layer) | P1 |
| Budget tracker (daily deployment) | HIGH | LOW | HIGH (prevents over-deployment) | P1 |
| Execution decision matrix | HIGH | MEDIUM | HIGH (auto vs manual gate) | P1 |
| Drawdown-integrated approval suspension | HIGH | LOW | HIGH (automatic safety) | P1 |
| Portfolio overview dashboard | HIGH | LOW | LOW | P2 |
| Equity curve chart | MEDIUM | MEDIUM | LOW | P2 |
| Score/signal tables on dashboard | MEDIUM | LOW | LOW | P2 |
| Risk dashboard (drawdown, sectors) | MEDIUM | LOW | MEDIUM (visual risk awareness) | P2 |
| Trade history view | MEDIUM | LOW | LOW (audit visibility) | P2 |
| Pipeline status panel | MEDIUM | LOW | LOW (operational visibility) | P2 |
| Partial fill handling | MEDIUM | MEDIUM | MEDIUM | P2 |
| Position reconciliation | MEDIUM | MEDIUM | HIGH (detect discrepancies) | P2 |
| Regime overlay on dashboard | LOW | LOW | LOW | P3 |
| Approval control panel on dashboard | LOW | MEDIUM | MEDIUM | P3 |
| Score evolution chart | LOW | MEDIUM | LOW | P3 |
| WebSocket order streaming | LOW | MEDIUM | MEDIUM | P3 |
| Notification digest | LOW | MEDIUM | LOW | P3 |

**Priority key:**
- **P1**: Must have for v1.2 -- core automation, safety, and approval infrastructure
- **P2**: Should have -- dashboard views and enhanced monitoring
- **P3**: Nice to have -- polish features for later iterations

---

## Competitor Feature Analysis (v1.2 Capabilities)

| Feature | QuantConnect | Alpaca Dashboard | TradingView | Zipline/Backtrader | **Ours (v1.2)** |
|---------|-------------|-----------------|-------------|--------------------|--------------------|
| Automated daily pipeline | User-coded in LEAN | No (API only) | No (charting only) | Backtest only, no live | **Built-in: screen->score->signal->execute** |
| Paper->live toggle | Via LEAN deployment | API parameter `paper=True/False` | No execution | Zipline: no live | **`paper=False` + safety gates** |
| Strategy/budget approval | No (full auto or full manual) | No (manual or webhook) | No | No | **Approval workflow with budget tracking** |
| Kill switch | No | Manual cancel all | No | No | **CLI + dashboard + auto-trigger** |
| Daily loss limit | No (user-coded) | No | No | No | **Built-in configurable limit** |
| Order monitoring | User-coded | Basic dashboard | No | No | **Automatic status verification + recovery** |
| Web dashboard | LEAN desktop | Alpaca web portal | TradingView charts | No | **Streamlit with regime context** |
| Regime-conditional automation | No | No | No | No | **Auto-execute in Bull, manual in Bear** |
| Execution audit trail | Logs in LEAN | Order history page | No | No | **Full SQLite audit log** |

### Key Differentiator

The strategy/budget approval workflow with regime-conditional auto-execution is genuinely novel. No existing platform offers a middle ground between "fully manual" and "fully automatic" that adapts to market regime. This is the UX innovation of v1.2.

---

## Sources

### Automated Pipeline / Scheduling
- [APScheduler Documentation](https://apscheduler.readthedocs.io/en/stable/) -- cron, interval, and date triggers (HIGH confidence)
- [APScheduler vs Celery Beat comparison](https://leapcell.io/blog/scheduling-tasks-in-python-apscheduler-vs-celery-beat) -- APScheduler for in-process scheduling, Celery for distributed (MEDIUM confidence)
- [Job Scheduling in Python with APScheduler](https://betterstack.com/community/guides/scaling-python/apscheduler-scheduled-tasks/) -- BackgroundScheduler patterns (MEDIUM confidence)

### Alpaca Live Trading
- [Alpaca Paper Trading Docs](https://docs.alpaca.markets/docs/paper-trading) -- paper=True/False toggle, same API spec (HIGH confidence)
- [Alpaca Trading API Docs](https://docs.alpaca.markets/docs/trading-api) -- endpoints, order types, account management (HIGH confidence)
- [Paper vs Live Trading Guide](https://alpaca.markets/learn/paper-trading-vs-live-trading-a-data-backed-guide-on-when-to-start-trading-real-money) -- transition best practices (MEDIUM confidence)
- [Alpaca-py TradingClient](https://alpaca.markets/sdks/python/api_reference/trading/trading-client.html) -- SDK reference (HIGH confidence)

### Trading Safety
- [Trading System Kill Switch (NYIF)](https://www.nyif.com/articles/trading-system-kill-switch-panacea-or-pandoras-box) -- kill switch design patterns (MEDIUM confidence)
- [Circuit Breaker Pattern in Trading](https://www.ai-futureschool.com/en/programming/understanding-the-pattern-circuit-breaker.php) -- automated halt mechanisms (MEDIUM confidence)
- [Complete Broker API Trading Guide (TradersPost)](https://blog.traderspost.io/article/broker-api-trading-guide) -- order monitoring, partial fills, error recovery (MEDIUM confidence)

### Approval Workflows
- [Trade Approval Automation (Everysk)](https://everysk.com/use-cases/trade-approval-automation-workflow/) -- institutional approval patterns, 85% reduction in approval timeline (MEDIUM confidence)
- [Human-in-the-Loop Architecture](https://www.agentpatterns.tech/en/architecture/human-in-the-loop-architecture) -- approval patterns for automated systems (MEDIUM confidence)

### Web Dashboard
- [Streamlit vs Plotly Dash Comparison 2025](https://dasroot.net/posts/2025/12/building-python-dashboards-streamlit-vs/) -- framework comparison (MEDIUM confidence)
- [Algo Trading Dashboard with Streamlit](https://jaydeep4mgcet.medium.com/algo-trading-dashboard-using-python-and-streamlit-live-index-prices-current-positions-and-payoff-f44173a5b6d7) -- trading-specific Streamlit patterns (MEDIUM confidence)
- [FastAPI + Jinja2 + HTMX Dashboard](https://www.johal.in/fastapi-templating-jinja2-server-rendered-ml-dashboards-with-htmx-2025-3/) -- alternative approach for FastAPI integration (MEDIUM confidence)
- [FastAPI WebSocket Real-Time Dashboard](https://testdriven.io/blog/fastapi-postgres-websockets/) -- WebSocket patterns for real-time data (MEDIUM confidence)

### Existing Codebase (verified -- HIGH confidence)
- `src/execution/application/handlers.py` -- TradePlanHandler lifecycle (generate -> approve -> execute)
- `src/execution/domain/value_objects.py` -- TradePlan, OrderSpec, OrderResult, TradePlanStatus
- `src/execution/domain/repositories.py` -- IBrokerAdapter, ITradePlanRepository interfaces
- `src/execution/infrastructure/alpaca_adapter.py` -- AlpacaExecutionAdapter (paper=True, mock fallback)
- `personal/execution/paper_trading.py` -- PaperTradingClient (legacy, pre-DDD)
- `personal/risk/manager.py` -- full_risk_check(), check_entry_allowed(), drawdown assessment
- `personal/risk/drawdown.py` -- assess_drawdown() with 10/15/20% tier thresholds
- `personal/sizer/kelly.py` -- validate_position() with 8% position / 25% sector limits
- `cli/main.py` -- Typer CLI with regime, score, signal, trade, screener, portfolio commands
- `commercial/api/main.py` -- FastAPI app with existing routes and middleware

---
*Feature research for: Intrinsic Alpha Trader v1.2 Production Trading & Dashboard*
*Domain: Automated Pipeline, Live Trading, Strategy Approval, Web Dashboard*
*Researched: 2026-03-13*
