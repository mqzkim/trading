# Feature Landscape: v1.4 Full Stack Trading Platform

**Domain:** Quantitative trading system -- technical scoring, sentiment scoring, commercial REST API, performance attribution, self-improvement
**Researched:** 2026-03-14
**Confidence:** HIGH (technical/sentiment scoring well-documented in existing research docs; commercial API patterns mature; attribution methodology established)

**Scope:** NEW features only for v1.4. The following already exists and is NOT covered:
- Fundamental scoring (F/Z/M/G-Score) with composite 0-100
- Signal generation (BUY/HOLD/SELL) with reasoning traces
- Risk management (Fractional Kelly 1/4, 3-tier drawdown defense)
- Alpaca execution with human approval
- Bloomberg-style React dashboard (Overview, Signals, Risk, Pipeline)
- Daily automated pipeline with strategy/budget approval
- Domain VOs: `TechnicalScore`, `TechnicalIndicatorScore`, `SentimentScore` already defined with validation (value_objects.py)
- Composite score computation already supports 3-axis weights (`fundamental/technical/sentiment`)

**Key constraint:** The domain VOs already define the shape of technical (RSI/MACD/MA/ADX/OBV sub-scores) and sentiment scoring. Implementation must fill these existing containers with real calculations, not redesign them.

---

## Table Stakes

Features users expect from a production quantitative trading system. Missing any of these means the composite score is incomplete (currently technical=placeholder, sentiment=neutral 50).

| Feature | Why Expected | Complexity | Dependencies on Existing | Notes |
|---------|--------------|------------|-------------------------|-------|
| **RSI scoring (14-period)** | Most basic momentum indicator. Weekly RSI for swing trading detects overbought/oversold conditions | LOW | `TechnicalIndicatorScore` VO exists, needs calculation logic | Score 0-100: RSI < 30 = high score (oversold opportunity), RSI > 70 = low score. Map via inverted sigmoid, not linear |
| **MACD signal scoring** | Second most common momentum indicator. MACD histogram direction and crossovers signal trend changes | LOW | `TechnicalIndicatorScore` VO exists | Score based on: histogram > 0 and rising = bullish. Crossover recency matters. Use weekly MACD for swing timeframe |
| **Moving average trend scoring** | Price relative to 50/200-day MA is universal trend confirmation. Golden/death cross is the most watched pattern | LOW | `TechnicalIndicatorScore` VO exists | Score based on: price > 200MA = base points, price > 50MA > 200MA = full points, distance from MA matters |
| **ADX trend strength scoring** | ADX > 25 confirms a trend exists (any direction). Without trend confirmation, momentum signals are unreliable | LOW | `TechnicalIndicatorScore` VO exists | ADX > 25 = trending (weight momentum signals higher), ADX < 20 = ranging (weight mean-reversion higher) |
| **OBV volume confirmation** | On-Balance Volume confirms price moves with volume. Divergence between price and OBV warns of reversals | LOW | `TechnicalIndicatorScore` VO exists | Score OBV trend direction + slope. Rising OBV + rising price = strong confirmation |
| **Technical composite (5-indicator weighted)** | The existing `TechnicalScore.value` is a placeholder. Must aggregate 5 sub-scores with configurable weights | LOW | `TechnicalScore` VO with sub_scores property exists | Default weights: RSI 20%, MACD 25%, MA 25%, ADX 15%, OBV 15%. Weights already storable in `TechnicalScore.weights` |
| **News sentiment scoring** | Market-moving news shifts stock prices. NLP sentiment from financial news is a validated alpha signal | MEDIUM | `SentimentScore` VO exists (value only, needs sub-components) | Use Finnhub or Alpha Vantage news sentiment API. Aggregate daily sentiment with decay (recent news weighted more). Score 0-100 where 50 = neutral |
| **Analyst revision scoring** | Earnings estimate revisions (FY1/FY2) are among the strongest documented alpha signals. Upward revisions = bullish | MEDIUM | `SentimentScore` VO exists | Use FMP or EODHD analyst estimates. Score: upgrades/revisions up = high, downgrades = low. Revision breadth matters (% of analysts revising) |
| **Insider transaction scoring** | Insider buying clusters predict positive returns (academically validated). Selling is less informative (insiders sell for many reasons) | MEDIUM | `SentimentScore` VO exists | Use SEC Form 4 data via FMP/EODHD. Score: cluster buying (3+ insiders in 30 days) = high signal. Ignore routine selling |
| **Institutional holdings change** | 13F filing changes show "smart money" positioning. Increasing institutional ownership = confidence signal | LOW | `SentimentScore` VO exists | Quarterly data from 13F filings. Score: increasing institutional ownership % = positive. Rate of change matters more than absolute level |
| **Sentiment composite (4-factor weighted)** | The existing `SentimentScore.value` defaults to 50 (neutral). Must aggregate sub-scores into a real composite | LOW | `SentimentScore` VO exists | Default weights: analyst revisions 35%, insider activity 25%, news sentiment 25%, institutional changes 15%. Analyst revisions are the strongest documented signal |
| **API key authentication** | Any commercial API needs auth. API keys are the standard for data APIs (simpler than OAuth for B2D products) | LOW | FastAPI already in stack | Use HTTP header `X-API-Key`. Store hashed keys in SQLite. Include key in all request logging |
| **Rate limiting per tier** | Without rate limiting, one user can overwhelm the system. Tiered limits (Free/Starter/Pro) are standard SaaS | MEDIUM | FastAPI + slowapi or custom middleware | Token bucket algorithm. Limits: Free 5 req/day, Starter 100 req/day, Pro unlimited. Return `429 Too Many Requests` with `Retry-After` header |
| **QuantScore API endpoint** | Core commercial product. GET /api/v1/score/{symbol} returns composite score + sub-scores. Already computed internally | LOW | Scoring engine already produces all data | Wrap existing `CompositeScore` computation as REST endpoint. Add caching (Redis or in-memory TTL). Include `updated_at` timestamp |
| **RegimeRadar API endpoint** | Market regime detection as an API. Unique differentiator (few competitors offer this). Already computed internally | LOW | Regime detection engine already exists | Wrap existing regime detection as REST endpoint. Return: regime label, confidence, probabilities, strategy affinity. Cache aggressively (regime changes infrequently) |
| **SignalFusion API endpoint** | Multi-strategy consensus signal as API. Combines existing signal generation | LOW | Signal generation for all strategies exists | Wrap existing signal consensus as REST endpoint. Return: per-strategy signals + consensus agreement count. Never use "buy/sell" -- use "bullish/bearish/neutral" |
| **API disclaimer/legal notice** | Commercial financial data APIs require disclaimers. "Not investment advice" is legally necessary | LOW | None | Every API response includes `disclaimer` field. Docs page with full legal text. Terms of Service required before API key issuance |
| **Trade P&L tracking** | Cannot do performance attribution without recording actual trade outcomes: entry price, exit price, holding period, fees | LOW | Execution engine already records order fills | Extend trade record with: realized P&L, holding period, slippage (fill vs. signal price), commission. Store in DuckDB for analytics |
| **Basic performance metrics** | Sharpe ratio, win rate, profit factor, max drawdown -- the minimum metrics any trader tracks | MEDIUM | Trade history in execution records | Compute: Sharpe (annualized), Sortino, win rate, average win/loss ratio, profit factor, max drawdown, Calmar ratio. Rolling and cumulative windows |

---

## Differentiators

Features that set this system apart. Not expected in every quant system, but significantly increase value.

| Feature | Value Proposition | Complexity | Dependencies on Existing | Notes |
|---------|-------------------|------------|-------------------------|-------|
| **Regime-adjusted technical weights** | Technical indicator weights shift based on market regime. ADX matters more in trending regimes; RSI matters more in ranging regimes. Most systems use fixed weights | MEDIUM | Regime detection + technical scoring both exist | In "Low-Vol Bull": increase MACD/MA weights (trend signals). In "Low-Vol Range": increase RSI weights (mean-reversion). Regime detection already outputs regime label |
| **Sentiment score with sub-component transparency** | Expand `SentimentScore` VO to expose sub-components (like `TechnicalScore` already does). Most APIs return an opaque sentiment number; showing breakdowns builds trust and explainability | MEDIUM | `SentimentScore` VO needs new fields | Add: `analyst_score`, `insider_score`, `news_score`, `institutional_score` sub-fields. Matches `TechnicalScore`'s pattern with sub_scores. Maintains explainability principle |
| **4-level performance attribution** | Decompose returns into portfolio/strategy/trade/skill levels. Most retail systems stop at portfolio-level Sharpe. Skill-level attribution (was the regime call correct? was position sizing optimal?) is institutional-grade | HIGH | Trade history + regime records + scoring records | Level 1: alpha vs beta. Level 2: per-strategy Sharpe/hit-rate. Level 3: per-trade P&L with timing analysis. Level 4: regime accuracy, signal IC, sizing efficiency |
| **Walk-forward parameter optimization** | Automatically re-optimize scoring weights, Kelly parameters, and indicator settings using rolling out-of-sample validation. Prevents overfitting while adapting to market changes | HIGH | Backtest engine exists, performance metrics needed | Rolling window: train on 12 months, validate on 3 months, step forward 3 months. Target: maximize out-of-sample Sharpe. Constrain parameter ranges to prevent extreme values |
| **Automated diagnostic flags** | System detects when a skill in the chain is degrading: "Signal IC dropped below 0.03", "Regime accuracy < 55%", "Position sizing efficiency < 70%". Self-monitoring before self-improvement | MEDIUM | Performance attribution provides the metrics | Thresholds from research: IC < 0.03 = signal drift, regime accuracy < 55% = retrain needed, sizing efficiency < 70% = recalibrate Kelly. Generate human-readable diagnostic reports |
| **Commercial API usage analytics** | Track per-user API usage, popular endpoints, error rates, latency percentiles. Standard SaaS ops feature but most MVP APIs skip it | MEDIUM | API middleware logging | Log: endpoint, user, timestamp, latency, status code. Dashboard: daily active users, top endpoints, error rate, p95 latency. Use DuckDB for analytics queries |
| **Tiered response detail** | Free tier gets composite score only. Starter gets sub-scores. Pro gets full detail + historical scores. Differentiates tiers by data richness, not just rate limits | LOW | API auth already identifies tier | Use response serialization that strips fields based on tier. More valuable than rate limit differentiation because users upgrade for data, not for more requests |
| **Webhook notifications** | Pro-tier users get POST webhooks when regime changes or when a symbol's score crosses a threshold. Push beats polling | MEDIUM | Regime change events already exist in event bus | Register webhook URL per user. On regime change or score threshold cross, POST to registered URLs. Retry with exponential backoff. Webhook signature verification for security |
| **Self-improvement recommendation engine** | Goes beyond diagnostics: recommends specific parameter changes with expected impact. "Reduce Dual Momentum lookback from 12 to 9 months (WFE improves from 48% to 56%)" | HIGH | Walk-forward optimization + diagnostic flags | Bayesian optimization (Optuna) over parameter space. Rank recommendations by expected improvement. Require human approval before applying changes (human-in-the-loop for parameter changes too) |
| **Fama-French factor decomposition** | Decompose returns into market, size, value, momentum, profitability factors. Tells the user WHERE their alpha comes from. Most retail tools cannot do this | MEDIUM | Trade history + market factor data | Use Kenneth French data library (free, daily updated). Regress portfolio returns against 5-factor model. Report: "62% of your return came from momentum factor, 23% from quality" |

---

## Anti-Features

Features to explicitly NOT build. Commonly requested but problematic for this specific system.

| Anti-Feature | Why Requested | Why Avoid | What to Do Instead |
|--------------|---------------|-----------|-------------------|
| **Real-time sentiment streaming** | "News moves markets in seconds" | This is a daily-granularity swing/position system. Intraday sentiment processing adds massive complexity (NLP pipeline, streaming infra, sub-second response) with zero value for 2-week+ holding periods. Day trading is explicitly forbidden | Batch sentiment scoring once daily during pipeline run. Aggregate 24h of news into a single score. Sufficient for swing timeframe |
| **Social media sentiment (Twitter/Reddit)** | "WSB and FinTwit move stocks" | Social media sentiment is extremely noisy, manipulation-prone (pump-and-dump), and has near-zero predictive power for swing/position timeframes. Academic evidence is weak outside of very short horizons. Data APIs are expensive and unreliable | Stick to validated sentiment signals: analyst revisions (strongest documented alpha), insider trades (academically validated), institutional holdings (13F data). These have decades of evidence |
| **Custom technical indicators** | "Let me add Ichimoku Cloud / SuperTrend / custom formulas" | The system uses 5 validated indicators (RSI/MACD/MA/ADX/OBV) with explainability. Custom indicators bypass the "verified methodologies only" constraint. Each new indicator adds maintenance burden and testing requirements | Expose indicator weights as configurable parameters. The set of indicators is fixed; their relative importance is tunable |
| **ML-based sentiment model** | "Train a transformer on financial news" | Training and maintaining a custom NLP model is a separate product-scale effort. Pre-trained financial sentiment APIs (Finnhub, Alpha Vantage) exist and are good enough. Custom models require labeled data, GPU compute, and ongoing retraining | Use pre-built sentiment APIs (Finnhub news sentiment, FMP analyst data). Aggregate their scores. Let them handle the NLP complexity |
| **Full-auto self-improvement** | "Let the system change its own parameters without approval" | Violates the human-in-the-loop principle. Unattended parameter changes can cause regime-mismatched strategies or oversized positions. Self-improving systems without human gates are a known cause of catastrophic losses | Self-improver generates RECOMMENDATIONS with evidence. Human reviews and approves parameter changes. Changes are logged with rollback capability. Minimum 50 trades before any parameter change recommendation |
| **Billing/payment integration** | "Stripe integration for API subscriptions" | Premature. Build the product first, validate demand, then add billing. Stripe integration is 2+ weeks of work (webhooks, failed payments, plan changes, invoicing) that delivers zero value until there are paying users | Manual API key provisioning for early users. Accept payment via Stripe Payment Links (no integration needed). Build proper billing when there are 10+ paying customers |
| **GraphQL API** | "GraphQL is more flexible than REST" | QuantScore/RegimeRadar/SignalFusion are simple, well-defined endpoints. GraphQL adds schema complexity, N+1 query risks, and caching difficulty. REST with OpenAPI auto-docs (FastAPI's strength) is better for this use case | FastAPI REST with auto-generated OpenAPI/Swagger docs. If complex queries emerge later, add specific REST endpoints rather than GraphQL |
| **Multi-currency / multi-market scoring** | "Score Japanese and European stocks too" | The scoring engine is calibrated for US market data (SEC filings, US fundamental formats, US-centric analyst coverage). Each market has different accounting standards, filing schedules, and data availability. Multi-market is a v2.0 effort | US market only for v1.4. Data adapters for EODHD/FMP already support US data well. Multi-market expansion requires per-market scoring calibration |
| **Portfolio-level optimization** | "Optimize my entire portfolio allocation using Modern Portfolio Theory" | Position sizing already uses Fractional Kelly 1/4. Adding Markowitz/HRP portfolio optimization is a separate feature that conflicts with the per-stock scoring + sizing approach. It is a different investment philosophy | Keep per-stock scoring + Kelly sizing. If portfolio-level risk analysis is needed, use sector limits (25% cap) and position limits (8% cap) which already exist |

---

## Feature Dependencies

```
[OHLCV Price History in DuckDB] (already exists)
    |
    +--enables--> [RSI Calculation]
    +--enables--> [MACD Calculation]
    +--enables--> [Moving Average Calculation]
    +--enables--> [ADX Calculation]
    +--enables--> [OBV Calculation]
                      |
                      +--all feed into--> [Technical Composite Score]
                                              |
                                              +--feeds--> [Composite Score (3-axis)]

[Data API Keys (EODHD/FMP)] (already configured)
    |
    +--enables--> [Analyst Revision Data Fetch]
    +--enables--> [Insider Transaction Data Fetch]
    +--enables--> [Institutional Holdings Data Fetch]

[News Sentiment API (Finnhub/Alpha Vantage)]
    |
    +--enables--> [News Sentiment Scoring]
                      |
                      +--all feed into--> [Sentiment Composite Score]
                                              |
                                              +--feeds--> [Composite Score (3-axis)]

[Composite Score (3-axis: fundamental + technical + sentiment)]
    +--enables--> [QuantScore API]
    +--enables--> [Improved Signal Generation] (scores now reflect real technical+sentiment)

[Regime Detection] (already exists)
    +--enables--> [RegimeRadar API]
    +--enables--> [Regime-Adjusted Technical Weights]

[Signal Generation] (already exists)
    +--enables--> [SignalFusion API]

[FastAPI Server Setup]
    +--requires--> [API Key Authentication]
    +--requires--> [Rate Limiting]
    +--enables--> [QuantScore API]
    +--enables--> [RegimeRadar API]
    +--enables--> [SignalFusion API]

[Trade P&L Tracking]
    +--requires--> [Execution records] (already exist)
    +--enables--> [Basic Performance Metrics]
                      |
                      +--enables--> [4-Level Performance Attribution]
                                        |
                                        +--enables--> [Automated Diagnostic Flags]
                                                          |
                                                          +--enables--> [Self-Improvement Recommendations]
                                                                            |
                                                                            +--enables--> [Walk-Forward Optimization]
```

### Dependency Notes

- **Technical scoring is independent of sentiment scoring:** Both can be built in parallel. Both feed into the existing composite score computation.
- **Technical scoring needs ONLY OHLCV data:** Already in DuckDB. No new data source needed. This is the lowest-friction feature.
- **Sentiment scoring needs external API data:** Analyst revisions and insider trades require FMP or EODHD API calls (already configured). News sentiment needs a new API (Finnhub free tier: 60 req/min, sufficient).
- **Commercial API wraps existing computation:** QuantScore/RegimeRadar/SignalFusion endpoints are thin REST wrappers around existing scoring/regime/signal engines. Low implementation cost.
- **Performance attribution is a pipeline:** Trade tracking -> metrics -> attribution -> diagnostics -> self-improvement. Each step depends on the previous one. Cannot skip steps.
- **Self-improvement is the LAST feature:** It requires all other features to produce data for analysis. Building it too early means no data to learn from.

---

## MVP Recommendation

### Phase 1 Priority: Technical + Sentiment Scoring

Build first because the existing composite score has placeholder technical and neutral sentiment values. Every downstream feature (signals, API scores) improves when these become real.

1. **Technical scoring (5 indicators)** -- LOW complexity, no new dependencies, fills existing VOs
2. **Sentiment scoring (4 factors)** -- MEDIUM complexity, needs API data fetching, fills existing VO
3. **Regime-adjusted technical weights** -- MEDIUM complexity, connects two existing systems

### Phase 2 Priority: Commercial API

Build second because the scoring engine now produces complete scores worth selling.

4. **FastAPI server + auth + rate limiting** -- MEDIUM complexity, standard infrastructure
5. **QuantScore endpoint** -- LOW complexity, wraps existing scoring
6. **RegimeRadar endpoint** -- LOW complexity, wraps existing regime detection
7. **SignalFusion endpoint** -- LOW complexity, wraps existing signal generation

### Phase 3 Priority: Performance Attribution + Self-Improvement

Build last because it requires trade history to accumulate first.

8. **Trade P&L tracking** -- LOW complexity, extends existing execution records
9. **Performance metrics** -- MEDIUM complexity, standard financial math
10. **4-level attribution** -- HIGH complexity, core differentiator
11. **Diagnostic flags + self-improvement recommendations** -- HIGH complexity, requires attribution data

### Defer

- **Walk-forward optimization** -- Needs 6+ months of trade data to be meaningful. Build when data exists.
- **Fama-French decomposition** -- Requires factor data integration. Nice-to-have after basic attribution works.
- **Webhook notifications** -- Defer until commercial API has paying users who request it.
- **Billing/Stripe integration** -- Defer until 10+ users. Use manual key provisioning initially.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Phase |
|---------|------------|---------------------|----------|-------|
| RSI scoring | HIGH | LOW | P1 | Technical |
| MACD scoring | HIGH | LOW | P1 | Technical |
| MA trend scoring | HIGH | LOW | P1 | Technical |
| ADX trend strength | HIGH | LOW | P1 | Technical |
| OBV volume confirm | MEDIUM | LOW | P1 | Technical |
| Technical composite | HIGH | LOW | P1 | Technical |
| News sentiment | MEDIUM | MEDIUM | P1 | Sentiment |
| Analyst revisions | HIGH | MEDIUM | P1 | Sentiment |
| Insider transactions | MEDIUM | MEDIUM | P1 | Sentiment |
| Institutional holdings | LOW | LOW | P1 | Sentiment |
| Sentiment composite | HIGH | LOW | P1 | Sentiment |
| Regime-adjusted weights | MEDIUM | MEDIUM | P1 | Technical |
| API key auth | HIGH | LOW | P2 | Commercial |
| Rate limiting | HIGH | MEDIUM | P2 | Commercial |
| QuantScore API | HIGH | LOW | P2 | Commercial |
| RegimeRadar API | HIGH | LOW | P2 | Commercial |
| SignalFusion API | HIGH | LOW | P2 | Commercial |
| API disclaimer | HIGH | LOW | P2 | Commercial |
| Tiered response detail | MEDIUM | LOW | P2 | Commercial |
| Usage analytics | MEDIUM | MEDIUM | P2 | Commercial |
| Trade P&L tracking | HIGH | LOW | P3 | Attribution |
| Performance metrics | HIGH | MEDIUM | P3 | Attribution |
| 4-level attribution | HIGH | HIGH | P3 | Attribution |
| Diagnostic flags | MEDIUM | MEDIUM | P3 | Attribution |
| Self-improvement recs | MEDIUM | HIGH | P3 | Attribution |
| Sentiment sub-component VO | MEDIUM | MEDIUM | P1 | Sentiment |
| Walk-forward optimization | MEDIUM | HIGH | P4 | Future |
| Fama-French decomposition | LOW | MEDIUM | P4 | Future |
| Webhook notifications | LOW | MEDIUM | P4 | Future |

**Priority key:**
- P1: Scoring completion -- makes the composite score real instead of placeholder
- P2: Commercial API -- monetizes the scoring engine
- P3: Attribution + self-improvement -- closes the feedback loop
- P4: Future enhancements -- need data/users to justify

---

## Sources

- Existing codebase: `src/scoring/domain/value_objects.py` -- TechnicalScore, TechnicalIndicatorScore, SentimentScore VOs already defined (HIGH confidence)
- `docs/quantitative-scoring-methodologies.md` -- Technical sub-score components (RSI, MACD, MA, ADX, OBV) and sentiment sub-score components (analyst, news, insider, institutional) fully specified (HIGH confidence)
- `docs/skill_chaining_and_self_improvement_research.md` -- 4-level performance attribution framework, feedback loop architecture, walk-forward optimization, diagnostic thresholds (HIGH confidence)
- `docs/strategy-recommendation.md` -- Commercial product definitions (QuantScore, RegimeRadar, SignalFusion), pricing tiers, legal boundaries (HIGH confidence)
- `docs/api-technical-feasibility.md` -- Data API availability for sentiment data (FMP, EODHD, Finnhub), rate limits, cost analysis (HIGH confidence)
- [Finnhub News Sentiment API](https://finnhub.io/docs/api/news-sentiment) -- News sentiment scoring API reference (MEDIUM confidence)
- [FMP Analyst Estimates API](https://site.financialmodelingprep.com/datasets/analyst-estimates-targets) -- Analyst revision data source (MEDIUM confidence)
- [SentimenTrader](https://sentimentrader.com/indicator-api) -- Sentiment indicator API reference (MEDIUM confidence)
- [Performance Attribution - Brinson-Fachler](https://www.neoxam.com/datahub/performance-attribution-brinson-fachler-method-explained/) -- Attribution methodology reference (MEDIUM confidence)
- [FastAPI Rate Limiting Best Practices 2025](https://zuplo.com/learning-center/10-best-practices-for-api-rate-limiting-in-2025) -- Token bucket, sliding window patterns (MEDIUM confidence)
- [QuantifiedStrategies: 100 Best Trading Indicators 2026](https://www.quantifiedstrategies.com/trading-indicators/) -- Indicator validation and parameter settings (MEDIUM confidence)

---
*Feature research for: v1.4 Full Stack Trading Platform*
*Researched: 2026-03-14*
