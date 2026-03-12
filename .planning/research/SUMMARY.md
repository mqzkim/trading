# Project Research Summary

**Project:** Intrinsic Alpha Trader -- v1.1 Stabilization & Expansion
**Domain:** Quantitative mid-term trading system (US + Korean equities, commercial API)
**Researched:** 2026-03-12
**Confidence:** HIGH

## Executive Summary

Milestone v1.1 expands the Intrinsic Alpha Trader across three axes: technical depth (technical scoring engine, HMM-based regime detection, multi-strategy signal fusion), geographic breadth (Korean market via KOSPI/KOSDAQ), and commercial viability (FastAPI REST API with tiered access). The existing v1.0 codebase already has functional implementations in `core/` and partial DDD skeletons in `src/` for four bounded contexts (Scoring, Signals, Regime, Portfolio). The critical architectural task for v1.1 is not building from scratch but converging the dual `core/` + `src/` structure through a shared event bus, while simultaneously addressing 16 tech debt items inherited from v1.0. The research confirms that the Python ecosystem has mature, well-verified libraries for every new capability -- hmmlearn for HMM regime detection, pykrx for Korean market data, python-kis for Korean broker integration, and the existing FastAPI stack needs only slowapi + PyJWT + passlib for production hardening. No speculative or unproven technology is required.

The recommended approach is to lead with tech debt resolution and infrastructure unification (event bus, composition root, database factory) before adding new features. This is not a cautious preference -- it is an architectural dependency. The existing `core/orchestrator.py` is a God Orchestrator anti-pattern that directly imports from every module, making it impossible to add new bounded contexts (Valuation, Monitoring, Korean market adapters) without further entangling the dependency graph. Building the synchronous event bus first (under 30 lines of code per ARCHITECTURE.md) and wiring existing contexts to it unlocks clean integration of all v1.1 features. Technical scoring requires no new dependencies -- all RSI, MACD, MA, ADX, and OBV indicators are already implemented in `core/data/indicators.py` using pure pandas/numpy. The work is DDD integration and composite scoring aggregation, not computation.

The top risks are: (1) look-ahead bias in fundamental data invalidating backtests if filing dates are not tracked from the data layer, (2) DCF valuation brittleness where terminal value can dominate 85%+ of the calculation producing nonsensical intrinsic values, (3) value trap blindness where high Piotroski F-Score stocks in structural decline generate repeated losing positions, and (4) Korean market data reliability via pykrx which scrapes KRX directly without API guarantees. The first three are addressed by the existing PITFALLS.md prevention strategies. The fourth requires robust data validation matching the same patterns already needed for yfinance.

## Key Findings

### Recommended Stack

The v1.1 stack is conservative and well-vetted. Only 5 new PyPI packages are needed as core dependencies, plus 2 existing optional ML dependencies that need installation.

**New core dependencies (5 packages):**
- **pykrx** (>=1.2.4): Korean market OHLCV + fundamentals from KRX directly -- provides PER/PBR/DIV that FinanceDataReader lacks
- **python-kis** (>=2.1.6): Korean broker API (orders, balance, streaming) -- only PyPI-packaged KIS wrapper with regular releases
- **slowapi** (>=0.1.9): FastAPI rate limiting -- battle-tested, in-memory storage sufficient for single-instance
- **PyJWT** (>=2.9.0): JWT authentication for API tier management -- replaces abandoned python-jose per FastAPI team recommendation
- **passlib[bcrypt]** (>=1.7.4): API key hashing -- industry standard

**Existing dependencies to install (2 packages, already in pyproject.toml):**
- **hmmlearn** (>=0.3.3, bump from >=0.3): GaussianHMM for probabilistic regime detection -- supplements existing rule-based classifier
- **scikit-learn** (>=1.5.0): Feature preprocessing for HMM + GaussianMixture baseline

**Critical stack decision -- no new technical analysis library needed.** All RSI, MACD, MA(50/200), ADX, OBV, and ATR indicators are already implemented with correct algorithms (Wilder's smoothing for RSI, proper DM+/DM- for ADX, EMA-based MACD) in `core/data/indicators.py`. Adding pandas-ta or TA-Lib would duplicate working code.

**Explicitly deferred:** Redis (overkill for single-instance), Stripe (premature before demand validation), Celery (no background tasks needed), pomegranate (heavier HMM library than hmmlearn).

### Expected Features

**v1.1 scope -- must deliver:**
- Tech debt resolution (16 items from v1.0 milestone audit)
- Live data pipeline validation with quality checks
- Technical scoring engine integrated into DDD composite scoring (0-100 scale)
- HMM-based market regime detection (Bull/Bear/Sideways/Crisis) supplementing rule-based classifier
- Multi-strategy signal fusion (CAN SLIM, Magic Formula, Dual Momentum, Trend Following) with regime-weighted aggregation
- Korean market support with pykrx data adapter + python-kis broker adapter
- Commercial FastAPI REST API: QuantScore ($29-99/mo), RegimeRadar ($19-49/mo), SignalFusion ($49-199/mo)

**Differentiators this milestone adds:**
- Regime-adaptive strategy weighting -- no retail tool does this
- Deterministic multi-methodology consensus vs. the LLM-dependent approach of ai-hedge-fund (43K+ stars)
- Korean market as the first non-US expansion (KOSPI/KOSDAQ with KRX fundamentals)
- Commercial API with tiered rate limiting and JWT authentication

**Defer to v1.2+:**
- Redis-based distributed caching (only when scaling to multi-instance)
- Stripe payment integration (validate demand first)
- Web GUI dashboard (CLI + API sufficient for v1.1)
- SEC filing NLP analysis
- Options hedging

### Architecture Approach

The architecture follows DDD with 7-8 bounded contexts communicating via a synchronous in-process event bus (Cosmic Python pattern). The highest-priority infrastructure gap is the missing event bus and composition root -- without these, the God Orchestrator in `core/orchestrator.py` forces direct imports across all contexts. The dual-database strategy (DuckDB for time-series analytics, SQLite for operational state) is confirmed as correct for both US and Korean data pipelines. Korean market adapters integrate at the infrastructure layer only, implementing the same `IMarketDataRepository` and `IBrokerRepository` interfaces as the existing US adapters.

**Major components and their v1.1 status:**

1. **Shared Infrastructure** (event bus, db factory, bootstrap) -- MISSING, highest priority to build
2. **Data Ingest Context** -- EXISTS in core/, needs DDD wrapping + Korean adapter
3. **Regime Context** -- EXISTS in src/regime/ + core/regime/, needs event bus wiring + HMM addition
4. **Scoring Context** -- EXISTS in src/scoring/ + core/scoring/, needs technical score integration
5. **Valuation Context** -- PARTIAL from v1.0, needs ensemble completion
6. **Signals Context** -- EXISTS in src/signals/, needs multi-strategy consensus + valuation gap
7. **Portfolio/Risk Context** -- EXISTS in src/portfolio/, needs event bus wiring
8. **Execution Context** -- EXISTS in personal/execution/, needs DDD migration
9. **Commercial API** -- EXISTS in commercial/api/, needs rate limiting + JWT + tier management

### Critical Pitfalls

The PITFALLS.md identifies 15 distinct pitfalls (6 Critical, 4 High, 3 Medium, 2 Low). The top 5 most relevant to v1.1:

1. **Look-ahead bias in fundamental data** -- Store `filing_date` alongside every financial data point. Assertion layer must reject backtest trades using future data. This affects both US and Korean markets. Recovery cost is HIGH (full data layer rebuild + all backtests invalidated).

2. **Value trap blindness in scoring** -- Piotroski F-Score is backward-looking and does not catch structural decline. Prevention: momentum overlay (price above 200-day MA), sector-adjusted scoring, Z''-Score variant for non-manufacturing companies. Directly relevant to the technical scoring engine being built in v1.1.

3. **DCF valuation model brittleness** -- 1% WACC change shifts valuation 10-15%; terminal value is 60-85% of total DCF. Prevention: cap terminal value contribution at 85%, use ensemble weighting with confidence bands, present ranges not point estimates. The v1.1 valuation work must implement these guards.

4. **Kelly criterion blow-up risk** -- Estimation errors in win rate cause Quarter Kelly to still oversize. Prevention: hard-cap 5% per position (stricter than the 8% in CLAUDE.md), correlation adjustment, drawdown tiers override Kelly. Must be enforced in the Portfolio context.

5. **Data source fragility (yfinance + pykrx)** -- Both yfinance and pykrx are unofficial scrapers without SLA. Prevention: data validation layer, local caching in DuckDB, fallback sources, pinned versions. pykrx inherits the same fragility class as yfinance -- treat identically.

## Implications for Roadmap

Based on combined research, the v1.1 milestone should be structured in 7 phases. The ordering follows the critical dependency chain identified in ARCHITECTURE.md and maps pitfall prevention to the earliest possible phase.

### Phase 1: Tech Debt Resolution + Infrastructure Foundation
**Rationale:** The 16 tech debt items from v1.0 and the missing shared infrastructure (event bus, composition root, db factory) are blocking dependencies for every subsequent phase. Building the event bus eliminates the God Orchestrator anti-pattern and makes clean feature addition possible. This is the lowest-risk, highest-leverage work.
**Delivers:** SyncEventBus, DB connection factory, bootstrap composition root, existing 4 contexts wired to event bus, tech debt items resolved.
**Addresses:** Tech debt resolution (16 items), shared infrastructure gap
**Avoids:** God Orchestrator anti-pattern (ARCHITECTURE.md), DB concurrency issues (Pitfall 11)
**Stack:** No new dependencies. Pure Python infrastructure.

### Phase 2: Live Data Pipeline Validation + Korean Data Adapter
**Rationale:** Data integrity is the foundation. PITFALLS.md identifies 4 of 15 pitfalls in the data layer alone (look-ahead bias, survivorship bias, data source fragility, XBRL incompleteness). Korean market data adapter reuses the same infrastructure and validation patterns. Doing both data pipelines together avoids duplicating validation logic.
**Delivers:** Validated live data pipeline with quality checks, pykrx Korean market adapter implementing IMarketDataRepository, data validation layer for both US and KR data.
**Addresses:** Live data pipeline validation, Korean market data support
**Avoids:** Look-ahead bias (Pitfall 1), survivorship bias (Pitfall 2), data source fragility (Pitfall 7), XBRL incompleteness (Pitfall 12)
**Stack:** pykrx (>=1.2.4)

### Phase 3: Technical Scoring Engine + Composite Integration
**Rationale:** Technical indicators already exist in `core/data/indicators.py`. The work is integrating them into the DDD scoring context and adding technical scores to the composite alongside fundamental scores. This must precede signal fusion since signals consume composite scores.
**Delivers:** Technical scoring (RSI, MACD, MA, ADX, OBV) integrated into DDD scoring context, composite score combining fundamental + technical + sentiment sub-scores, sector-normalized scoring.
**Addresses:** Technical scoring engine, composite scoring integration
**Avoids:** Value trap blindness (Pitfall 3) via momentum overlay from technical indicators
**Stack:** No new dependencies. Existing pandas/numpy implementations.

### Phase 4: Market Regime Detection (HMM)
**Rationale:** Regime detection feeds into signal weighting (Phase 5) and is an independent bounded context that only depends on data pipeline (Phase 2). HMM supplements the existing rule-based classifier. This phase installs and integrates the ML optional dependencies.
**Delivers:** GaussianHMM(n_components=3) for Bull/Bear/Transition detection, dual classifier (rule-based deterministic + HMM probabilistic), regime transition probabilities feeding into weight adjustment.
**Addresses:** Market regime detection (Bull/Bear/Sideways/Crisis)
**Avoids:** Regime blindness (Pitfall 9) -- models trained on single market state
**Stack:** hmmlearn (>=0.3.3), scikit-learn (>=1.5.0)

### Phase 5: Multi-Strategy Signal Fusion
**Rationale:** Depends on composite scoring (Phase 3) and regime detection (Phase 4) for regime-weighted aggregation. The four strategies (CAN SLIM, Magic Formula, Dual Momentum, Trend Following) already have partial implementations in `core/signals/`. Integration with valuation gap from the Valuation context is the key enhancement.
**Delivers:** 4-strategy consensus signal engine, regime-weighted strategy aggregation, 3/4 agreement threshold for strong signals, valuation gap integration.
**Addresses:** Multi-strategy signal fusion, regime-adaptive weighting
**Avoids:** Backtesting overfitting (Pitfall 6) by limiting free parameters, regime blindness (Pitfall 9)
**Stack:** No new dependencies.

### Phase 6: Korean Broker Integration
**Rationale:** Data adapter (Phase 2) must be stable before adding the broker adapter. python-kis requires KIS developer account registration which may have lead time. Separate from data phase to isolate risk.
**Delivers:** python-kis broker adapter implementing IBrokerRepository, paper trading support for Korean market, environment isolation (KIS vs Alpaca credentials).
**Addresses:** Korean market support (execution side)
**Avoids:** Paper-to-live gap (Pitfall 8), operational kill switch absence (Pitfall 10)
**Stack:** python-kis (>=2.1.6)

### Phase 7: Commercial FastAPI REST API
**Rationale:** The API is a presentation layer that wraps the analysis engine. All scoring, regime, and signal contexts must be complete and stable before exposing them commercially. Rate limiting, JWT authentication, and tier management are the new additions to the existing FastAPI skeleton.
**Delivers:** QuantScore API endpoint, RegimeRadar API endpoint, SignalFusion API endpoint, JWT-based tier access (free/basic/pro), rate limiting per tier, API key management.
**Addresses:** Commercial FastAPI REST API (3 products)
**Avoids:** Alert fatigue (Pitfall 14) via rate limiting, precision fallacy (Pitfall 15) via range-based responses
**Stack:** slowapi (>=0.1.9), PyJWT (>=2.9.0), passlib[bcrypt] (>=1.7.4)

### Phase Ordering Rationale

- **Phase 1 first** because the event bus and composition root are prerequisites for clean integration of every subsequent feature. Without them, each new bounded context deepens the God Orchestrator coupling.
- **Phase 2 before 3-5** because scoring, regime detection, and signal fusion all consume data. Garbage data produces garbage signals regardless of algorithm quality.
- **Phases 3 and 4 can partially overlap** since they depend only on the data pipeline (Phase 2), not on each other. However, Phase 5 requires both to be complete.
- **Phase 6 after Phase 2** because the Korean broker adapter depends on the Korean data adapter being stable and validated.
- **Phase 7 last** because the commercial API is a thin wrapper over the analysis engine. Exposing unstable or incomplete analysis capabilities commercially would damage product credibility.
- **Tech debt upfront** rather than interleaved because the 16 items from v1.0 include structural issues (missing event bus, inconsistent error handling, incomplete DDD migration) that compound in cost if deferred further.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Korean Data):** pykrx data schema mapping to existing pipeline, KRX-specific fundamentals field naming (PER vs P/E, PBR vs P/B), KRX trading calendar holidays
- **Phase 4 (Regime Detection):** HMM hyperparameters (n_components, covariance_type), feature selection for GaussianHMM input, training window size, regime state labeling methodology
- **Phase 6 (Korean Broker):** KIS API developer registration process, API documentation is Korean-only, paper trading mode availability and limitations
- **Phase 7 (Commercial API):** Rate limit tier design, API key lifecycle management, legal disclaimers for financial data products

Phases with standard patterns (skip deeper research):
- **Phase 1 (Tech Debt + Infrastructure):** Event bus is <30 lines of standard Python. Composition root is standard DI wiring. Tech debt items are well-scoped from v1.0 audit.
- **Phase 3 (Technical Scoring):** Indicators already implemented. Integration is standard DDD pattern (wrap existing code as infrastructure adapter).
- **Phase 5 (Signal Fusion):** 4-strategy consensus pattern is well-documented. Regime weighting is a multiplication of existing weights.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All 7 new/updated packages verified on PyPI (2026-03-12). hmmlearn, pykrx, slowapi, PyJWT are mature with active maintenance. python-kis is the only MEDIUM-confidence package (Korean-only docs, community-maintained). |
| Features | HIGH | v1.1 scope is well-defined. Table stakes for each feature area validated against competitors. Korean market is the only expansion with uncertainty around KIS broker API access requirements. |
| Architecture | HIGH | DDD patterns proven in v1.0. Event bus design follows Cosmic Python (authoritative reference). Dual-database strategy validated. Korean adapters follow identical interface patterns as US adapters. |
| Pitfalls | HIGH | 15 pitfalls identified from 30+ authoritative sources. 6 critical pitfalls have specific prevention strategies with verification criteria. Pitfall-to-phase mapping ensures prevention is built into the schedule. |

**Overall confidence:** HIGH

### Gaps to Address

- **python-kis KIS developer registration:** Requires Korean brokerage account. Unclear if international users can register. Must verify access before committing to Phase 6 timeline. Fallback: defer Korean execution to v1.2 if registration is blocked, keep data-only Korean support.
- **pykrx KOSDAQ small-cap coverage:** pykrx scrapes KRX directly, but KOSDAQ small-caps may have sparse fundamental data. Need empirical validation during Phase 2 with a sample of 50+ KOSDAQ tickers.
- **HMM regime state labeling:** GaussianHMM outputs numbered states (0, 1, 2), not labeled regimes (Bull, Bear, Transition). Mapping hidden states to meaningful regime labels requires domain expertise. Validate against historical VIX regimes during Phase 4.
- **Commercial API legal disclaimers:** Financial data API products require "not investment advice" disclaimers. Exact legal language needs review. The system correctly separates "information products" (scores, data, statistics -- commercial) from "investment recommendations" (buy/sell with position sizing -- personal only).
- **Valuation ensemble weights for Korean stocks:** DCF/EPV/relative weights (40/35/25) calibrated for US equities. Korean market may have different dynamics (chaebol structures, different accounting norms). Needs validation during Phase 2-3.
- **Rate limiting tier boundaries:** slowapi in-memory storage resets on server restart. Acceptable for v1.1 single-instance, but tier abuse tracking (free tier users creating multiple accounts) needs a persistence strategy for v1.2.

## Sources

### Primary (HIGH confidence)
- [Cosmic Python -- Events and Message Bus](https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html) -- Event bus architecture pattern
- [CFA Level 2 -- Problems in Backtesting](https://analystprep.com/study-notes/cfa-level-2/problems-in-backtesting/) -- Look-ahead bias, data snooping
- [Alpaca Paper Trading Docs](https://docs.alpaca.markets/docs/paper-trading) -- Paper trading limitations
- [Statistical Overfitting -- Bailey et al.](https://sdm.lbl.gov/oapapers/ssrn-id2507040-bailey.pdf) -- Deflated Sharpe Ratio
- [Avoiding Value Traps -- Research Affiliates](https://www.researchaffiliates.com/publications/articles/1013-avoiding-value-traps) -- Momentum overlay strategy
- [Point-in-Time Data -- FactSet](https://insight.factset.com/hubfs/Resources%20Section/White%20Papers/ID11996_point_in_time.pdf) -- Filing date tracking
- [Knight Capital Disaster](https://soundofdevelopment.substack.com/p/the-knight-capital-disaster-how-a) -- Kill switch necessity
- [Kelly Criterion -- arXiv (2025)](https://arxiv.org/html/2508.18868v1) -- Estimation risk in Kelly sizing

### Secondary (MEDIUM confidence)
- [pykrx PyPI](https://pypi.org/project/pykrx/) -- Korean market data library versions
- [python-kis PyPI](https://pypi.org/project/python-kis/) -- Korean broker API library
- [slowapi GitHub](https://github.com/laurentS/slowapi) -- Rate limiting for FastAPI
- [edgartools XBRL mappings](https://www.edgartools.io/i-learnt-xbrl-mappings-from-32-000-sec-filings/) -- XBRL tag coverage data
- [DCF Common Errors -- Wall Street Prep](https://www.wallstreetprep.com/knowledge/common-errors-in-dcf-models/) -- Terminal value sensitivity
- [DuckDB vs SQLite (Jan 2026)](https://www.analyticsvidhya.com/blog/2026/01/duckdb-vs-sqlite/) -- Dual database rationale

### Tertiary (needs validation)
- **python-kis paper trading mode:** Documented but not verified through hands-on testing. Must confirm during Phase 6 planning.
- **pykrx KOSDAQ fundamental coverage:** Claimed to cover PER/PBR/DIV but small-cap coverage depth unknown. Validate empirically.

---
*Research completed: 2026-03-12*
*Ready for roadmap: yes*
