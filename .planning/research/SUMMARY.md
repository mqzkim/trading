# Project Research Summary

**Project:** Intrinsic Alpha Trader v1.4 -- Full Stack Trading Platform
**Domain:** Quantitative trading system (technical scoring, sentiment analysis, commercial REST API, performance attribution)
**Researched:** 2026-03-14
**Confidence:** HIGH

## Executive Summary

v1.4 extends an already-operational quantitative trading system (v1.3 delivered a Bloomberg-style dashboard, fundamental scoring, signal generation, risk management, and Alpaca execution) by filling two critical gaps in the composite scoring pipeline -- technical and sentiment axes that are currently placeholders -- then monetizing the engine through three commercial REST API products, and closing the feedback loop with performance attribution. The existing DDD architecture with 10 bounded contexts, event bus, and dual-store (SQLite + DuckDB) provides a solid foundation, but known tech debt (DDD wiring gaps, scoring store mismatch, adapter bottlenecks) must be resolved before new contexts are added.

The recommended approach is conservative and dependency-ordered: stabilize the pipeline and unify stores first, then fill the scoring gaps (technical indicators already implemented in `core/data/indicators.py`, sentiment via Alpaca News + VADER + EDGAR with only 4 new pip packages), then wrap existing handlers as commercial API endpoints behind auth/rate-limiting middleware, and finally build read-only performance attribution. The stack additions are minimal -- no new frameworks, no GPU dependencies, no paid APIs required. Technical scoring needs zero new dependencies; sentiment needs only vaderSentiment and finvizfinance; the commercial API needs PyJWT, slowapi, and optionally Stripe.

The top risks are: (1) lookahead bias in technical indicator backtesting if data cutoffs are not enforced, (2) sentiment scores silently defaulting to 50 and corrupting composite calculations, (3) DDD wiring gaps compounding when adding 3 new bounded contexts (sentiment, performance, commercial), and (4) MACD histogram normalization being price-dependent. All are preventable with specific architectural decisions documented in the research. The self-improver (latest phase) carries overfitting risk that requires walk-forward validation and constrained parameter spaces.

## Key Findings

### Recommended Stack

The existing stack (Python 3.12, pandas, numpy, DuckDB, SQLite, FastAPI, Typer, alpaca-py, edgartools) covers 90% of v1.4 needs. Only 4 new core packages are required, plus 1 optional. No C extensions, no GPU, no large ML frameworks.

**New dependencies only:**
- **vaderSentiment** (3.3.2): headline sentiment scoring -- lexicon-based, zero transitive deps, 339x faster than FinBERT. Adequate for daily-granularity pipeline where sentiment carries 20% composite weight
- **finvizfinance** (1.3.0): aggregated ownership percentages and analyst ratings -- supplements raw SEC data. Web scraper, use as enrichment only with graceful fallback
- **PyJWT** (>=2.12): JWT encode/decode for commercial API auth -- already coded in codebase, just missing from pyproject.toml
- **slowapi** (>=0.1.9): per-user tiered rate limiting -- already coded in codebase, wraps `limits` library
- **stripe** (>=14.4, optional): subscription billing -- defer integration until 10+ paying users exist

**Explicit rejections:** TA-Lib (C build dependency, all 5 indicators already exist in 92 LOC), pandas-ta (30+ transitive deps), torch+transformers (2.5GB for one 20%-weight axis), OpenBB (100+ deps), Redis (premature for single-instance), Celery (APScheduler already handles scheduling).

### Expected Features

**Must have (table stakes):**
- Technical scoring: 5-indicator composite (RSI/MACD/MA/ADX/OBV) filling existing `TechnicalScore` VO -- all LOW complexity, no new deps
- Sentiment scoring: 4-factor composite (analyst revisions/insider trades/news/institutional) filling existing `SentimentScore` VO -- MEDIUM complexity, needs data adapters
- Commercial API: auth + rate limiting + 3 endpoints (QuantScore/RegimeRadar/SignalFusion) + legal disclaimers -- wraps existing handlers
- Trade P&L tracking and basic performance metrics (Sharpe, Sortino, win rate, max drawdown)

**Should have (differentiators):**
- Regime-adjusted technical weights (ADX matters more in trending, RSI in ranging)
- Sentiment sub-component transparency (match TechnicalScore's sub_scores pattern)
- 4-level performance attribution (market/sector/stock/timing via Brinson-Fachler)
- Tiered API response detail (free=composite only, pro=full sub-scores)
- Automated diagnostic flags for skill chain degradation

**Defer (v2+):**
- Walk-forward parameter optimization (needs 6+ months of trade data)
- Fama-French factor decomposition (needs factor data integration)
- Webhook notifications (defer until paying users request it)
- Stripe billing integration (manual key provisioning until 10+ customers)
- Real-time sentiment streaming (system is daily-granularity)
- Social media sentiment (noisy, manipulation-prone, no evidence for swing timeframe)
- Multi-currency/multi-market scoring (each market needs separate calibration)

### Architecture Approach

The architecture adds 3 new bounded contexts (sentiment, performance, commercial) and modifies 3 existing ones (scoring, regime, portfolio), following the established DDD pattern with event-driven cross-context communication via SyncEventBus. The commercial API is a thin facade calling existing handlers behind auth/rate-limit middleware -- it never duplicates domain logic. The sentiment context publishes `SentimentUpdatedEvent` consumed by scoring. Performance attribution is strictly read-only, consuming `PositionClosedEvent` and `OrderFilledEvent`.

**Major components:**
1. **Sentiment context** (`src/sentiment/`) -- news, insider, institutional, analyst data ingestion with own adapters and persistence; publishes events to scoring
2. **Commercial context** (`src/commercial/`) -- API key auth, rate limiting, usage tracking, tiered response shaping; facade over existing scoring/regime/signal handlers
3. **Performance context** (`src/performance/`) -- Brinson-Fachler attribution, trade P&L decomposition; read-only consumer of portfolio/execution events
4. **Modified scoring context** -- wire real sentiment via event subscription, ensure technical indicators flow through DDD path
5. **Modified bootstrap.py** -- composition root wires 3 new contexts + 3 new event subscriptions

### Critical Pitfalls

1. **Lookahead bias in technical indicators** -- enforce `as_of_date` data cutoff in `TechnicalIndicatorAdapter`; separate live vs. backtest code paths; test by verifying tomorrow's close does not change today's score
2. **Silent sentiment=50 corruption** -- add confidence field to SentimentScore; when confidence=NONE, exclude sentiment from composite and re-normalize weights to fundamental+technical only; ship with at least one real data source
3. **DDD wiring gaps compounding** -- fix store mismatch (SQLite vs DuckDB) and verify event bus delivery BEFORE adding new contexts; wire one complete vertical slice as reference implementation; all new features go through `src/` only
4. **MACD normalization range mismatch** -- current hardcoded [-5, +5] range fails for stocks outside $50-500 price range; switch to percentage-based MACD (`histogram / close * 100`) or z-score normalization
5. **Performance attribution without decision context** -- snapshot composite_score, regime_type, and strategy_weights at trade entry time; cannot recover this retroactively; implement context capture early (before attribution phase)
6. **Commercial API security as afterthought** -- auth + rate-limit + request logging must be the FIRST thing built in the commercial phase, not the last

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Pipeline Stabilization & DDD Unification

**Rationale:** PITFALLS.md identifies DDD wiring gaps and store mismatch as the #1 compounding risk. Every subsequent phase adds complexity to a foundation that has known cracks. Fix first.
**Delivers:** Unified data store strategy; verified event bus cross-context delivery; one complete vertical slice (technical scoring for a single indicator) end-to-end through DDD
**Addresses:** Store unification, event bus verification, adapter bottleneck resolution
**Avoids:** Pitfall 3 (DDD wiring gaps), Pitfall 5 (missing decision context -- add context snapshot fields to trade plan records NOW)

### Phase 2: Technical Scoring Integration

**Rationale:** Zero new dependencies. All 5 indicators already implemented. Fills the `TechnicalScore` VO placeholder. Every downstream feature improves when technical scores are real. Lowest-friction, highest-impact work.
**Delivers:** 5-indicator technical composite (RSI/MACD/MA/ADX/OBV) flowing through DDD pipeline; regime-adjusted technical weights; percentage-based MACD normalization
**Addresses:** All 6 technical scoring table-stakes features; regime-adjusted weights differentiator
**Avoids:** Pitfall 1 (lookahead bias -- add `as_of_date` parameter), Pitfall 6 (MACD normalization -- switch to percentage-based)

### Phase 3: Sentiment Scoring

**Rationale:** Independent of technical scoring (can overlap). Fills the last placeholder in composite scoring. Requires external data adapters (Alpaca News, EDGAR, finvizfinance) but no paid APIs.
**Delivers:** 4-factor sentiment composite (analyst/insider/news/institutional); `SentimentUpdatedEvent` wired to scoring; sentiment sub-component transparency
**Uses:** vaderSentiment, finvizfinance (new); alpaca-py news, edgartools (existing)
**Avoids:** Pitfall 2 (silent sentiment=50 -- implement confidence field and two-mode composite)

### Phase 4: Commercial REST API

**Rationale:** Scoring engine now produces complete 3-axis scores worth selling. The commercial API is a thin facade -- LOW implementation cost. Auth/rate-limit/logging must come first in this phase.
**Delivers:** 3 API products (QuantScore, RegimeRadar, SignalFusion); API key auth; tiered rate limiting; usage tracking; legal disclaimers; tiered response detail
**Uses:** PyJWT, slowapi (already coded, just needs pyproject.toml declaration)
**Implements:** Commercial bounded context with own presentation/api layer
**Avoids:** Pitfall 4 (security as afterthought -- middleware first), Pitfall 7 (billing accuracy -- atomic usage counting + idempotency keys)

### Phase 5: Performance Attribution

**Rationale:** Requires trade history to accumulate. Read-only analytics domain. Depends on portfolio context having closed position queries (minor addition from Phase 1).
**Delivers:** Trade P&L tracking; basic performance metrics (Sharpe/Sortino/win rate/drawdown); 4-level Brinson-Fachler attribution (market/sector/stock/timing)
**Implements:** Performance bounded context; benchmark adapter (SPY daily returns)
**Avoids:** Pitfall 5 (decision context already captured from Phase 1)

### Phase 6: Diagnostics & Self-Improvement

**Rationale:** Last phase because it consumes data from all other phases. Requires 50+ trades across 2+ market regimes to be meaningful.
**Delivers:** Automated diagnostic flags; self-improvement recommendation engine (with human approval); parameter versioning with rollback
**Avoids:** Pitfall 8 (overfitting -- constrain parameters to +/-20% of defaults; walk-forward validation mandatory; minimum 50 trades before recommendations)

### Phase Ordering Rationale

- **Stabilize before building:** Phase 1 resolves known tech debt that would otherwise multiply across 3 new bounded contexts
- **Scoring before API:** Phases 2-3 complete the composite score; Phase 4 wraps it for sale. Building the API before scoring is complete means selling an incomplete product
- **Technical before sentiment:** Technical scoring has zero new dependencies and fills existing VOs directly. Sentiment requires external data adapters and has more failure modes
- **Attribution after API:** Performance attribution needs trade history. The longer it waits, the more data it has to work with. It does not block any other feature
- **Self-improvement last:** Requires all other systems producing data. Building it early means optimizing on nothing
- **Parallel opportunities:** Phases 2 and 3 can overlap (independent data sources). Phase 4 auth infrastructure can start during Phase 3

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Sentiment):** Multiple data sources with different APIs, update cadences, and failure modes. Need to validate Alpaca News API response format and VADER accuracy on financial headlines specifically
- **Phase 5 (Attribution):** Brinson-Fachler implementation details, benchmark data sourcing, trade-level vs portfolio-level attribution granularity decisions
- **Phase 6 (Self-Improvement):** Optuna parameter space design, walk-forward window sizing, constraint specification

Phases with standard patterns (skip research-phase):
- **Phase 1 (Stabilization):** Internal refactoring, well-understood codebase
- **Phase 2 (Technical Scoring):** All indicators already implemented; just DDD wiring
- **Phase 4 (Commercial API):** FastAPI + JWT + rate limiting is a well-documented pattern; auth/middleware code already exists in codebase

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All packages verified on PyPI; 4 of 5 already exist in codebase; no version conflicts; existing indicators verified by reading source code |
| Features | HIGH | Features directly derived from existing VOs and methodology docs; dependency graph is clear; complexity estimates grounded in codebase analysis |
| Architecture | HIGH | Extends proven DDD pattern with 10 existing contexts; event bus patterns established; commercial facade pattern is standard |
| Pitfalls | HIGH | Pitfalls identified from codebase inspection (hardcoded MACD range, sentiment=50 default, store mismatch) and domain expertise (lookahead bias, overfitting) |

**Overall confidence:** HIGH

### Gaps to Address

- **VADER accuracy on financial headlines:** Research cites 56% general accuracy. Need to validate on actual Alpaca/Benzinga headlines during Phase 3. If inadequate, FinBERT is the documented upgrade path (add to `requirements-ml.txt` as optional)
- **finvizfinance reliability:** Web scraper, inherently fragile. Must implement graceful fallback (edgartools as primary, finvizfinance as enrichment only). Test during Phase 3 planning
- **slowapi maintenance status:** Last release 12+ months ago. Stable and feature-complete, but if it breaks on FastAPI updates, replacement with direct `limits` library usage is straightforward
- **DuckDB single-writer bottleneck under commercial API load:** Research identifies this as the second scaling bottleneck (after rate-limit state). For initial launch (<100 users), caching scoring results with TTL is sufficient. Monitor during Phase 4 and add Redis cache if p95 latency exceeds 2 seconds
- **Decision context snapshot schema:** The specific fields to capture at trade entry (composite_score, regime_type, strategy_weights, etc.) need to be finalized during Phase 1 planning to ensure attribution has the data it needs

## Sources

### Primary (HIGH confidence)
- Direct codebase verification: `core/data/indicators.py`, `core/scoring/technical.py`, `core/scoring/sentiment.py`, `src/scoring/domain/value_objects.py`, `src/scoring/domain/services.py`, `commercial/api/` -- all verified by reading source
- EdgarTools documentation (13F filings, Form 3/4/5 insider trades)
- Alpaca News API documentation (historical + real-time news)
- FastAPI security documentation (API key auth patterns)
- DuckDB concurrency model documentation (single-writer limitation)
- Marcos Lopez de Prado, "Advances in Financial Machine Learning" (2018) -- lookahead bias, walk-forward validation

### Secondary (MEDIUM confidence)
- VADER vs FinBERT accuracy comparison (DZone article) -- 56% vs 91% general accuracy
- finvizfinance PyPI (v1.3.0, Jan 2026) -- web scraper reliability uncertain
- FastAPI + Stripe integration patterns (community guides)
- Brinson-Fachler attribution methodology (standard financial literature)
- PyJWT CVE-2026-32597 -- low severity for controlled token issuance

### Tertiary (LOW confidence)
- None identified -- all research areas had multiple corroborating sources

---
*Research completed: 2026-03-14*
*Ready for roadmap: yes*
