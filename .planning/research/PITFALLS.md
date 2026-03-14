# Pitfalls Research

**Domain:** Adding technical scoring, sentiment analysis, commercial API, and performance attribution to existing quantitative trading system
**System:** Intrinsic Alpha Trader v1.3 -> v1.4 (Full Stack Trading Platform)
**Researched:** 2026-03-14
**Confidence:** HIGH (codebase analysis + domain expertise + known tech debt from PROJECT.md)

---

## Critical Pitfalls

### Pitfall 1: Lookahead Bias in Technical Indicator Calculations

**What goes wrong:**
Technical indicators (RSI, MACD, MA, ADX, OBV) use future data during backtesting or scoring, producing unrealistically good results. The system then makes live trading decisions based on inflated scores. Common forms: using the current bar's close to compute an indicator value that should only use data up to the previous bar; using the full dataset to normalize indicator values (e.g., min-max scaling OBV across the entire time series including future data); rebalancing the composite score using forward-looking regime information.

The existing `TechnicalIndicatorAdapter.compute_technical_subscores()` in `src/scoring/infrastructure/core_scoring_adapter.py` fetches 756 days of price history and calls `indicators.compute_all(df)`. The indicators themselves (in `core/data/indicators.py`) use pandas rolling/ewm functions which are correctly causal. However, the `_compute_obv_change()` method uses a 60-day lookback which is fine for live scoring but could be problematic if this same code path is used during walk-forward backtesting without proper data slicing.

**Why it happens:**
The existing fundamental scoring (F-Score, Z-Score) uses point-in-time financial data -- each quarterly filing has a known date, making lookahead bias easy to avoid. Technical indicators are different: they operate on continuous price data where the boundary between "known" and "unknown" shifts with each bar. Developers compute indicators on the full DataFrame and then slice by date, but the indicator values themselves already contain future information (e.g., a 200-day MA computed using today's close when scoring for yesterday).

**How to avoid:**
1. **Strict data cutoff in backtesting:** When scoring for date T, the DataFrame must end at T-1 close. Never pass the full history and then pick the row at T.
2. **Validate with the "walk-forward data fence" test:** For each scoring date, assert that no data point in the indicator computation postdates the scoring date.
3. **Separate live vs. backtest code paths:** Live scoring uses the full current DataFrame (correct -- today's data IS known). Backtest scoring must truncate the DataFrame to `df[:scoring_date]` BEFORE computing indicators.
4. **Add a `as_of_date` parameter to `TechnicalIndicatorAdapter.compute_technical_subscores()`** that truncates data before indicator computation.

**Warning signs:**
- Backtest Sharpe ratio > 2.0 for a long-only equity strategy (suspiciously high)
- Live performance dramatically worse than backtest (the classic "it worked in backtest" failure)
- Technical score for a past date changes when new data is appended to the DataFrame
- Composite scores in the DuckDB scoring store differ from re-computed scores for the same date

**Phase to address:**
Technical Scoring phase -- implement the `as_of_date` cutoff in the adapter before integrating technical scores into the composite pipeline. The backtest engine already has walk-forward logic in `core/backtest/walk_forward.py`; ensure it enforces the data fence.

---

### Pitfall 2: Sentiment Score Defaulting to 50 Silently Corrupts Composite Scores

**What goes wrong:**
The current `SentimentScore` value object defaults to 50 (neutral) when data is insufficient. The existing `core/scoring/sentiment.py` function `compute_sentiment_score()` already returns `{"sentiment_score": 50.0, "note": "insufficient data, using neutral"}` when no inputs are available. The composite score formula (`CompositeScore.compute()`) assigns 20% weight to sentiment. If sentiment silently defaults to 50 for most stocks (because real sentiment data sources are expensive or incomplete), the composite score becomes effectively an 80/20 fundamental/technical score with a constant 10-point sentiment contribution (50 * 0.20 = 10). This is mathematically equivalent to a different weight scheme, but the system reports incorrect weights, making the explainability chain lie to the user.

**Why it happens:**
Real sentiment data requires: (1) news sentiment APIs ($50-200/mo for meaningful coverage), (2) insider trading data (SEC Form 4, available via EDGAR but needs parsing), (3) institutional holdings (13F filings, quarterly lag), (4) analyst revision data (expensive -- Bloomberg/Refinitiv tier). The temptation is to build the sentiment scoring interface, hardcode 50 as default, and plan to "add real data later." But the composite score starts using this fake 50 immediately, and nobody notices the distortion because the system "works."

**How to avoid:**
1. **Track data availability explicitly:** Add a `confidence` field to `SentimentScore` (HIGH/MEDIUM/LOW/NONE). When confidence is NONE, exclude sentiment from the composite calculation entirely and adjust weights to fundamental+technical only.
2. **Two-mode composite calculation:** When sentiment data is available, use 40/40/20 weights. When sentiment is missing, use 55/45 fundamental/technical (re-normalized to sum to 1.0).
3. **Log and surface missing data:** Every time sentiment defaults to 50, emit a domain event (`SentimentDataMissingEvent`) that shows up in the dashboard's data quality panel.
4. **Do not ship sentiment scoring without at least one real data source.** The simplest free source is analyst target price vs. current price (already implemented in `compute_sentiment_score()` -- requires `analyst_target` and `current_price` from yfinance). Ensure this path is wired before activating sentiment in the composite.

**Warning signs:**
- More than 50% of scored stocks have sentiment_score = 50.0 exactly
- `SentimentScore.value` distribution is a spike at 50 instead of a distribution
- Composite scores for high-quality and low-quality stocks cluster closer together than expected (the constant 10-point sentiment contribution compresses the range)
- No sentiment data source is actually configured in `.env` but sentiment scoring is "complete"

**Phase to address:**
Sentiment Scoring phase -- must ship with at least one real data source wired. Pipeline Stabilization phase should add data quality monitoring that catches the "silent 50" pattern.

---

### Pitfall 3: DDD Wiring Gaps Compound When Adding New Bounded Contexts

**What goes wrong:**
The PROJECT.md explicitly flags tech debt: "DDD wiring gaps need fixing" and "scoring store mismatch needs resolution." The current system has two parallel code paths: the `core/` legacy path (working) and the `src/` DDD path (partially wired). When adding new features (technical scoring, sentiment scoring, performance attribution), developers face a choice: wire through the incomplete DDD path or add directly to `core/`. Each new feature added to `core/` makes the DDD migration harder. Each new feature added to `src/` without fixing existing wiring gaps encounters broken cross-context communication (the event bus, repository injection, handler dispatch).

The specific store mismatch: scoring uses SQLite (`src/scoring/infrastructure/sqlite_repo.py`) while signals and backtest use DuckDB (`src/signals/infrastructure/duckdb_signal_store.py`, `src/backtest/infrastructure/duckdb_backtest_store.py`). When the composite score includes a new technical score component, that score needs to be stored, queried for signal generation, and available for backtest replay. If technical scores go to SQLite (scoring context) but signals need them from DuckDB (signal context), there is a data access mismatch.

**Why it happens:**
The adapter pattern (`CoreScoringAdapter`, `TechnicalIndicatorAdapter`, `CoreSignalAdapter`) was a pragmatic choice to ship v1.0-v1.2 quickly by wrapping `core/` functions. This works when the DDD layer is thin -- just VOs and adapters. But v1.4 requires real domain logic in the DDD layer (regime-adjusted weights, sentiment fusion, performance decomposition). At this point, the adapters become bottlenecks: they cannot express the new business rules because the underlying `core/` functions do not support them.

**How to avoid:**
1. **Fix the store mismatch FIRST**, before adding any new feature. Decide: either all analytical stores use DuckDB (recommended -- DuckDB is better for OLAP queries like "show me all stocks with composite > 60 and RSI oversold") or all use SQLite. Unify before adding new table schemas.
2. **New features go into `src/` DDD path ONLY.** The `core/` directory is frozen for new feature additions. New technical/sentiment logic lives in domain services, not in new `core/` modules.
3. **Wire one complete vertical slice first:** Pick a simple feature (e.g., technical scoring for a single indicator like RSI), and wire it end-to-end through DDD: domain VO -> domain service -> application handler -> infrastructure adapter -> persistence -> presentation/API. This flushes out all the wiring gaps before adding complexity.
4. **Fix the event bus:** The `SyncEventBus` in `src/shared/infrastructure/sync_event_bus.py` and `AsyncEventBus` in `src/shared/infrastructure/event_bus.py` need verified cross-context event delivery. Test: scoring context publishes `ScoreUpdatedEvent` -> signals context receives it and recomputes signal.

**Warning signs:**
- New code added to `core/` directory instead of `src/`
- Application handlers that bypass domain services and call infrastructure directly
- Tests that work with in-memory repos but fail with SQLite/DuckDB repos
- Cross-context queries that import from another context's internal modules instead of going through the event bus
- Two different score values for the same stock: one from `core/scoring/` and one from `src/scoring/`

**Phase to address:**
Pipeline Stabilization phase (FIRST, before any new feature). This phase must unify the store, fix event bus wiring, and validate one vertical slice before Technical Scoring begins.

---

### Pitfall 4: Commercial API Security Hardcoded as Afterthought

**What goes wrong:**
The commercial API (QuantScore, RegimeRadar, SignalFusion) is built with FastAPI, and developers focus on getting the endpoints working first, then "add auth later." By the time auth is added, the system has: (1) no rate limiting, so a single user can exhaust API quota and DuckDB connections; (2) API keys stored in plain text in SQLite; (3) no request logging for billing, making it impossible to charge users accurately; (4) no input validation on ticker symbols, allowing injection attacks via malformed symbols; (5) no response sanitization, leaking internal error traces with Python file paths and DuckDB schema details.

**Why it happens:**
The personal trading system has no authentication (single user, localhost). The commercial API requires authentication, authorization, rate limiting, billing, and audit logging -- all of which are infrastructure concerns that do not exist in the current codebase. The natural development flow is: build endpoints -> test manually -> add auth. But auth retrofitting is expensive because it affects every endpoint, every error handler, and every response shape.

**How to avoid:**
1. **Auth middleware from day one.** The very first commercial API endpoint must have authentication before the second endpoint is written. Use API key authentication (simplest for B2B API): `X-API-Key` header -> lookup in database -> attach user context to request.
2. **Rate limiting from day one.** Use `slowapi` (FastAPI-compatible, wraps `limits`) with per-key rate limits. Different tiers get different limits.
3. **Request logging from day one.** Every API request logged with: timestamp, API key, endpoint, response time, status code. This is the billing audit trail. Use a separate SQLite table or append-only file (not the same DB as trading data).
4. **Input validation as domain invariant.** The `Symbol` value object in `src/scoring/domain/value_objects.py` already validates tickers (uppercase, max 10 chars). Route the commercial API through the same domain layer -- do not create a parallel validation path.
5. **Error sanitization.** Never expose Python tracebacks, file paths, or SQL queries in API responses. Use FastAPI exception handlers that map internal errors to generic API error responses with correlation IDs.

**Warning signs:**
- Commercial API endpoints accessible without an API key (even in dev)
- No `slowapi` or rate limiting middleware in the FastAPI app
- API error responses containing Python traceback text
- No logging table/file for API request audit trail
- Billing amounts calculated from "number of API keys" rather than actual usage

**Phase to address:**
Commercial API phase -- but auth/rate-limit/logging middleware must be the FIRST thing built in that phase, before any scoring endpoint. Not the last thing.

---

### Pitfall 5: Performance Attribution Without Accurate Trade Tracking

**What goes wrong:**
Performance attribution decomposes P&L into components: what came from stock selection (alpha), what came from sector allocation, what came from market timing (regime), what came from position sizing (risk management). This requires accurate records of: (1) every trade's entry and exit prices with timestamps, (2) the composite score and regime at the time of entry, (3) the position size and why that size was chosen, (4) benchmark returns over the same period. If any of these are missing or approximate, the attribution is garbage.

The current system stores trade plans (`src/execution/infrastructure/sqlite_trade_plan_repo.py`) and has execution tracking, but it may not capture the "scoring context at entry time" -- the composite score, regime classification, and individual factor scores that were active when the trade was opened. Without this, you cannot attribute performance to "good scoring" vs. "good timing" vs. "good sizing."

**Why it happens:**
Trade execution naturally records price and quantity. But performance attribution needs the "decision context" -- why was this trade made? What scores supported it? What regime was active? This is metadata about the decision, not the execution. Developers build attribution assuming the scores can be recomputed retroactively, but scores change daily (new financial data, new price data, new sentiment), so yesterday's composite score cannot be reliably recomputed today.

**How to avoid:**
1. **Snapshot decision context at trade entry.** When a trade plan is approved, store: composite_score, fundamental_score, technical_score, sentiment_score, regime_type, strategy_weights, position_size_reason (Kelly fraction, ATR-based stop distance), and benchmark_price (SPY or relevant index).
2. **Immutable trade event log.** Create an append-only log of `TradeEntryEvent` and `TradeExitEvent` domain events with full context. This log is the source of truth for attribution -- never recompute from current data.
3. **Benchmark tracking.** Start recording SPY (or chosen benchmark) daily returns from day one. Attribution formulas (Brinson-Fachler, etc.) require benchmark returns over the exact same period as each trade. Missing benchmark data makes sector allocation attribution impossible.
4. **Design the attribution schema before implementing.** The 4-level P&L decomposition mentioned in PROJECT.md (scoring, regime, sizing, execution) requires specific data at each level. Define the data requirements first, then ensure every upstream component (scoring, regime, sizing, execution) emits the required fields.

**Warning signs:**
- Trade plan records do not contain the composite score at approval time
- No benchmark return data stored alongside trade data
- Attribution calculations use current scores instead of historical scores
- `self-improver` tries to optimize parameters but cannot explain what drove past performance
- Attribution sums do not equal total P&L (the residual is large because key components are missing)

**Phase to address:**
Performance Attribution phase -- but the "snapshot decision context" requirement must be implemented in the Pipeline Stabilization or Technical Scoring phase, because it requires modifying the trade execution pipeline. If you wait until the attribution phase to add context logging, you have no historical data to attribute.

---

### Pitfall 6: MACD Histogram Normalization Range Mismatch Across Stocks

**What goes wrong:**
The current `TechnicalScoringService._score_macd()` normalizes the MACD histogram from a hardcoded range of [-5, +5] to [0, 100]. This range was likely calibrated for US large-cap stocks trading at $50-500. But: (1) a $5 stock has a MACD histogram in the [-0.1, +0.1] range, making all scores cluster around 50 (neutral); (2) a $2000 stock (BRK.A) has histograms in the [-50, +50] range, making all scores extreme (0 or 100); (3) penny stocks and high-volatility names have wildly different ranges. The technical score becomes meaningless for any stock outside the assumed price range.

**Why it happens:**
The MACD histogram is price-denominated (it is the difference between two EMAs of the close price). Unlike RSI (always 0-100) or ADX (typically 0-50), MACD has no natural bounded range. The developer picks a "reasonable" normalization range based on a few test stocks and moves on. This works for a narrow stock universe but breaks silently when the universe expands.

**How to avoid:**
1. **Use percentage-based MACD.** Instead of raw MACD histogram value, use `histogram / close * 100` (percentage of price). This normalizes across price levels. A $5 stock and a $500 stock will have comparable percentage MACD values.
2. **Alternatively, use z-score normalization.** Compute the MACD histogram's rolling z-score over 252 days: `(current_histogram - mean(histogram_252d)) / std(histogram_252d)`. This normalizes each stock relative to its own history. Map z-score [-2, +2] to [0, 100].
3. **Test with diverse stocks.** Include in the test suite: a penny stock (<$5), a normal stock ($50-200), a high-price stock (>$1000), a high-volatility stock (TSLA-class), and a low-volatility stock (utility). Verify MACD scores are not all clustered at 50 or at extremes.

**Warning signs:**
- MACD sub-scores are almost always 50.0 for low-price stocks
- MACD sub-scores are almost always 0.0 or 100.0 for high-price stocks
- The standard deviation of MACD sub-scores across a 500-stock universe is very small (all scores compressed)
- Technical composite score has low discriminating power (stocks with very different momentum have similar scores)

**Phase to address:**
Technical Scoring phase -- fix the normalization before integrating into the composite. The fix is small (change `_score_macd()` to use percentage MACD) but must be done before any backtest or live scoring uses the result.

---

### Pitfall 7: Commercial API Billing Without Idempotent Request Tracking

**What goes wrong:**
Usage-based billing (e.g., $29/mo for 1000 API calls) requires accurate request counting. Without idempotent request tracking: (1) a client retry (network timeout, 504 gateway error) counts as two requests, overbilling the customer; (2) a server crash during request processing loses the count, underbilling; (3) concurrent requests from the same API key race against the usage counter, producing inconsistent counts; (4) the "requests remaining" endpoint returns stale data, causing clients to hit limits unexpectedly.

**Why it happens:**
Request counting looks trivial: increment a counter per API key per request. But production edge cases break simple counters. The existing system has no multi-user state management -- it is a single-user system. Adding usage tracking is the first multi-user, concurrent-access feature, and it introduces concurrency bugs that the codebase has never encountered.

**How to avoid:**
1. **Atomic usage increment.** Use SQLite's `UPDATE api_usage SET count = count + 1 WHERE api_key = ? AND period = ?` with a unique constraint on (api_key, period). This is atomic at the database level.
2. **Idempotency keys.** Require clients to send an `Idempotency-Key` header. Store completed request IDs. If a key is seen again, return the cached response without incrementing the usage counter.
3. **Pre-check rate limit middleware.** Before processing the request, check if the key has remaining quota. Reject with 429 before doing expensive computation (scoring a stock takes 1-3 seconds of DuckDB queries). This prevents wasted compute on over-quota requests.
4. **Monthly usage reset.** Use a `(api_key, year_month)` composite key for usage tracking. Reset is implicit: new month = new row = zero count.

**Warning signs:**
- Usage counts in the billing dashboard do not match server access logs
- Customers report being billed for more requests than they made
- Race condition in load testing: 100 concurrent requests from one key exceed the quota but are all processed
- No `429 Too Many Requests` response in the API -- over-quota requests just succeed

**Phase to address:**
Commercial API phase -- billing infrastructure must be designed before endpoints are public. This is business-critical: incorrect billing destroys customer trust immediately.

---

### Pitfall 8: Self-Improver Overfitting to Historical Regime Patterns

**What goes wrong:**
The self-improver optimizes parameters (indicator weights, scoring thresholds, regime-specific adjustments) based on historical performance. If it optimizes freely, it will find parameters perfectly tuned to past regimes -- e.g., "in the 2022-2023 data, ADX weight should be 0.35 and MACD weight should be 0.05." These parameters are overfitted to that specific market period and fail in new regimes. The system's live performance degrades over time as optimized parameters diverge from current market behavior.

**Why it happens:**
The system has 5 technical indicator weights, 3 composite strategy weights, regime-specific weight overrides for 4 regimes, scoring thresholds, and potentially more tunable parameters. With so many degrees of freedom and limited data (the system has been running for weeks/months, not decades), any optimization algorithm will find spurious patterns. This is the fundamental overfitting problem in quantitative finance, and it is more dangerous with automated self-improvement because the human sanity check is removed.

**How to avoid:**
1. **Constrain the parameter space.** Do not allow the self-improver to change more than +/- 20% from the research-validated defaults. The current weights (swing: 40/40/20 fundamental/technical/sentiment) are based on methodology research. The self-improver can adjust to 35/45/20 or 45/35/20, but not to 10/80/10.
2. **Walk-forward validation mandatory.** Any parameter change proposed by the self-improver must pass walk-forward validation: optimize on months 1-6, validate on months 7-9, test on months 10-12. If out-of-sample performance is worse than defaults, reject the change.
3. **Minimum sample size.** Do not optimize until the system has executed at least 50 trades across at least 2 distinct market regimes. Optimization on 10 trades in a bull market is meaningless.
4. **Human approval for parameter changes.** Self-improver proposes changes with evidence. Human approves. This matches the existing "human-in-the-loop" constraint.
5. **Version-controlled parameters.** Store every parameter change with timestamp, rationale, and out-of-sample metrics. Enable rollback to any previous parameter set.

**Warning signs:**
- Self-improver proposes extreme weights (e.g., sentiment weight = 0.05 or 0.50)
- Optimized parameters change dramatically month-over-month
- Out-of-sample performance is consistently worse than in-sample
- Self-improver "optimizes" by effectively removing a scoring axis (setting its weight near zero)
- Parameter changes always improve backtest results but not live results

**Phase to address:**
Self-Improver phase -- but the constraint infrastructure (parameter bounds, walk-forward validation, human approval workflow) should be designed during the Performance Attribution phase because attribution data feeds the self-improver.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Adding new scores to `core/` instead of `src/` | Avoids DDD wiring issues; code works immediately | Two parallel code paths; DDD migration becomes harder; adapters grow unwieldy | Never for v1.4 -- new features go through `src/` only |
| Hardcoded MACD/OBV normalization ranges | Quick to implement; works for tested stocks | Silent scoring errors for stocks outside the assumed price/volume range; discriminating power loss | Only for initial prototype; must be replaced with percentage-based or z-score normalization before production use |
| Sentiment score = 50 when no data source configured | System "works" without paid sentiment APIs | Composite score has a hidden constant bias; explainability chain is dishonest; users trust fake neutral scores | Only if the system explicitly marks sentiment as "not available" and excludes it from composite calculation |
| Single SQLite DB for both trading data and commercial API billing | Simple setup; one DB to manage | Lock contention between trading pipeline and API request processing; billing audit mixed with trading audit | Never for commercial API -- use separate databases |
| Skipping API authentication during development | Faster iteration; no auth token management in curl commands | Security shortcuts get shipped; "I'll add auth later" becomes tech debt; someone connects from outside localhost | Never -- even in dev, use a hardcoded dev API key |
| Computing attribution retroactively from current scores | No need to modify the trade execution pipeline | Attribution results are wrong because scores change daily; cannot accurately attribute past performance | Never -- snapshot decision context at trade entry time |

## Integration Gotchas

Common mistakes when connecting new features to the existing system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Technical indicators from `core/data/indicators.py` | Using raw indicator values (MACD histogram in absolute terms) directly as scores | Normalize to 0-100 using percentage-based or z-score methods in `TechnicalScoringService`; raw values vary by orders of magnitude across stocks |
| Sentiment data from external APIs (news, filings) | Calling external APIs synchronously during the scoring pipeline | Fetch sentiment data asynchronously in a separate data ingestion step; cache in SQLite/DuckDB; scoring pipeline reads from cache, never from external API directly |
| Commercial API on the same FastAPI app as the dashboard | Sharing the same `app.state.ctx` bootstrap context between personal dashboard and commercial API | Separate FastAPI applications with separate contexts; commercial API should not access personal portfolio/execution data |
| Regime-adjusted weights in composite scoring | Having the regime detector and the scoring engine depend on each other circularly (scorer needs regime to set weights; regime detector needs scores to classify) | Regime detection is independent: it uses only market data (VIX, yield curve, breadth). Scoring consumes the regime result. One-directional dependency only. |
| Performance attribution reading from live scoring database | Attribution queries scanning the same DuckDB tables that the live pipeline is writing to | Attribution reads from snapshot/archive tables, not from the live scoring tables; or run attribution during off-market hours |
| Self-improver modifying production parameters | Self-improver writes optimized parameters directly to the production config | Self-improver writes proposals to a staging area; human reviews; approved changes are applied via a separate "apply parameters" command |

## Performance Traps

Patterns that work at small scale but fail as the stock universe or feature count grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Computing all 5 technical indicators for all stocks sequentially | Pipeline takes 30+ minutes for 500 stocks; each stock fetches 756 days of OHLCV from yfinance (rate limited) | Batch-fetch OHLCV data first, then compute indicators in parallel; cache price data in DuckDB | > 100 stocks in universe |
| Sentiment API calls per stock during scoring pipeline | Rate limit exhaustion; pipeline hangs or errors; $100/mo+ in API costs | Aggregate sentiment data in a daily background job; scoring pipeline reads from local cache | > 50 stocks with sentiment data |
| Performance attribution scanning all trades for every report | Attribution query time grows linearly with trade history | Pre-compute monthly/quarterly attribution summaries; store aggregated results; full recomputation only on demand | > 500 historical trades |
| Commercial API scoring requests hitting DuckDB for each request | DuckDB single-writer lock causes request queuing; response times spike under concurrent load | Cache scoring results in Redis or SQLite with TTL; serve from cache for same-day requests; DuckDB updated only during pipeline runs | > 10 concurrent API requests |
| Loading full financial history for every stock during backtesting | Memory usage scales with (stocks x history length); 500 stocks x 10 years of daily data = large DataFrame | Use DuckDB's columnar storage for backtest data access; query only needed columns and date ranges; never load full history into pandas at once | > 200 stocks x 5 years |

## Security Mistakes

Domain-specific security issues for a commercial quantitative trading API.

| Mistake | Risk | Prevention |
|---------|------|------------|
| API key in URL query parameters instead of headers | API keys leak in access logs, browser history, referrer headers, CDN logs | Require `X-API-Key` header only; reject requests with key in query params; FastAPI middleware to check |
| No rate limiting per API key tier | A free-tier user sends 10,000 requests/minute; exhausts DuckDB connections; DoS on paying customers | Use `slowapi` with per-key limits: free = 10/min, basic = 60/min, pro = 300/min |
| Exposing internal score decomposition to free-tier users | Free-tier users get the same response as paid users; no incentive to upgrade | Tier-based response shaping: free tier gets composite score only; paid tier gets sub-scores, regime data, historical trends |
| Commercial API returns personal trading positions or portfolio data | Data leak; legal liability; user's personal financial data exposed via commercial API | Complete data isolation: commercial API has its own database/tables with only public scoring data; no access to portfolio, execution, or trade plan tables |
| No input sanitization on ticker symbols in API requests | SQL injection via malformed ticker like `AAPL'; DROP TABLE scores; --` | Already have `Symbol` VO validation (uppercase, max 10 chars); ensure all API inputs go through VO construction before any database query |
| Missing rate limit on login/API key generation endpoint | Brute force attacks on API key generation or validation endpoint | Rate limit the auth endpoint separately (3/min per IP); use time-constant comparison for key validation |

## UX Pitfalls

Common user experience mistakes in quantitative scoring APIs and trading dashboards.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Returning composite score without explanation | User gets "72.3" but cannot act on it -- does not know which axis is strong/weak | Always return sub-scores (fundamental, technical, sentiment) alongside composite; include top 3 reasons as text |
| Sentiment score showing as 50 without indicating data unavailability | User trusts a "neutral sentiment" assessment that is actually "no data" | Distinguish `50 (measured neutral)` from `N/A (no data)`; show confidence level |
| Performance attribution with too many categories | 15-category attribution is mathematically correct but unusable for decision-making | Start with 4 categories (alpha, sector, timing, sizing); offer drill-down for advanced users |
| Commercial API error messages that leak internal architecture | User gets `DuckDB connection error: /home/mqz/workspace/trading/data/scores.db` | Generic error messages: `"error": "scoring_unavailable", "retry_after": 60`; log details server-side |
| Dashboard showing stale scores without freshness indicator | User makes trading decisions based on yesterday's scores thinking they are current | Every score display includes "as of: 2026-03-14 09:30 ET" and staleness warning if > 24h old |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Technical scoring:** Indicators compute correctly -- verify that MACD scores are not all clustered at 50 for low-price stocks or all at extremes for high-price stocks (test with AAPL, F, BRK.A)
- [ ] **Technical scoring:** Backtesting uses technical scores -- verify no lookahead bias by checking that changing tomorrow's close does not change today's technical score
- [ ] **Sentiment scoring:** Sentiment API is "integrated" -- verify that actual external data flows in for at least one data source (not all stocks returning 50.0)
- [ ] **Composite scoring:** Weights sum to 1.0 -- verify that when sentiment is unavailable, the remaining weights are re-normalized (not summing to 0.80)
- [ ] **Commercial API:** Endpoints return data -- verify authentication is required (test with no API key; should get 401)
- [ ] **Commercial API:** Rate limiting configured -- verify it actually blocks (send 100 requests in 1 second; count 429 responses)
- [ ] **Commercial API:** Billing counts are accurate -- verify with a known number of requests that the usage counter matches
- [ ] **Performance attribution:** Attribution report generated -- verify that component attributions sum to total P&L (residual < 5%)
- [ ] **Performance attribution:** Decision context captured -- verify trade entry records contain the composite score, regime type, and strategy weights at the time of entry (not today's scores)
- [ ] **Self-improver:** Parameter optimization works -- verify it respects bounds (proposed weights are within +/- 20% of defaults)
- [ ] **Store unification:** All scoring data in consistent store -- verify no scoring queries cross between SQLite and DuckDB in the same workflow
- [ ] **Event bus:** Cross-context events work -- verify that publishing `ScoreUpdatedEvent` from scoring context triggers signal regeneration in signals context

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Lookahead bias in technical scores | HIGH | All historical technical scores must be recomputed with proper data cutoffs; backtest results invalidated and re-run; any live trades made based on biased scores need manual review; 3-5 day effort |
| Silent sentiment = 50 corruption | MEDIUM | Add confidence field to SentimentScore; recompute composite scores excluding fake sentiment; compare with and without sentiment to assess impact; 1-2 day effort |
| DDD wiring gaps blocking new features | MEDIUM | Fix one vertical slice end-to-end as a reference implementation; other features follow the same pattern; 2-3 day effort per context |
| Commercial API shipped without auth | HIGH | Add auth middleware; issue API keys to all existing users; breaking change requiring API key header; user communication needed; 3-5 day effort |
| Attribution with missing decision context | HIGH | Cannot recover historical context retroactively; must accept that early trades have incomplete attribution; implement context capture going forward; early attribution marked as "partial"; 1 day to implement, months to accumulate data |
| MACD normalization wrong for diverse stocks | LOW | Change `_score_macd()` to use percentage MACD; recompute all technical scores; 1 day effort |
| Overfitted self-improver parameters deployed | MEDIUM | Rollback to default parameters; review optimization constraints; add walk-forward validation; 1-2 day effort |
| Commercial API billing inaccurate | HIGH | Audit all request logs; compare with billing records; issue credits for overbilling; fix counting logic; communicate with affected customers; 2-3 day effort |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Lookahead bias (1) | Technical Scoring | Backtest with synthetic data: insert a known anomaly at date T+1; verify score at T is unchanged |
| Silent sentiment = 50 (2) | Sentiment Scoring | Query: `SELECT COUNT(*) FROM scores WHERE sentiment_score = 50.0` should be < 30% of scored stocks (with real data source active) |
| DDD wiring gaps (3) | Pipeline Stabilization (FIRST) | One vertical slice works end-to-end: CLI command -> application handler -> domain service -> infrastructure repo -> persistence -> query handler -> API response |
| API security (4) | Commercial API (FIRST task) | All endpoints return 401 without valid API key; 429 after rate limit exceeded; no Python traces in error responses |
| Attribution without context (5) | Pipeline Stabilization + Technical Scoring | Trade plan records include composite_score, regime_type, strategy_weights fields; verify with `SELECT * FROM trade_plans WHERE composite_score IS NULL` = 0 rows |
| MACD normalization (6) | Technical Scoring | Standard deviation of MACD sub-scores across 500-stock universe > 15 (not compressed) |
| Billing accuracy (7) | Commercial API | Load test: 1000 requests with known API key; usage counter = 1000 exactly |
| Self-improver overfitting (8) | Self-Improver | All proposed parameter changes within +/- 20% of defaults; out-of-sample Sharpe > 0.5 (not zero or negative) |

## Sources

- Project file `src/scoring/domain/value_objects.py` -- existing VO definitions, STRATEGY_WEIGHTS, SentimentScore default behavior
- Project file `src/scoring/domain/services.py` -- TechnicalScoringService with hardcoded MACD normalization [-5, +5]
- Project file `src/scoring/infrastructure/core_scoring_adapter.py` -- adapter pattern, TechnicalIndicatorAdapter
- Project file `core/scoring/sentiment.py` -- existing sentiment scoring with 50.0 default
- Project file `core/data/indicators.py` -- indicator implementations (RSI, MACD, MA, ADX, OBV)
- Project file `.planning/PROJECT.md` -- tech debt flags: "DDD wiring gaps," "scoring store mismatch"
- Project file `src/signals/infrastructure/duckdb_signal_store.py` -- DuckDB for signals (vs SQLite for scoring)
- Marcos Lopez de Prado, "Advances in Financial Machine Learning" (2018) -- lookahead bias, walk-forward validation, overfitting in strategy optimization (HIGH confidence, foundational quant finance text)
- FastAPI security documentation -- API key authentication patterns (HIGH confidence)
- Brinson-Fachler attribution model -- standard method for multi-factor performance decomposition (HIGH confidence, widely adopted)
- DuckDB concurrency model -- single-writer limitation relevant to commercial API scaling (HIGH confidence, from DuckDB docs)

---
*Pitfalls research for: Technical scoring, sentiment analysis, commercial API, and performance attribution added to existing quantitative trading system*
*Researched: 2026-03-14*
