# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-12
**Phases:** 4 | **Plans:** 12 | **Commits:** 106

### What Was Built
- Data ingestion pipeline with DuckDB/SQLite dual-DB and SEC filing point-in-time awareness
- Fundamental scoring (F/Z/M/G-Score) with safety gates and composite 0-100 scoring
- Valuation ensemble (DCF + EPV + Relative) with margin of safety
- Signal generation with BUY/HOLD/SELL reasoning traces
- Risk management with Fractional Kelly sizing and 3-tier drawdown defense
- Trade execution with Alpaca paper trading, human approval CLI, dashboard, and monitoring

### What Worked
- Coarse 4-phase roadmap with strict dependency chain kept execution focused
- Adapter pattern wrapping existing core/ math prevented rewrites and saved significant time
- Frozen dataclass VO pattern with _validate() was consistent and easy to replicate across all domains
- DI for all infrastructure made testing fast and reliable (352+ tests passing)
- YOLO mode with quality profile balanced speed and verification

### What Was Inefficient
- DuckDB vs SQLite store decisions not aligned upfront -- scoring writes to SQLite but screener queries DuckDB, causing integration gaps
- CLI commands added late (Phase 4) without verifying they wire all the way back to Phase 1 entry points
- Domain events defined in all contexts but never wired to EventBus -- async event architecture is scaffolding only
- G-Score and regime adjustment implemented in domain but handler wiring incomplete

### Patterns Established
- Frozen dataclass VOs with `_validate()` and `__post_init__` for domain value objects
- `kw_only=True` for domain event dataclass inheritance
- Local imports inside CLI function bodies (lazy loading pattern)
- alpaca-py imports inside methods only (avoid SDK init on import)
- CoreXxxAdapter pattern: thin adapter wrapping core/ functions, no math rewriting
- DuckDB INSERT OR REPLACE for upsert semantics

### Key Lessons
1. **Wire stores end-to-end before building consumers** — The DuckDB/SQLite mismatch was avoidable if we'd verified the screener's data source matched the scoring store in Phase 2
2. **Add CLI surface incrementally per phase** — Waiting until Phase 4 to add CLI commands left integration gaps. Each phase should expose its capabilities through CLI immediately
3. **Test cross-context integration, not just unit** — 352 passing tests didn't catch that the screener queries a non-existent table. Integration tests spanning bounded contexts would have caught this
4. **Define event contracts early, publish immediately** — Defining events without publishing them creates dead code. Events should be published as soon as they're defined
5. **Adapter pattern is excellent for incremental DDD migration** — Wrapping core/ math with thin adapters preserved correctness while adding DDD structure

### Cost Observations
- Model mix: ~80% sonnet (plan execution), ~15% opus (orchestration/review), ~5% haiku (research/analysis)
- Execution velocity: ~5.5 min/plan average
- Total execution time: ~1.1 hours for 12 plans
- Notable: YOLO mode + coarse granularity + parallelization = very efficient

---

## Milestone: v1.1 — Stabilization & Expansion

**Shipped:** 2026-03-12
**Phases:** 7 | **Plans:** 17

### What Was Built
- Tech debt fixes for DuckDB/SQLite store alignment
- Live data pipeline with EODHD API and Korean market data
- Technical scoring engine (RSI, MACD, MA, ATR, OBV, ADX)
- Market regime detection (Bull/Bear/Sideways/Crisis via VIX, 200MA, ADX, yield curve)
- Multi-strategy signal fusion (CAN SLIM, Magic Formula, Dual Momentum, Trend Following)
- Korean broker integration (KIS API)
- Commercial FastAPI REST API (QuantScore, RegimeRadar, SignalFusion)

### Key Lessons
1. Fix tech debt immediately after MVP — store mismatches from v1.0 caused cascading issues
2. Commercial API and personal system share the same scoring engine — "one code, two products" works

---

## Milestone: v1.2 — Production Trading & Dashboard

**Shipped:** 2026-03-14
**Phases:** 9 | **Plans:** 20

### What Was Built
- Safety infrastructure (kill switch, cooldown, circuit breaker)
- Automated pipeline with APScheduler and market calendar
- Strategy and budget approval workflow
- Live trading activation (Alpaca paper → live)
- Web dashboard (HTMX + Jinja2) with 5 pages
- SSE real-time event wiring
- Drawdown defense wiring (3-tier auto-suspension)
- Dashboard/CLI polish and data accuracy improvements
- CI/test debt cleanup

### Key Lessons
1. Safety infrastructure should be the first production feature, not an afterthought
2. HTMX+Jinja2 is fast to build but limited for data-dense financial UIs — led to v1.3 rewrite

---

## Milestone: v1.3 — Bloomberg Dashboard

**Shipped:** 2026-03-14
**Phases:** 5 | **Plans:** 9 | **Commits:** 40

### What Was Built
- Next.js 16 + FastAPI BFF proxy architecture
- Bloomberg OKLCH dark theme design system with shadcn/ui
- 4-page professional dashboard (Overview, Signals, Risk, Pipeline)
- TradingView Lightweight Charts equity curve with regime overlay
- SSE real-time updates via EventSource-to-TanStack-Query mapping
- Legacy HTMX/Jinja2/Plotly complete removal

### What Worked
- BFF proxy via next.config.ts rewrites: clean separation, no CORS issues, SSE works without buffering
- CSS-only visualizations (conic-gradient gauge, donut chart): zero additional dependencies
- TanStack Query for server state: automatic cache invalidation via SSE integration
- Biome 2.x as single lint+format tool: faster than ESLint+Prettier combo
- One-day delivery for 5 phases: tight scope + existing backend + component reuse

### What Was Inefficient
- shadcn/ui required manual Biome compatibility fixes (tailwindDirectives config)
- TradingView chart required useLayoutEffect workaround for memory leak prevention
- Phase 22 still needs human visual verification for 4 Bloomberg theme rendering items

### Patterns Established
- Next.js rewrites for BFF proxy to Python backend (no Route Handlers for SSE)
- OKLCH color space for theme tokens (perceptually uniform)
- Column definitions declared outside React components to avoid recreation
- CSS conic-gradient for semicircle gauges and donut charts
- EventSource → TanStack Query invalidation mapping pattern

### Key Lessons
1. **BFF proxy > direct API calls** — Next.js rewrites handle CORS, SSE buffering, and auth in one place
2. **CSS-only visualizations scale well** — No need for chart libraries for gauges and simple charts
3. **Keep design system tokens in CSS variables** — Easier to maintain than JS constants
4. **SSE > WebSocket for server-push-only** — Simpler, auto-reconnects, works through proxies
5. **Scope tightly for one-day milestones** — 9 plans across 5 phases is the sweet spot

### Cost Observations
- Model mix: ~70% sonnet (execution), ~20% opus (orchestration), ~10% haiku (research)
- Execution velocity: ~3.4 min/plan average (faster than v1.0's 5.5 min)
- Total execution time: ~31 minutes for 9 plans
- Notable: Reusing existing FastAPI backend + tight scoping enabled single-day delivery

---

## Milestone: v1.4 — Full Stack Trading Platform

**Shipped:** 2026-03-18
**Phases:** 4 (26-29) | **Plans:** 9 | **Commits:** 151

### What Was Built
- Pipeline stabilized: DDD event bus live, unified SQLite/DuckDB sync, real current_price + target_price from adapters
- 3-axis scoring: technical (RSI/MACD ATR-norm/MA/ADX/OBV) + sentiment (Alpaca+VADER + yfinance ×3) with SentimentConfidence
- Commercial API: QuantScore/RegimeRadar/SignalFusion with sub-score breakdowns, JWT, rate limiting, legal disclaimer
- Dashboard enhanced: expandable F/T/S rows, regime probability bars, Performance Attribution page, 5-link nav
- Performance DDD context: Brinson-Fachler, per-axis IC with Spearman correlation, Kelly efficiency, DuckDB trade/proposal stores
- Self-improver DDD: 50-trade threshold, walk-forward before proposals, propose-then-approve Dashboard workflow

### What Worked
- MACD ATR-scaled normalization: dynamic range prevents saturation across all price scales
- SentimentConfidence enum + weight renormalization: graceful degradation when data unavailable
- BFF proxy split (performance page vs. other dashboard pages): natural boundary matches deployment topology
- Coarse 4-phase structure with strict dependency chain: clean execution, minimal rework
- 148 tests passing (scoring module only) after Phase 27: strong regression lock

### What Was Inefficient
- Phase 26 VERIFICATION.md never written — carried as tech debt; integration checker had to confirm pipeline correctness at audit time
- signal_direction not propagated through Position lifecycle — IC calculation broken; caught at audit but not at phase execution
- proposal_gen_handler wired in bootstrap but no trigger path defined — SELF-02 gap shipped without detection
- sentiment_confidence not persisted to SQLite scored_symbols table — surfaced at audit integration check, not during phase execution
- 3 of 4 v1.4 audit gaps were integration issues (cross-module data flow), not unit-level bugs

### Patterns Established
- `WalkForwardAdapter` synthetic OHLCV conversion: adapter boundary converts trade_returns to OHLCV for existing backtest engine
- Dashboard BFF with two different env var patterns (`BACKEND_URL` vs `NEXT_PUBLIC_API_URL`) — document in `.env.example`
- Performance bounded context as pure read-model fed by domain events — event-driven persistence pattern
- Propose-then-approve: `DuckDBProposalRepository` + Dashboard mutation flow as approval UI

### Key Lessons
1. **Integration gaps are invisible at the unit level** — need cross-phase integration checks before declaring phases done
2. **Data flow must be traced end-to-end** — signal_direction lifecycle gap (open → close → persist → IC) wasn't caught because each piece tested in isolation
3. **Bootstrap wiring needs explicit integration tests** — handler stored in ctx but never called is a systemic risk when only unit tests exist
4. **Audit identifies gaps audit cannot fix** — 3 clear next-milestone items from v1.4 audit: signal_direction, proposal trigger, sentiment_confidence column
5. **Coarse 4-phase structure remains optimal** — each phase ships a complete vertical slice; dependent phases don't start until previous verified

### Cost Observations
- Model mix: ~65% sonnet (execution), ~25% opus (orchestration + audit), ~10% haiku
- Execution velocity: ~5 min/plan average (slower than v1.3 due to larger plans)
- Total execution time: ~45 minutes for 9 plans + audit
- Notable: Integration checker agent at audit time identified 4 actionable gaps missed during phase execution

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Commits | Phases | Plans | Avg min/plan | Key Change |
|-----------|---------|--------|-------|-------------|------------|
| v1.0 | 106 | 4 | 12 | 5.5 | Initial DDD architecture with adapter pattern |
| v1.1 | ~80 | 7 | 17 | ~4.5 | Tech debt fix + expansion to 7 contexts |
| v1.2 | ~90 | 9 | 20 | ~4.0 | Production safety + HTMX dashboard |
| v1.3 | 40 | 5 | 9 | 3.4 | React dashboard + legacy removal |
| v1.4 | 151 | 4 | 9 | ~5.0 | 3-axis scoring + commercial API + performance attribution |

### Cumulative Quality

| Milestone | Tests | Python LOC | TS LOC | Tech Debt |
|-----------|-------|-----------|--------|-----------|
| v1.0 | 352+ | 20,357 | 0 | 16 items |
| v1.1 | 352+ | ~25K | 0 | reduced |
| v1.2 | 352+ | ~28K | 0 | reduced |
| v1.3 | 352+ | 13,008 | 2,430 | 3 items |
| v1.4 | 352++ | ~180K | ~5K | 5 items (3 critical, 2 cosmetic) |

### Top Lessons (Verified Across Milestones)

1. Wire data stores end-to-end before building consumers (v1.0)
2. Adapter pattern is excellent for incremental DDD migration (v1.0)
3. Safety infrastructure first for production features (v1.2)
4. BFF proxy pattern cleanly separates frontend and backend concerns (v1.3)
5. CSS-only visualizations reduce dependency count without sacrificing quality (v1.3)
6. Tight scope enables single-day milestone delivery (v1.3)
7. Cross-phase integration gaps are invisible at unit test level — run integration checker before declaring phases done (v1.4)
8. Data lifecycle must be traced end-to-end at design time — field gaps (signal_direction) surface late if only tested in isolation (v1.4)
9. Bootstrap ctx entries need explicit trigger paths — a handler that is wired but never called is silent dead code (v1.4)
