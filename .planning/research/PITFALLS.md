# Pitfalls Research

**Domain:** Automated live trading pipeline, pipeline scheduling, web dashboard, strategy/budget approval workflow
**System:** Intrinsic Alpha Trader v1.1 -> v1.2
**Researched:** 2026-03-13
**Confidence:** HIGH (codebase analysis + official Alpaca docs + domain literature)

---

## Critical Pitfalls

### Pitfall 1: One-Boolean Live Trading Switch With No Safety Net

**What goes wrong:**
The existing `AlpacaExecutionAdapter` hardcodes `paper=True` at line 44 of `src/execution/infrastructure/alpaca_adapter.py`. Switching to live trading means changing this single boolean to `paper=False` (or making it configurable). There is no environment guard, no confirmation gate, no daily budget cap, and no "are you sure this is production?" check between the code and real money. A misconfigured `.env` file or an accidental deploy sends live orders immediately.

**Why it happens:**
The adapter was designed exclusively for paper trading. The mock fallback pattern (credentials missing = mock mode) was a safety net for development, but it creates a dangerous inversion for live trading: credentials present = real orders. There is no intermediate "live mode explicitly enabled" flag. The `PaperTradingClient` in `personal/execution/paper_trading.py` has the same pattern -- `_use_mock = not (api_key and secret_key)` -- meaning any environment with credentials auto-activates real execution.

**How to avoid:**
1. Add an explicit `TRADING_MODE` setting (`paper`/`live`/`dry-run`) in `src/settings.py`. Default MUST be `paper`. Live mode requires BOTH credentials AND `TRADING_MODE=live`.
2. The `AlpacaExecutionAdapter.__init__()` must check `TRADING_MODE` before setting `paper=False`. Even with valid live credentials, `TRADING_MODE=paper` forces paper mode.
3. Add a startup banner that clearly logs whether the system is in paper or live mode. The log line must be impossible to miss: `*** LIVE TRADING MODE ACTIVE -- REAL MONEY ***`.
4. Require separate API keys for paper and live (Alpaca uses different key pairs). Store them in separate env vars (`ALPACA_PAPER_API_KEY` / `ALPACA_LIVE_API_KEY`). Never reuse paper keys for live.
5. The `paper=True/False` parameter in `TradingClient()` must be derived from `TRADING_MODE`, not from whether credentials exist.

**Warning signs:**
- Any code path where `paper=False` can be reached without an explicit `TRADING_MODE` check.
- `.env.example` that does not clearly separate paper and live credential sections.
- Tests that pass credentials and don't verify mock mode is still active.

**Phase to address:**
Live Trading phase -- the very first task before any other live integration work.

---

### Pitfall 2: Silent Error Fallback to Mock During Live Execution

**What goes wrong:**
The `AlpacaExecutionAdapter._real_bracket_order()` (line 94-127) catches ALL exceptions and falls back to `self._mock_bracket_order(spec)`. This means if a live order fails for ANY reason (network timeout, insufficient funds, PDT rule violation, account restricted to liquidation), the system silently returns a "filled" mock result. The caller has no way to know the real order was never placed. In an automated pipeline, this means the system believes it has a position that does not exist.

**Why it happens:**
The mock fallback was a convenience for development -- if Alpaca is down, tests still pass. But this pattern is catastrophic for live trading. The same pattern exists in `_real_get_positions()` (returns `[]` on error) and `_real_get_account()` (returns `cash: 0.0, status: ERROR`). The `PaperTradingClient` has the identical pattern at lines 101-103.

**Specific failure cascade:**
1. Live bracket order fails (e.g., HTTP 403 "insufficient buying power")
2. `_real_bracket_order` catches exception, returns mock `OrderResult(status="filled")`
3. `TradePlanHandler.execute()` sees "filled", updates plan status to `EXECUTED`
4. Pipeline continues, believes position is open
5. Next pipeline run calculates portfolio value including phantom position
6. Risk management uses wrong portfolio value for drawdown calculation
7. Real account has no position but system thinks it does -- stop-loss monitoring watches a phantom trade

**How to avoid:**
1. Remove ALL mock fallbacks from the live code path. Create separate `LiveAlpacaAdapter` and `PaperAlpacaAdapter` classes (or at minimum, raise on error in live mode, fallback only in paper/mock mode).
2. If `TRADING_MODE=live`, exceptions in `submit_order()` MUST propagate as `OrderResult(status="FAILED", error_message=str(e))`. Never return mock data for a failed live order.
3. Add `OrderResult.is_mock: bool` field to distinguish mock fills from real fills. Any live pipeline step that receives a mock result when in live mode must halt and alert.
4. The pipeline scheduler must treat `FAILED` orders as hard stops requiring human intervention, not as "try again next run."

**Warning signs:**
- `except Exception` blocks that return mock/default data instead of raising or returning error results.
- Any `OrderResult` that has `order_id` starting with "MOCK-" when `TRADING_MODE=live`.
- Position count mismatch between system state (SQLite) and broker state (Alpaca API `get_positions()`).

**Phase to address:**
Live Trading phase -- must be refactored before the first live order is placed.

---

### Pitfall 3: Automated Pipeline Running Outside Market Hours

**What goes wrong:**
A scheduler fires the daily pipeline (screen -> score -> signal -> execute) at the configured time, but the market is closed (holidays, weekends, early close days). Market orders submitted outside trading hours either fail immediately (Alpaca rejects) or queue until next open and fill at a gap price far from the entry price used in position sizing. ATR-based stop-loss levels calculated at Friday's close may be invalid at Monday's open.

**Why it happens:**
The system has no concept of market calendars. There is no `is_market_open()` check anywhere in the codebase. The `.env.example` has `TRADING_ENV=development` but no timezone or market hours configuration. Cron or APScheduler runs at fixed times regardless of market status. US market has 9 holidays, 3-4 early close days per year, and DST changes affect UTC-based schedules twice a year.

**Specific scenarios:**
- **Holiday:** Scheduler runs on Martin Luther King Jr. Day. Screen/score work fine (using cached data). Pipeline generates trade plans and submits orders. Alpaca rejects with "market is closed" or queues as GTC order that fills Monday at an unknown price.
- **Early close:** Day after Thanksgiving closes at 1:00 PM ET. Pipeline scheduled for 3:00 PM ET submits orders to a closed market.
- **DST transition:** Pipeline scheduled at "9:30 AM ET" using UTC offset runs at 8:30 AM ET or 10:30 AM ET when DST changes.
- **Weekend:** If scheduler has a bug and fires Saturday, orders queue until Monday.

**How to avoid:**
1. Use `exchange_calendars` library (standard for US market calendar) to check market status before pipeline execution. Guard the entire pipeline: `if not calendar.is_session(today): skip`.
2. Schedule by market time (US/Eastern), not UTC. Use `zoneinfo.ZoneInfo("America/New_York")` for timezone-aware scheduling.
3. Pipeline execution should happen between market open (9:30 AM ET) and close (4:00 PM ET), with a buffer. Run screening/scoring overnight, execute orders after 10:00 AM ET (avoid the volatile first 30 minutes).
4. All order submissions must check `time_in_force` carefully. Use `TimeInForce.DAY` for automated orders, never `TimeInForce.GTC` for scheduled pipeline orders -- a GTC order queued Friday may fill Monday at a wildly different price.
5. Log and record every pipeline skip with reason: "Skipped: market holiday (MLK Day 2026-01-19)".

**Warning signs:**
- No `exchange_calendars` or equivalent in `pyproject.toml` dependencies.
- Scheduler configured with UTC times instead of US/Eastern.
- Orders submitted with `TimeInForce.GTC` in automated pipeline.
- Pipeline log gaps on holidays/weekends (no "skipped" entries).

**Phase to address:**
Automated Pipeline phase -- the scheduler must integrate market calendar before the first scheduled run.

---

### Pitfall 4: No Reconciliation Between System State and Broker State

**What goes wrong:**
The system maintains its own portfolio state in SQLite (`portfolio.db`, `positions` table) separately from Alpaca's actual account state. Over time, these diverge. An order may partially fill, a stop-loss may trigger, a corporate action may adjust shares, or a manual trade via Alpaca dashboard creates a position the system doesn't know about. Without reconciliation, the risk management layer operates on fictional data.

**Why it happens:**
The current architecture has a one-way flow: system generates plan -> submits order -> records result. There is no reverse flow: broker state -> system state. The `get_positions()` and `get_account()` methods exist on the adapter but are only used by the CLI `monitor` command for display -- they never update the system's portfolio state. The `SqlitePortfolioRepository` stores `peak_value` and `initial_value` but never syncs with Alpaca's `portfolio_value`.

**Specific drift scenarios:**
- **Partial fill:** Order for 100 shares only fills 73. System records 100 (from plan quantity), Alpaca has 73.
- **Stop-loss triggered:** ATR stop fires at broker level. Alpaca closes position. System still shows position as open. Drawdown calculation is wrong.
- **Take-profit hit:** Bracket order's take-profit leg executes. System doesn't update.
- **Manual intervention:** User sells a position via Alpaca dashboard during a drawdown. System doesn't know.
- **Peak value drift:** `Portfolio.peak_value` is only updated when `drawdown` property is accessed. If no one calls it between peak and decline, peak_value is stale.

**How to avoid:**
1. Build a `ReconciliationService` that runs at pipeline start and periodically. Compares `adapter.get_positions()` with `position_repo.find_all_open()` and flags discrepancies.
2. After every order submission, poll the order status until it reaches a terminal state (filled, partially_filled, cancelled, expired). Do not assume the initial response is final.
3. Use Alpaca's order events (websocket or polling) to track fill updates. The current codebase returns `OrderResult` immediately from `submit_order()` but market orders may not fill instantly (especially in pre-market or for illiquid stocks).
4. `peak_value` must be updated from Alpaca's `portfolio_value` at the start of each pipeline run, not computed from internal position tracking.
5. Add a daily reconciliation check at pipeline start. If discrepancy is found, halt the pipeline and alert.

**Warning signs:**
- `Portfolio.peak_value` never updated from broker data.
- No code path that calls `get_positions()` and compares with internal state.
- `OrderResult.quantity` taken from the plan (requested) rather than from the fill (actual).
- No order status polling after `submit_order()`.

**Phase to address:**
Live Trading phase -- reconciliation must exist before automated execution is trusted.

---

### Pitfall 5: Strategy Approval Workflow That Either Blocks Everything or Approves Everything

**What goes wrong:**
The v1.2 goal is "human approves strategy + daily budget, execution is automatic." But the design can fail in two opposing ways: (1) The approval workflow requires so much human input that it defeats automation (approve each trade individually, like v1.0's `approve` command), or (2) The approval is so coarse (approve "buy stocks under $100K/day") that it provides no meaningful control and the system trades freely with real money.

**Why it happens:**
The existing approval pattern in `TradePlanHandler.approve()` is per-trade: each symbol requires individual approval via CLI prompt. This is fine for manual trading but incompatible with a daily automated pipeline that may generate 5-10 trade plans. On the other extreme, a "daily budget" approval with no trade-level constraints allows the system to concentrate all budget in a single risky position.

**Specific failure modes:**
- **Over-blocking:** Strategy approval required daily at 9:00 AM. User is in a meeting, misses the window. Pipeline generates plans but cannot execute. By 3:00 PM, market conditions have changed and the signals are stale. User approves at 3:30 PM, orders execute with outdated entry prices.
- **Under-constraining:** User approves "$5,000 daily budget, BUY signals only." System buys 5 positions at $1,000 each in the same sector. Risk management should catch sector concentration (25% limit), but sector check relies on internal state which may be stale (see Pitfall 4).
- **Stale approval:** User approves strategy on Sunday for the week. Tuesday the market enters a bear regime. The pre-approved strategy still executes bull-market plays.

**How to avoid:**
1. Design a two-tier approval model:
   - **Strategy approval** (weekly/daily): approve regime-aware parameters: allowed signal types (BUY only / BUY+HOLD), maximum daily budget, maximum per-trade size, sector exclusions.
   - **Execution guard** (automatic): the system checks each trade against the approved parameters AND real-time risk gates (drawdown level, sector exposure, position limits). No per-trade human approval needed IF within approved parameters.
2. Strategy approvals must have an expiration. A 7-day approval that auto-expires forces periodic human review. Never allow indefinite approvals.
3. If regime changes during an active approval period, the system should pause and request re-approval. The `RegimeChangedEvent` (already defined, partially wired via `regime_adjuster.on_regime_changed` in bootstrap) should trigger this.
4. Store approval records with timestamp, parameters, and expiry in the database. Every executed trade must reference which approval authorized it (audit trail).

**Warning signs:**
- Approval model has no expiration date.
- No check for regime change between approval and execution.
- Pipeline that generates AND executes plans in the same run without an approval checkpoint.
- No per-trade constraint enforcement beyond the daily budget cap.

**Phase to address:**
Strategy Approval phase -- design the approval model BEFORE building the automated pipeline, because the pipeline's behavior depends on what approvals look like.

---

### Pitfall 6: Drawdown Defense Not Working Autonomously

**What goes wrong:**
The 3-tier drawdown defense (10%/15%/20%) is the system's most critical risk control. It MUST work in automated mode. But the current implementation has two fatal gaps: (1) `cooldown_days_remaining` is passed as a parameter, not tracked in persistent state, and (2) the drawdown calculation depends on `peak_value` which is only updated when manually accessed.

**Why it happens:**
In v1.0's manual CLI workflow, the human operator calls `monitor` to check drawdown and manually passes `cooldown_days` to the risk manager. The 30-day cooldown after 20% drawdown is a business rule in code (`COOLDOWN_DAYS = 30` in `personal/risk/drawdown.py`) but nowhere is the cooldown start date persisted. If the automated pipeline restarts, it has no memory of an active cooldown period.

**Specific code gaps:**
- `assess_drawdown()` takes `cooldown_days_remaining: int = 0` as a parameter. Default is 0 (no cooldown). Nothing persists the cooldown state.
- `full_risk_check()` takes `cooldown_days: int = 0`. Default is 0. The automated pipeline would need to compute this from a stored cooldown start date, but no such storage exists.
- `Portfolio.peak_value` is stored in SQLite but only updated when `Portfolio.drawdown` property is accessed. If the pipeline doesn't access this property between portfolio value increase and decrease, peak_value is wrong.
- Level 3 drawdown returns `requires_cooldown: True` but no code reads this flag and persists a cooldown start date.

**Failure scenario:**
1. Portfolio drops 20%. `assess_drawdown()` returns `level: 3, action: "FULL LIQUIDATION"`.
2. Pipeline liquidates positions (if this is even implemented -- current code only returns the assessment, doesn't actually liquidate).
3. Next day, pipeline restarts. `cooldown_days_remaining` defaults to 0. System thinks cooldown is over.
4. Pipeline immediately re-enters positions during what should be a 30-day cooling period.
5. Market continues declining. Second liquidation, more losses.

**How to avoid:**
1. Add a `CooldownState` table in SQLite with `start_date`, `end_date`, `trigger_drawdown_pct`. The pipeline must check this at startup.
2. The automated pipeline must implement the ACTIONS, not just the assessment:
   - Level 1 (10%): pipeline sets `allow_new_entries = False` in approval state.
   - Level 2 (15%): pipeline generates SELL orders to reduce positions by 50%.
   - Level 3 (20%): pipeline generates SELL orders for ALL positions and persists cooldown start date.
3. `peak_value` must be synced from Alpaca at every pipeline run start (see Pitfall 4).
4. Add an integration test that simulates: "20% drawdown -> cooldown stored -> pipeline restart -> cooldown still active."

**Warning signs:**
- `cooldown_days_remaining` always defaults to 0 in pipeline code.
- No database table or persistent state for cooldown periods.
- Drawdown assessment returned but no code acts on the `reduce_pct` or `requires_cooldown` fields.
- `peak_value` only updated via `Portfolio.drawdown` property, not from broker sync.

**Phase to address:**
Live Trading phase -- drawdown defense must be autonomous before live execution starts. This is a hard prerequisite.

---

### Pitfall 7: Web Dashboard Polling Trades SQLite While Pipeline Writes

**What goes wrong:**
The web dashboard (FastAPI) and the automated pipeline (scheduler) both access the same SQLite databases simultaneously. The dashboard reads portfolio state, trade plans, and execution history while the pipeline writes scores, signals, and order results. SQLite's default journal mode (`DELETE`) blocks concurrent readers during writes, causing "database is locked" errors on the dashboard during pipeline runs.

**Why it happens:**
The existing architecture uses separate SQLite files per context (`data/scoring.db`, `data/signals.db`, `data/portfolio.db`) via `DBFactory`. But the connection pattern (`sqlite3.connect(self._db_path)` in every method, no WAL mode, no connection pooling) is designed for a single-process CLI, not for concurrent access from a web server and a background pipeline.

**Specific contention points:**
- Pipeline writes to `data/portfolio.db` (trade plan status updates, position records) while dashboard reads the same file for portfolio display.
- Pipeline writes to `data/scoring.db` (new scores) while the commercial API serves QuantScore queries from the same store.
- DuckDB analytical queries (screener) hold read locks that block SQLite WAL checkpoint.

**How to avoid:**
1. Enable WAL mode on all SQLite connections: `conn.execute("PRAGMA journal_mode=WAL")`. WAL allows concurrent reads during writes. This is a one-line fix per repository.
2. The dashboard should use read-only connections: `sqlite3.connect(f"file:{path}?mode=ro", uri=True)`.
3. For the pipeline-to-dashboard data flow, consider a message-based pattern: pipeline writes to SQLite and publishes an event; dashboard subscribes to events for real-time updates instead of polling the database.
4. Set `PRAGMA busy_timeout = 5000` (5 seconds) on all connections so transient locks retry instead of immediately failing.
5. If the dashboard needs real-time updates, use SSE (Server-Sent Events) from FastAPI, not WebSocket. SSE is simpler, unidirectional (server to client), and sufficient for a portfolio dashboard that updates every few seconds. The commercial API already has FastAPI infrastructure that can serve SSE.

**Warning signs:**
- "database is locked" errors in either the pipeline or dashboard logs.
- Dashboard showing stale data during pipeline runs.
- No `PRAGMA journal_mode=WAL` in any repository initialization.
- Dashboard and pipeline importing the same repository class without any connection separation.

**Phase to address:**
Web Dashboard phase (infrastructure setup step), but WAL mode should be added in Automated Pipeline phase since the commercial API already exists and may conflict.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Mock fallback on live error | "Code never crashes" | Phantom positions, wrong portfolio state, invisible order failures | Never in live mode. Only in paper/dev mode. |
| Single `paper=True/False` toggle | Simple config | One env mistake = real money orders | Never. Use explicit `TRADING_MODE` enum. |
| No market calendar check | Pipeline code is simpler | Holiday/weekend orders, gap risk, stale signals | Never for automated pipeline. |
| Polling SQLite from dashboard | No new infrastructure needed | "database is locked" under concurrent access | Only if WAL mode enabled AND read-only dashboard connections. |
| Approval with no expiration | Less user friction | Stale approvals executing in changed market conditions | Never. All approvals must expire. |
| `cooldown_days=0` default | Backward compatible | 30-day cooldown ignored, re-entry during cooling period | Never. Must persist cooldown state. |
| SSE for all dashboard updates | Simpler than WebSocket | Cannot push bidirectional commands | Acceptable -- dashboard is mostly read-only. SSE is the right choice here. |
| In-memory rate limit state | Works for single instance | Rate limits reset on restart, no cross-instance sharing | Acceptable for v1.2 single-instance. Redis needed at scale. |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Alpaca paper -> live | Using same API keys for both environments | Alpaca requires separate key pairs. Store in separate env vars (`ALPACA_PAPER_*` / `ALPACA_LIVE_*`). Paper keys DO NOT work on live endpoint. |
| Alpaca order submission | Assuming immediate fill, not polling status | Market orders fill within seconds but are not guaranteed. Poll `get_order(order_id)` until terminal status. Use `TimeInForce.DAY` for automated orders. |
| Alpaca bracket orders | Submitting bracket during extended hours | Bracket orders rejected outside regular trading hours. Extended hours only accepts limit orders. |
| Alpaca PDT rule | Not checking day trade count before submitting | Accounts under $25K equity are restricted to 3 day trades per 5 business days. System's mid-term strategy (2-week minimum hold) avoids this, but automated sells within 1 day of buy trigger PDT. |
| Alpaca paper vs. live fills | Expecting identical fill behavior | Paper trading does not enforce liquidity constraints. A paper fill of 10,000 shares at $150 would succeed, but live may only fill 2,000 at that price. Paper also ignores slippage. |
| Alpaca dividends | Expecting paper account to reflect dividends | Paper trading does NOT simulate dividends. Long-term position values in paper do not include dividend income, making paper P&L unrealistically low for dividend-paying stocks. |
| yfinance data timing | Fetching "today's" data during pre-market | yfinance returns previous close during pre-market. If pipeline runs at 8:00 AM ET, "current price" is yesterday's close. Entry prices based on this will differ from actual market open price. |
| SQLite concurrent access | Using default journal mode with multiple processes | Enable WAL mode. Set busy_timeout. Use read-only connections for dashboard. |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Full universe screening on every pipeline run | Pipeline takes 30+ minutes, hitting yfinance rate limits | Cache scores, only re-screen symbols that changed. Use universe of ~400 S&P400 stocks, not all US equities. | Above 500 tickers per run |
| SQLite write contention between pipeline and dashboard | "database is locked" errors, dashboard freezes | WAL mode + busy_timeout + read-only dashboard connections | When dashboard has 2+ concurrent users during pipeline run |
| Per-symbol Alpaca API call for portfolio reconciliation | Rate limited (200 req/min), slow reconciliation | Use bulk `get_all_positions()` (single API call), not per-symbol queries | Above 10 positions |
| Dashboard polling SQLite every second | High CPU, unnecessary I/O | SSE with event-driven updates, poll every 30 seconds at most | Continuous refresh with 5+ dashboard users |
| APScheduler in-memory job store | Jobs lost on restart, missed pipeline runs | Use `SQLAlchemyJobStore` or persist last-run state separately | Any process restart |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Live API keys in `.env` committed to git | Anyone with repo access can trade on your account | Add `ALPACA_LIVE_*` to `.gitignore`. Use secrets manager for production. Never commit `.env` files. |
| `CORS allow_origins=["*"]` in commercial API (line 27, `commercial/api/main.py`) | Any website can make API requests to your trading dashboard | Restrict to specific dashboard origin (`http://localhost:3000` or production domain). |
| JWT secret key hardcoded as default (`"dev-only-change-me..."` in `commercial/api/config.py`) | Trivially forgeable tokens if default not overridden | Fail fast on startup if `JWT_SECRET_KEY` matches the dev default in production mode. |
| Dashboard exposes broker account details | If dashboard is publicly accessible, account info is leaked | Dashboard must require authentication. API keys and account IDs must never appear in dashboard responses. |
| Approval workflow bypass via direct API call | If the strategy approval is only enforced in the CLI, the scheduler/API can bypass it | Enforce approval checks in the execution domain layer, not just the presentation layer. |
| Pipeline logs containing full order details | Logs with account info, position sizes, and symbols are sensitive | Sanitize logs. Never log API keys. Use structured logging with PII filtering. |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Dashboard that only shows current state, no history | User cannot see how portfolio evolved, when trades were made | Include timeline view with historical P&L, trade markers, and drawdown chart |
| No clear visual distinction between paper and live mode | User accidentally monitors paper account thinking it is live | Prominent banner: red "LIVE" or green "PAPER" on every page. Different background color for live mode. |
| Approval workflow that requires synchronous response | User must be available at exact pipeline time to approve | Async approval: pipeline generates plans, sends notification (email/push/Telegram), waits for approval within time window (e.g., 30 minutes). If no response, skip execution. |
| Dashboard showing raw composite scores without context | "Score: 72.3" means nothing without reference | Show score relative to universe: "72.3 (top 15%)" or "72.3 / 100 -- Strong Buy zone" |
| Alert fatigue from too many notifications | User ignores all alerts including critical ones | Tier alerts: INFO (daily summary), WARNING (drawdown level 1), CRITICAL (drawdown level 2+, order failure). Only CRITICAL alerts are push notifications. |
| Pipeline status invisible until something breaks | User has no idea if daily pipeline ran successfully | Dashboard widget showing last pipeline run time, status, and count of actions taken. "Last run: Today 10:15 AM -- 3 scored, 1 signal, 0 executed" |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Live trading adapter:** Often missing `TRADING_MODE` guard -- verify that `paper=False` cannot be reached without explicit `TRADING_MODE=live` in settings.
- [ ] **Order execution:** Often missing order status polling -- verify that `submit_order()` polls until terminal status, not just returning the initial response.
- [ ] **Reconciliation:** Often missing broker <-> system state sync -- verify that `get_positions()` result is compared with internal position state at pipeline start.
- [ ] **Drawdown defense:** Often missing cooldown persistence -- verify that a 20% drawdown event writes a cooldown start date to the database and subsequent pipeline runs read it.
- [ ] **Market calendar:** Often missing holiday handling -- verify that the pipeline skips execution on market holidays and early-close days.
- [ ] **Approval expiration:** Often missing TTL -- verify that strategy approvals have an expiry date and expired approvals block execution.
- [ ] **Dashboard auth:** Often missing when "it's just for me" -- verify that the web dashboard requires authentication even for personal use (if exposed on a network).
- [ ] **Pipeline failure alerting:** Often missing notification on silent failure -- verify that a failed pipeline run sends an alert (not just logs).
- [ ] **CORS restriction:** Verify `allow_origins=["*"]` in `commercial/api/main.py` is changed to the actual dashboard origin before deployment.
- [ ] **Timezone handling:** Verify all timestamps in trade plans, approvals, and logs use timezone-aware datetimes (`datetime.now(timezone.utc)`), not naive datetimes.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Live order placed accidentally | HIGH | Immediately cancel via Alpaca dashboard. Check `get_all_orders(status="open")` for pending orders. If filled, assess whether to hold or close. Document the incident. |
| Phantom position (system thinks position exists, broker doesn't) | MEDIUM | Run reconciliation. Compare `position_repo.find_all_open()` with `adapter.get_positions()`. Update system state to match broker. Investigate why the divergence occurred. |
| Drawdown cooldown skipped | HIGH | Manually halt the pipeline. Check current drawdown level. If past 20%, liquidate remaining positions. Manually record cooldown start date. Investigate why persistence failed. |
| Pipeline ran on holiday | LOW | Check if orders were queued (GTC) or rejected. Cancel any queued orders. Verify no fills occurred. Add market calendar check. |
| SQLite corruption from concurrent writes | MEDIUM | Restore from last backup. Enable WAL mode. Verify all data files with `PRAGMA integrity_check`. Reconcile with broker state. |
| Stale approval executing in changed regime | MEDIUM | Cancel pending orders. Re-run pipeline with current regime detection. Create new approval for current conditions. Verify no trades executed under stale approval. |
| Dashboard shows wrong portfolio state | LOW | Force reconciliation. Dashboard auto-refreshes. If persistent, check SQLite file permissions and WAL mode. |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| One-boolean live switch (1) | Live Trading (first task) | `TRADING_MODE` setting exists, defaults to `paper`, adapter reads it |
| Silent mock fallback (2) | Live Trading (adapter refactor) | Live mode adapter raises on error, never returns mock data |
| No market calendar (3) | Automated Pipeline (scheduler setup) | Pipeline skips on holidays, logs skip reason |
| No reconciliation (4) | Live Trading (post-order flow) | `ReconciliationService` runs at pipeline start, flags mismatches |
| Bad approval model (5) | Strategy Approval (design first) | Approval has expiry, regime-change pause, per-trade constraints |
| Drawdown not autonomous (6) | Live Trading (risk engine) | Cooldown persisted, drawdown actions implemented, not just assessed |
| SQLite concurrent access (7) | Automated Pipeline (infra setup) | WAL mode enabled, dashboard uses read-only connections |
| CORS wildcard (security) | Web Dashboard (first task) | `allow_origins` restricted to dashboard URL |
| JWT default secret (security) | Web Dashboard (first task) | Startup fails if JWT secret matches dev default |
| Alert fatigue (UX) | Web Dashboard (notification design) | Tiered alerts, only CRITICAL push notifications |

## Sources

- Direct codebase analysis of `/home/mqz/workspace/trading/` (HIGH confidence -- primary source)
  - `src/execution/infrastructure/alpaca_adapter.py` -- mock fallback on live error (line 127), hardcoded `paper=True` (line 44)
  - `src/execution/application/handlers.py` -- per-trade approval flow, no batch/strategy approval
  - `src/execution/domain/value_objects.py` -- `TradePlanStatus` enum (no EXPIRED status for stale approvals)
  - `personal/risk/drawdown.py` -- cooldown_days parameter defaulting to 0, no persistence
  - `personal/risk/manager.py` -- full_risk_check with cooldown_days=0 default
  - `src/portfolio/domain/aggregates.py` -- peak_value only updated on drawdown property access
  - `src/portfolio/infrastructure/sqlite_portfolio_repo.py` -- no WAL mode, no read-only option
  - `commercial/api/main.py` -- CORS `allow_origins=["*"]` (line 27)
  - `commercial/api/config.py` -- JWT default secret key
  - `src/settings.py` -- no TRADING_MODE setting, no paper/live distinction
  - `src/bootstrap.py` -- AlpacaExecutionAdapter wired with credentials only, no mode check
  - `.env.example` -- no TRADING_MODE variable, no paper/live key separation
- [How to Fix 30 Common Errors in Alpaca's Trading API](https://alpaca.markets/learn/how-to-fix-common-trading-api-errors-at-alpaca) (HIGH confidence -- official Alpaca)
- [Paper Trading - Alpaca Docs](https://docs.alpaca.markets/docs/paper-trading) (HIGH confidence -- official Alpaca)
- [Paper Trading vs. Live Trading: A Data-Backed Guide](https://alpaca.markets/learn/paper-trading-vs-live-trading-a-data-backed-guide-on-when-to-start-trading-real-money) (HIGH confidence -- official Alpaca)
- [Alpaca Support: Difference Between Paper and Live Trading](https://alpaca.markets/support/difference-paper-live-trading) (HIGH confidence -- official Alpaca)
- [Trading Automation: From Idea to Real-Time Execution](https://obside.com/trading-algorithmic-trading/trading-automation/) (MEDIUM confidence -- domain expertise)
- [Systemic Failures in Algorithmic Trading (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8978471/) (HIGH confidence -- academic)
- [5 Common Algorithmic Trading Mistakes (Intrinio)](https://intrinio.com/blog/5-common-mistakes-to-avoid-when-using-automated-trading-systems) (MEDIUM confidence)
- [Weaponizing Real Time: WebSocket/SSE with FastAPI](https://blog.greeden.me/en/2025/10/28/weaponizing-real-time-websocket-sse-notifications-with-fastapi-connection-management-rooms-reconnection-scale-out-and-observability/) (MEDIUM confidence)
- [APScheduler User Guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) (HIGH confidence -- official docs)
- [Human-in-the-Loop Architecture: When Humans Approve Agent Decisions](https://www.agentpatterns.tech/en/architecture/human-in-the-loop-architecture) (MEDIUM confidence)

---
*Pitfalls research for: Automated live trading pipeline, scheduling, web dashboard, strategy approval*
*Researched: 2026-03-13*
