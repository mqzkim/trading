# Requirements: Intrinsic Alpha Trader v1.4

**Defined:** 2026-03-14
**Core Value:** Every recommendation must be explainable and risk-controlled — capital preservation and positive expectancy over maximizing returns.

## v1.4 Requirements

Requirements for Full Stack Trading Platform milestone. Each maps to roadmap phases.

### Pipeline & Tech Debt

- [ ] **PIPE-01**: Pipeline runs successfully end-to-end (screening → scoring → signal → execution)
- [ ] **PIPE-02**: DuckDB/SQLite scoring store mismatch resolved (single source of truth)
- [ ] **PIPE-03**: Domain events actually published and consumed via EventBus (not just defined)
- [ ] **PIPE-04**: target_price populated from valuation engine (not always 0.0)
- [ ] **PIPE-05**: current_price uses live/latest price data (not entry_price proxy)
- [ ] **PIPE-06**: DDD path wiring gaps closed (legacy core/ wrapper only as fallback)

### Technical Scoring

- [ ] **TECH-01**: RSI(14) scoring integrated into TechnicalScore VO with 0-100 mapping
- [ ] **TECH-02**: MACD scoring with histogram direction and crossover detection
- [ ] **TECH-03**: Moving average trend scoring (50/200-day MA, golden/death cross)
- [ ] **TECH-04**: ADX trend strength scoring (>25 trending, <20 ranging)
- [ ] **TECH-05**: OBV volume confirmation scoring
- [ ] **TECH-06**: MACD normalization bug fixed (hardcoded [-5,+5] range)
- [ ] **TECH-07**: Composite score reflects 3-axis weights (fundamental/technical/sentiment)

### Sentiment Scoring

- [ ] **SENT-01**: News sentiment scoring via Alpaca News API + VADER analysis
- [ ] **SENT-02**: Insider trade scoring from SEC Form 4 data (buy/sell ratio)
- [ ] **SENT-03**: Institutional holdings change rate from 13F filings
- [ ] **SENT-04**: Analyst estimate revision direction integrated
- [ ] **SENT-05**: SentimentScore VO populated with real sub-component data (not default 50)
- [ ] **SENT-06**: Sentiment confidence field added (data freshness/coverage indicator)

### Commercial API

- [ ] **API-01**: QuantScore endpoint returns composite score with sub-component breakdown
- [ ] **API-02**: RegimeRadar endpoint returns current regime with probability and indicators
- [ ] **API-03**: SignalFusion endpoint returns consensus signal with reasoning trace
- [ ] **API-04**: JWT authentication with API key management
- [ ] **API-05**: Rate limiting per tier (free/basic/pro)
- [ ] **API-06**: Legal disclaimer auto-included in all responses
- [ ] **API-07**: OpenAPI/Swagger documentation auto-generated

### Performance Attribution

- [ ] **PERF-01**: Trade-level P&L tracking with entry/exit context
- [ ] **PERF-02**: Brinson-Fachler 4-level decomposition (portfolio/strategy/trade/skill)
- [ ] **PERF-03**: Signal IC validation (>= 0.03 threshold)
- [ ] **PERF-04**: Kelly efficiency monitoring (>= 70% threshold)
- [ ] **PERF-05**: Decision context snapshot captured at trade entry time

### Self-Improvement

- [ ] **SELF-01**: Parameter adjustment proposals generated from performance analysis
- [ ] **SELF-02**: Propose-then-approve workflow (no auto-modification)
- [ ] **SELF-03**: Walk-forward validation before parameter changes applied
- [ ] **SELF-04**: Minimum 50 trades threshold before self-improvement activates

### Dashboard Enhancement

- [ ] **DASH-01**: Technical and sentiment sub-scores visible on Signals page
- [ ] **DASH-02**: Performance attribution page added to dashboard
- [ ] **DASH-03**: Real data displayed across all pages (no empty states when data exists)
- [ ] **DASH-04**: Regime detection enhanced view with HMM probabilities

## Future Requirements

### Korean Market

- **KR-01**: KIS broker integration for Korean stock market
- **KR-02**: Korean financial data sources (재무제표, 공시)

### Advanced ML

- **ML-01**: FinBERT upgrade for sentiment analysis (91% vs VADER 56%)
- **ML-02**: HMM ensemble for regime detection

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full auto-execution | Strategy/budget approval still required (human-in-the-loop) |
| Mobile app | Web dashboard first |
| Real-time intraday | Daily granularity for mid-term holding |
| Options/derivatives | Stock-only |
| Social media sentiment | Noisy, unverified methodology |
| Real-time sentiment streaming | Daily granularity sufficient |
| Stripe billing integration | Deferred — manual API key issuance for initial customers |
| Auto parameter changes | Self-improver proposes only, human approves |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PIPE-01 | Phase 26 | Pending |
| PIPE-02 | Phase 26 | Pending |
| PIPE-03 | Phase 26 | Pending |
| PIPE-04 | Phase 26 | Pending |
| PIPE-05 | Phase 26 | Pending |
| PIPE-06 | Phase 26 | Pending |
| TECH-01 | Phase 27 | Pending |
| TECH-02 | Phase 27 | Pending |
| TECH-03 | Phase 27 | Pending |
| TECH-04 | Phase 27 | Pending |
| TECH-05 | Phase 27 | Pending |
| TECH-06 | Phase 27 | Pending |
| TECH-07 | Phase 27 | Pending |
| SENT-01 | Phase 27 | Pending |
| SENT-02 | Phase 27 | Pending |
| SENT-03 | Phase 27 | Pending |
| SENT-04 | Phase 27 | Pending |
| SENT-05 | Phase 27 | Pending |
| SENT-06 | Phase 27 | Pending |
| API-01 | Phase 28 | Pending |
| API-02 | Phase 28 | Pending |
| API-03 | Phase 28 | Pending |
| API-04 | Phase 28 | Pending |
| API-05 | Phase 28 | Pending |
| API-06 | Phase 28 | Pending |
| API-07 | Phase 28 | Pending |
| PERF-01 | Phase 29 | Pending |
| PERF-02 | Phase 29 | Pending |
| PERF-03 | Phase 29 | Pending |
| PERF-04 | Phase 29 | Pending |
| PERF-05 | Phase 29 | Pending |
| SELF-01 | Phase 29 | Pending |
| SELF-02 | Phase 29 | Pending |
| SELF-03 | Phase 29 | Pending |
| SELF-04 | Phase 29 | Pending |
| DASH-01 | Phase 28 | Pending |
| DASH-02 | Phase 28 | Pending |
| DASH-03 | Phase 28 | Pending |
| DASH-04 | Phase 28 | Pending |

**Coverage:**
- v1.4 requirements: 39 total
- Mapped to phases: 39
- Unmapped: 0

---
*Requirements defined: 2026-03-14*
*Last updated: 2026-03-14 after roadmap creation*
