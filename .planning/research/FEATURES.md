# Feature Research: v1.1 New Capabilities

**Domain:** Quantitative Trading System -- Technical Scoring, Regime Detection, Multi-Strategy Signal Fusion, Korean Market, Commercial API
**Researched:** 2026-03-12
**Confidence:** HIGH (existing codebase verified + domain research)

**Scope:** This document covers ONLY new capabilities for v1.1. v1.0 features (fundamental scoring, valuation, basic signals, risk management, Alpaca paper trading, CLI dashboard) are already built with 352+ tests.

---

## Capability 1: Technical Scoring Engine (RSI, MACD, MA, ADX, OBV)

### What It Is

A rule-based scoring system that converts raw technical indicators into a normalized 0-100 TechnicalScore. The existing codebase already has a `TechnicalScore(ValueObject)` placeholder in `scoring/domain/value_objects.py` (value: float, 0-100) and strategy weights allocating 40% (swing) / 30% (position) to technical scoring. The scoring handler currently falls back to `core.scoring.technical.compute_technical_score`. This phase replaces the placeholder with a real, multi-indicator composite.

### Expected Behavior

**Standard technical indicators and their roles:**

| Indicator | Purpose | Standard Parameters | Signal Logic |
|-----------|---------|---------------------|--------------|
| RSI (Relative Strength Index) | Momentum oscillator, overbought/oversold | Period: 14 days | <30 = oversold (bullish), >70 = overbought (bearish), 30-70 = neutral |
| MACD (Moving Average Convergence Divergence) | Trend direction + momentum | Fast: 12, Slow: 26, Signal: 9 | Histogram >0 + rising = bullish, <0 + falling = bearish, crossovers for entries |
| Moving Averages (SMA/EMA) | Trend identification | 50-day (medium), 200-day (long-term) | Price > 200 EMA = uptrend, Golden Cross (50 > 200) = bullish, Death Cross = bearish |
| ADX (Average Directional Index) | Trend strength (not direction) | Period: 14 days | <20 = no trend (sideways), 20-25 = weak, 25-40 = strong, >40 = very strong |
| OBV (On-Balance Volume) | Volume-price confirmation | Cumulative | Rising OBV + rising price = confirmed, divergence = warning |

**Composite technical score formula (industry standard approach):**

```
technical_score = (
    rsi_score * 0.20           # Momentum state
  + macd_score * 0.25          # Trend direction + momentum
  + ma_trend_score * 0.25      # Price vs moving averages
  + adx_score * 0.15           # Trend strength
  + obv_score * 0.15           # Volume confirmation
)
```

Each sub-indicator produces a 0-100 score. The composite is also 0-100 and plugs directly into the existing `CompositeScore.compute()` method.

### Table Stakes

| Feature | Why Expected | Complexity | Dependency |
|---------|--------------|------------|------------|
| RSI calculation with standard 14-period | Every technical screener has RSI. Finviz, TradingView, Stock Rover all include it. | LOW | OHLCV data (existing `data_ingest` context) |
| MACD with 12/26/9 parameters | Standard momentum indicator. No technical analysis tool omits MACD. | LOW | OHLCV data |
| 50-day and 200-day moving averages | Golden Cross / Death Cross are universally referenced. Existing regime detection already uses S&P 200MA. | LOW | OHLCV data |
| ADX trend strength | Already a value object in `regime/domain/value_objects.py` (`TrendStrength`). Reuse the same logic. | LOW | OHLCV data |
| OBV volume confirmation | Standard volume indicator. Detects accumulation/distribution. | LOW | OHLCV data (needs volume field) |
| Composite technical score (0-100) | The `TechnicalScore` VO already expects this. Existing `CompositeScore.compute()` weights it at 40% (swing) / 30% (position). | MEDIUM | All above indicators |
| Sub-score breakdown in output | Matches existing explainability pattern -- F-Score shows 9 sub-criteria. Technical score should show 5 sub-scores. | LOW | Composite technical score |

### Differentiators

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| Regime-conditioned technical interpretation | RSI <30 in a bull market = buying opportunity. RSI <30 in a crisis = catching a falling knife. Context-aware interpretation. | MEDIUM |
| Volume-price divergence detection | OBV divergence from price trend is a leading indicator. Alert when OBV weakens before price drops. | LOW |
| Configurable weights per strategy | Swing traders weigh momentum (RSI, MACD) more. Position traders weigh trend (MA, ADX) more. Weights already exist in `STRATEGY_WEIGHTS`. | LOW |

### Anti-Features

| Feature | Why Problematic | Alternative |
|---------|-----------------|-------------|
| 50+ indicators (Bollinger, Stochastic, Ichimoku, etc.) | Indicator overload causes analysis paralysis and overfitting. 5 orthogonal indicators cover momentum, trend, strength, volume. | Stick to 5 core indicators. Add more only with backtest evidence. |
| Intraday indicator updates | Mid-term holding (2 weeks+) does not benefit from minute-level RSI. Adds data cost and complexity. | Daily EOD calculation is sufficient. |
| ML-optimized indicator weights | Overfits to historical regimes. Weights should be explainable. | Fixed, documented weights with optional strategy profiles. |

---

## Capability 2: Market Regime Detection (Bull/Bear/Sideways/Crisis)

### What It Is

Already partially built. The DDD domain exists at `src/regime/` with:
- `RegimeType` enum (Bull/Bear/Sideways/Crisis)
- Value objects: `VIXLevel`, `TrendStrength` (ADX), `YieldCurve`, `SP500Position`
- `RegimeDetectionService.detect()` with rule-based classification
- `MarketRegime` entity with 3-day confirmation logic
- `RegimeChangedEvent` for event-driven communication
- SQLite persistence repository

**What is NOT built:** Data ingestion for regime indicators (VIX, S&P 500 200MA, yield curve), scheduled detection, and integration with scoring weights.

### Expected Behavior

**Regime classification rules (already coded, academically validated):**

| Regime | Conditions | Confidence |
|--------|------------|------------|
| Crisis | VIX > 40 OR Yield Curve < -0.5% | 0.6-1.0 (dual signal) |
| Bear | VIX > 30 AND S&P 500 < 200MA | 0.5-0.9 |
| Sideways | ADX < 20 (no clear trend) | 0.6 |
| Bull | VIX < 20 AND S&P > 200MA AND ADX > 25 AND Yield Curve > 0 | 0.85 |

**Regime-to-strategy weight mapping (documented but not wired):**

| Regime | Fundamental Weight | Technical Weight | Sentiment Weight | Rationale |
|--------|-------------------|-----------------|-----------------|-----------|
| Bull | 0.30 | 0.45 | 0.25 | Emphasize momentum/trend |
| Bear | 0.55 | 0.25 | 0.20 | Emphasize quality/safety |
| Sideways | 0.40 | 0.35 | 0.25 | Balanced |
| Crisis | 0.60 | 0.20 | 0.20 | Maximum quality emphasis |

### Table Stakes

| Feature | Why Expected | Complexity | Dependency |
|---------|--------------|------------|------------|
| VIX data ingestion | VIX is the primary fear indicator. Must be sourced daily. yfinance provides ^VIX. | LOW | `data_ingest` context |
| S&P 500 vs 200MA position | Already modeled as `SP500Position` VO. Need data feed for SPY/^GSPC + 200-day SMA. | LOW | `data_ingest` context |
| Yield curve spread (10Y - 2Y) | `YieldCurve` VO exists. Need Treasury rate data feed (FRED API or yfinance ^TNX/^TWO). | LOW | New data source (FRED API or yfinance proxy) |
| ADX for S&P 500 | `TrendStrength` VO exists. Same ADX calculation as technical scoring but for index. | LOW | Technical scoring engine (shared calculation) |
| Current regime endpoint (CLI) | User needs to see current market state before making decisions. | LOW | Regime detection service |
| Regime history (last 90 days) | Track regime transitions for pattern analysis. SQLite repo already exists. | LOW | SQLite persistence (existing) |
| Regime-changed event emission | `RegimeChangedEvent` is defined but events are not published to EventBus (tech debt item). | LOW | EventBus wiring (tech debt fix) |

### Differentiators

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| Regime-conditioned scoring weights | Bull: emphasize momentum. Bear: emphasize quality. This is the `RegimeWeightAdjuster` Protocol already defined in `scoring/domain/services.py`. No retail tool does this automatically. | MEDIUM |
| 3-day confirmation before regime change | Prevents whipsaw. Already coded in `MarketRegime.is_confirmed`. Just needs wiring. | LOW |
| Regime-specific strategy recommendations | "Current regime is Bear. Trend Following performance is historically weak in bear markets. Consider reducing exposure." | LOW |
| RegimeRadar commercial API | Unique commercial product -- no competitor offers regime detection as an API. | MEDIUM (after regime works locally) |

### Anti-Features

| Feature | Why Problematic | Alternative |
|---------|-----------------|-------------|
| HMM (Hidden Markov Model) for regime detection | Adds hmmlearn/scikit-learn dependency, requires training data, non-deterministic results. The rule-based approach with 4 indicators is more explainable and already coded. | Rule-based detection with VIX/S&P/ADX/YieldCurve. HMM only if rule-based proves insufficient after 6+ months of live validation. |
| Sub-minute regime updates | Regimes don't change in minutes. VIX and S&P close prices are sufficient. Real-time streaming adds cost without value. | Daily detection (after market close) with 3-day confirmation. |
| Micro-regimes (10+ states) | More states = more noise, more parameter tuning, harder to map to strategy adjustments. Academic consensus uses 2-4 states. | 4 regimes (Bull/Bear/Sideways/Crisis) is the sweet spot for actionability. |

---

## Capability 3: Multi-Strategy Signal Fusion (CAN SLIM, Magic Formula, Dual Momentum, Trend Following)

### What It Is

The DDD domain at `src/signals/` already defines:
- `MethodologyType` enum: CAN_SLIM, MAGIC_FORMULA, DUAL_MOMENTUM, TREND_FOLLOWING
- `MethodologyResult` VO: direction + score + reason per methodology
- `ConsensusThreshold` VO: 3/4 agreement required
- `SignalFusionService.fuse()`: produces consensus signal from 4 methodology results
- `SignalDirection` enum: BUY/SELL/HOLD

**What is NOT built:** The actual methodology implementations. The fusion logic exists but has no concrete strategy calculators to feed it.

### Expected Behavior Per Strategy

#### CAN SLIM (William O'Neil, Growth + Momentum)

7 criteria scored individually, composite determines signal:

| Letter | Criterion | Quantitative Rule | Data Source |
|--------|-----------|-------------------|-------------|
| C | Current quarterly EPS | EPS growth >= 25% YoY | Financial statements |
| A | Annual earnings growth | 5-year EPS growth >= 25% CAGR | Financial statements |
| N | New highs, new product/management | Price within 15% of 52-week high | OHLCV |
| S | Supply and demand | Below-average share count + volume surge on up days | OHLCV + shares outstanding |
| L | Leader or laggard | Relative strength rank >= 80 (top 20% of market) | OHLCV (relative performance) |
| I | Institutional sponsorship | Institutional ownership 30-60% + increasing | Financial data (holders) |
| M | Market direction | S&P 500 above 200 MA (bull market) | Regime detection context |

**Score:** 0-7 criteria met. BUY when >= 5/7 AND market in Bull regime.

#### Magic Formula (Joel Greenblatt, Quality + Value)

Two rankings combined:

| Metric | Formula | Data Source |
|--------|---------|-------------|
| Earnings Yield | EBIT / Enterprise Value | Financial statements |
| Return on Capital | EBIT / (Net Fixed Assets + Working Capital) | Financial statements |

**Score:** Rank all stocks by each metric. Sum ranks. Lower combined rank = better. Top 20-30 stocks in universe get BUY signal. Hold for 1 year, rebalance annually.

#### Dual Momentum (Gary Antonacci, Absolute + Relative)

Two-step momentum filter:

| Step | Logic | Parameters |
|------|-------|------------|
| Absolute Momentum | Is 12-month return > T-bill return? | 12-month lookback vs risk-free rate |
| Relative Momentum | Which asset class performed better? | US equity vs International equity (12-month return) |

**Signal:** If absolute momentum positive AND US outperforms International, BUY US equity. If absolute momentum positive AND International outperforms, BUY International. If absolute momentum negative, go to bonds/cash. Applied at portfolio level, not individual stocks.

#### Trend Following (Turtle-inspired, Price + ATR)

Rule-based trend system:

| Rule | Logic | Parameters |
|------|-------|------------|
| Entry | Price breaks above 20-day high (System 1) or 55-day high (System 2) | 20/55 day lookback |
| Exit | Price breaks below 10-day low (System 1) or 20-day low (System 2) | 10/20 day lookback |
| Position Size | 1% risk per trade, sized by ATR | ATR(21) for volatility normalization |
| Trend Confirmation | ADX > 25 confirms trend | ADX period 14 |

**Signal:** BUY when price > 20-day high AND ADX > 25. SELL when price < 10-day low.

### Table Stakes

| Feature | Why Expected | Complexity | Dependency |
|---------|--------------|------------|------------|
| CAN SLIM scoring (7 criteria) | Iconic growth stock methodology. O'Neil's IBD uses it. Requires EPS growth, relative strength, institutional data. | MEDIUM | Financial statements + OHLCV (existing) + institutional ownership data (new) |
| Magic Formula ranking (EBIT-based) | Greenblatt's methodology is widely published. Requires EBIT, enterprise value, net fixed assets. | MEDIUM | Financial statements (existing data pipeline) |
| Dual Momentum signal (absolute + relative) | Antonacci's methodology is simple: 12-month return vs T-bill, US vs International. | LOW | OHLCV + risk-free rate (new data point) |
| Trend Following signal (breakout + ADX) | Turtle-inspired rules. Uses 20/55-day highs and lows. | LOW | OHLCV (existing) + ADX (from technical scoring) |
| Consensus fusion (3/4 agreement) | Already coded in `SignalFusionService.fuse()`. Just needs real methodology inputs. | LOW | All 4 methodology implementations |
| Per-methodology reasoning trace | Each methodology should explain why it signaled BUY/HOLD/SELL. Matches existing explainability pattern. | LOW | Methodology implementations |

### Differentiators

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| Regime-weighted methodology aggregation | In Bull markets, weight Trend Following and Dual Momentum higher. In Bear markets, weight Magic Formula (quality) higher. Uses regime detection output. | MEDIUM |
| Methodology agreement visualization | Show which strategies agree and why. "3/4 methods agree BUY: CAN SLIM (6/7 criteria), Magic Formula (rank 15/500), Trend Following (20-day breakout). Dual Momentum says HOLD (absolute momentum negative)." | LOW |
| Methodology-specific backtest validation | Each methodology can be backtested independently before inclusion in fusion. | HIGH |
| SignalFusion commercial API | Expose consensus signals as REST API. No competitor offers 4-strategy fusion as a service. | MEDIUM (after fusion works locally) |

### Anti-Features

| Feature | Why Problematic | Alternative |
|---------|-----------------|-------------|
| Dynamic methodology weight optimization | ML-optimized weights overfit to historical regimes. Fixed regime-based weight tables are more robust. | Predefined weight tables per regime (Bull/Bear/Sideways/Crisis). |
| 10+ methodologies | More strategies does not mean better consensus. 4 orthogonal methods (growth, value, momentum, trend) cover the major factor families. | 4 methodologies covering 4 factor families. |
| Individual stock picks from Dual Momentum | Dual Momentum is an asset-class-level strategy (US vs International vs Bonds). Forcing it to pick individual stocks distorts the methodology. | Use Dual Momentum for asset allocation overlay, not individual stock selection. |

---

## Capability 4: Korean Market Support (KOSPI/KOSDAQ + KIS Broker)

### What It Is

Expansion from US-only to US + Korean market. Requires:
1. Korean market data ingestion (KOSPI/KOSDAQ OHLCV + financials)
2. Korean brokerage integration (KIS OpenAPI for paper/live trading)
3. Scoring/signal compatibility with Korean financial statement formats (K-IFRS)

### Expected Behavior

**KIS OpenAPI capabilities (REST-based, Linux-compatible):**

| Feature | Endpoint | Rate Limit |
|---------|----------|------------|
| Domestic stock price | `/uapi/domestic-stock/v1/quotations/inquire-price` | 20 req/sec |
| OHLCV history | `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice` | 20 req/sec |
| Order placement | `/uapi/domestic-stock/v1/trading/order-cash` | 20 req/sec |
| Account balance | `/uapi/domestic-stock/v1/trading/inquire-balance` | 20 req/sec |
| Mock trading | Separate base URL (port 29443 vs 9443) | Same limits |
| WebSocket real-time | `/uapi/domestic-stock/v1/quotations/ws` | Streaming |

**Korean market data specifics:**

| Aspect | US Market (Current) | Korean Market (New) |
|--------|--------------------|--------------------|
| Ticker format | AAPL, MSFT (alphabetic) | 005930, 000660 (6-digit numeric) |
| Exchange suffix | .US or none | .KS (KOSPI), .KQ (KOSDAQ) |
| Accounting standard | US GAAP | K-IFRS (mostly aligned with IFRS) |
| Currency | USD | KRW |
| Trading hours | 09:30-16:00 ET | 09:00-15:30 KST |
| Lot size | 1 share | 1 share |
| Settlement | T+1 | T+2 |
| Financial statement access | SEC EDGAR (free, authoritative) | DART (FSS disclosure, Korean equivalent) |

### Table Stakes

| Feature | Why Expected | Complexity | Dependency |
|---------|--------------|------------|------------|
| KOSPI/KOSDAQ OHLCV ingestion | Cannot analyze Korean stocks without price data. yfinance supports KRX (suffix .KS/.KQ). EODHD supports KRX data. | MEDIUM | Data source adapter (new exchange mapping in `data_ingest`) |
| Korean financial statement ingestion | F-Score, Z-Score require financial statements. K-IFRS is close to IFRS. DART API or EODHD fundamentals. | HIGH | K-IFRS to scoring model mapping (field name differences) |
| KIS broker mock trading | Paper trading equivalent for Korean market. KIS provides a separate mock trading environment (port 29443). | MEDIUM | New broker adapter in `execution` context |
| KIS order placement (market/limit) | Basic buy/sell for Korean stocks. REST API, OAuth-like token auth (24h refresh). | MEDIUM | Token refresh logic, order model adaptation |
| Korean ticker resolution | Map 005930 to Samsung Electronics, support .KS/.KQ suffixes. | LOW | Ticker lookup table or API |
| Currency handling (KRW) | Position sizing must handle KRW denominations. KRW lots are typically larger nominal values. | LOW | Currency-aware position sizing |

### Differentiators

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| Cross-market screening (US + KR) | Screen both markets simultaneously. Compare Samsung (005930.KS) vs Apple (AAPL) on same composite score. Sector-neutral normalization handles cross-market comparison. | MEDIUM |
| KIS overseas trading | KIS supports US stock trading too (via overseas stock endpoints). Could become single-broker solution for both markets. | LOW |
| DART financial disclosure integration | Korean SEC equivalent. Free API for Korean company filings. Authoritative source for K-IFRS financials. | HIGH |

### Anti-Features

| Feature | Why Problematic | Alternative |
|---------|-----------------|-------------|
| Real-time Korean market streaming | Same rationale as US -- daily EOD is sufficient for swing/position trading. | Daily batch ingestion. |
| Korean market intraday trading | Project constraint: no day trading. Korean market T+2 settlement makes day trading even less suitable. | Swing/position trading only. |
| Naver Finance scraping | Unreliable, unstructured, can break anytime. Not production-grade. | KIS API + EODHD/yfinance for data. |
| Multi-currency portfolio optimization | Adds FX risk modeling complexity. KRW/USD hedging is a separate domain. | Track positions per currency. Simple FX conversion for display only. |

---

## Capability 5: Commercial REST API (QuantScore, RegimeRadar, SignalFusion)

### What It Is

FastAPI-based REST API exposing scoring, regime detection, and signal fusion as commercial products. Three tiers of service at different price points, with rate limiting and API key authentication. Legal boundary: "information provision" only (no buy/sell recommendations = no investment advisory license needed).

### Expected Behavior

**Three API products (from strategy-recommendation.md):**

| Product | Endpoint Pattern | What It Returns | Legal Status |
|---------|-----------------|-----------------|--------------|
| QuantScore | `GET /api/v1/score/{symbol}` | Composite score (0-100), sub-scores, safety filter status | Information provision (scores are data) |
| RegimeRadar | `GET /api/v1/regime/current` | Current market regime, confidence, indicator values, strategy affinity | Information provision (regime is data) |
| SignalFusion | `GET /api/v1/signal/{symbol}` | Per-methodology direction, consensus agreement, regime context | Information provision (signal strength is data, NOT buy/sell advice) |

**API tier structure:**

| Tier | Rate Limit | Features | Price |
|------|-----------|----------|-------|
| Free | 5 req/day | US market, composite score only | $0 |
| Starter | 100 req/day | US + KR, detailed sub-scores, history | $29-49/mo |
| Pro | Unlimited | All markets, screening, WebSocket, full API | $99-199/mo |

### Table Stakes

| Feature | Why Expected | Complexity | Dependency |
|---------|--------------|------------|------------|
| API key authentication | Every commercial API requires auth. Simple API key in header. | LOW | FastAPI middleware |
| Rate limiting per tier | Tier-based throttling (Free: 5/day, Starter: 100/day, Pro: unlimited). Use `slowapi` or `fastapi-limiter` + Redis. | MEDIUM | Redis for distributed counters |
| `/score/{symbol}` endpoint | Core QuantScore product. Returns composite score with breakdown. Reuses existing `CompositeScoringService`. | LOW | Scoring context (existing) |
| `/regime/current` endpoint | Core RegimeRadar product. Returns current regime, confidence, indicators. Reuses `RegimeDetectionService`. | LOW | Regime context (existing/enhanced) |
| `/signal/{symbol}` endpoint | Core SignalFusion product. Returns per-methodology results + consensus. Reuses `SignalFusionService`. | LOW | Signal context (existing/enhanced) |
| Legal disclaimer in every response | Required for investment information APIs. `"disclaimer": "This information is not investment advice."` | LOW | Response middleware |
| OpenAPI/Swagger documentation | FastAPI auto-generates this. Every API product needs interactive docs. | LOW | FastAPI built-in |
| Health check endpoint | `GET /health` for monitoring. Standard for production APIs. | LOW | None |
| CORS configuration | API consumers need cross-origin access for web apps. | LOW | FastAPI CORS middleware |

### Differentiators

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| Batch scoring endpoint | `POST /api/v1/score/batch` -- score 50 symbols in one request. More efficient for screener use cases. | LOW |
| Score history endpoint | `GET /api/v1/score/{symbol}/history?days=90` -- track score evolution. No competitor offers this as API. | MEDIUM |
| Webhook notifications | Notify subscribers when regime changes or a watched stock's score crosses threshold. | HIGH |
| Regime stream (WebSocket) | `WS /api/v1/regime/stream` -- real-time regime updates. Premium feature for Pro tier. | HIGH |
| Screening endpoint | `GET /api/v1/screen?min_score=70&market=US` -- programmatic screener. Competitors require web UI. | MEDIUM |

### Anti-Features

| Feature | Why Problematic | Alternative |
|---------|-----------------|-------------|
| Position sizing in API response | "Allocate 4.5% of your portfolio" = investment advisory (license required). | Return scores and signals only. Users apply their own sizing. |
| Specific buy/sell recommendations | "BUY AAPL at $180" = investment advisory. | Return "BULLISH/NEUTRAL/BEARISH" as signal strength, not action instruction. |
| User portfolio management | Managing other people's portfolios requires asset management license. | Users manage their own portfolios. API provides data only. |
| Free tier with unlimited access | Attracts abuse, makes monetization impossible. | Strict free tier (5 req/day) to demonstrate value, paid for production use. |
| OAuth2 for authentication | Over-engineered for API key authentication. OAuth2 is for delegated access (social login). | Simple API key in `X-API-Key` header. JWT tokens for session-based access if needed later. |

---

## Cross-Capability Feature Dependencies

```
[Technical Scoring Engine]
    |
    +--requires--> [OHLCV Data] (existing data_ingest context)
    +--feeds-----> [CompositeScore] (existing scoring context, replaces placeholder)
    +--shares----> [ADX Calculation] (with Regime Detection)
    +--feeds-----> [Trend Following Strategy] (in Signal Fusion)
    |
[Regime Detection]
    |
    +--requires--> [VIX Data Feed] (new data source)
    +--requires--> [S&P 500 + 200MA] (new data source)
    +--requires--> [Yield Curve Data] (FRED API or yfinance proxy)
    +--requires--> [ADX for S&P 500] (shared with Technical Scoring)
    +--feeds-----> [RegimeWeightAdjuster] (existing Protocol in scoring/domain/services.py)
    +--feeds-----> [CAN SLIM "M" criterion] (market direction filter)
    +--feeds-----> [RegimeRadar API] (Commercial API)
    |
[Signal Fusion (4 Strategies)]
    |
    +--requires--> [Technical Scoring] (for Trend Following, CAN SLIM relative strength)
    +--requires--> [Fundamental Data] (for CAN SLIM EPS, Magic Formula EBIT)
    +--requires--> [Regime Detection] (for CAN SLIM "M", regime-weighted aggregation)
    +--feeds-----> [SignalFusion API] (Commercial API)
    |
    +-- CAN SLIM:
    |     +--requires--> EPS quarterly/annual growth (existing financial data)
    |     +--requires--> 52-week high proximity (OHLCV)
    |     +--requires--> Relative strength rank (OHLCV, cross-stock calculation)
    |     +--requires--> Institutional ownership % (NEW data: may need additional source)
    |
    +-- Magic Formula:
    |     +--requires--> EBIT (existing financial data)
    |     +--requires--> Enterprise Value (existing financial data)
    |     +--requires--> Net Fixed Assets + Working Capital (existing financial data)
    |
    +-- Dual Momentum:
    |     +--requires--> 12-month returns (OHLCV)
    |     +--requires--> Risk-free rate / T-bill yield (NEW data point)
    |     +--requires--> International equity benchmark (NEW data: e.g., ACWX or EFA)
    |
    +-- Trend Following:
          +--requires--> 20-day / 55-day high-low (OHLCV)
          +--requires--> ADX (shared with Technical Scoring)
          +--requires--> ATR (existing risk management context)

[Korean Market Support]
    |
    +--requires--> [OHLCV Data Adapter for KRX] (new exchange mapping)
    +--requires--> [Korean Financial Statement Adapter] (K-IFRS mapping)
    +--requires--> [KIS Broker Adapter] (new broker integration)
    +--requires--> [Currency Handling (KRW)] (position sizing update)
    +--independent-of--> [Technical Scoring] (same indicators, different data source)
    +--independent-of--> [Regime Detection] (US market regime; Korean market regime is separate concern)
    +--enhances--> [QuantScore API] (multi-market scoring)

[Commercial API (FastAPI)]
    |
    +--requires--> [Scoring Context] (QuantScore product)
    +--requires--> [Regime Context] (RegimeRadar product)
    +--requires--> [Signal Context] (SignalFusion product)
    +--requires--> [Redis] (rate limiting, caching)
    +--independent-of--> [Korean Market] (can launch US-only first)
```

### Critical Dependency Notes

1. **Technical Scoring must come before Signal Fusion.** CAN SLIM needs relative strength, Trend Following needs ADX, both from the technical scoring engine. The `TechnicalScore` placeholder must be real before signal fusion can work.

2. **Regime Detection should come before Signal Fusion.** CAN SLIM's "M" criterion checks market direction. Regime-weighted methodology aggregation requires knowing the current regime. However, Signal Fusion CAN work without regime (just uses default weights).

3. **Korean Market is largely independent.** It can be built in parallel with signal fusion. Only data adapters and broker integration are new -- scoring/signal logic is the same.

4. **Commercial API depends on all three core capabilities working.** Cannot sell QuantScore API until scoring is solid. Cannot sell RegimeRadar until regime detection runs daily. Cannot sell SignalFusion until at least 2-3 methodologies produce real signals.

5. **Institutional ownership data for CAN SLIM "I" criterion** is the hardest data to get for free. yfinance provides `major_holders` but coverage is spotty. Options: (a) use EODHD/FMP institutional data, (b) drop the "I" criterion and score out of 6 instead of 7, (c) defer CAN SLIM institutional criterion. Recommendation: score out of 6, add institutional later.

---

## MVP Definition for v1.1

### Phase 1: Technical Scoring + Regime Wiring (Foundation)

Build first because everything else depends on these:

- [ ] **Technical indicator calculations** (RSI, MACD, MA, ADX, OBV) using TA-Lib or pandas-ta
- [ ] **Composite technical score** (0-100) replacing the `TechnicalScore` placeholder
- [ ] **Regime data ingestion** (VIX, S&P 500 200MA, yield curve)
- [ ] **RegimeWeightAdjuster implementation** (concrete class replacing `NoOpRegimeAdjuster`)
- [ ] **EventBus wiring** for `RegimeChangedEvent` (tech debt fix)
- [ ] **CLI commands**: `regime current`, `score technical AAPL`

### Phase 2: Signal Fusion Strategies (Core Intelligence)

Build second because this creates the "3/4 agreement" value:

- [ ] **Magic Formula implementation** (EBIT-based, uses existing financial data)
- [ ] **Trend Following implementation** (20-day breakout + ADX, uses existing OHLCV + technical indicators)
- [ ] **Dual Momentum implementation** (12-month returns + T-bill, needs international benchmark data)
- [ ] **CAN SLIM implementation** (6/7 criteria without institutional data)
- [ ] **Consensus signal generation** (wire 4 strategies into existing `SignalFusionService.fuse()`)
- [ ] **CLI command**: `signal analyze AAPL`

### Phase 3: Korean Market (Market Expansion)

Build third because it's independent and adds breadth:

- [ ] **KRX data adapter** in `data_ingest` (KOSPI/KOSDAQ via yfinance/EODHD)
- [ ] **Korean financial statement adapter** (K-IFRS field mapping)
- [ ] **KIS broker adapter** (paper trading with mock environment)
- [ ] **Cross-market screening** (US + KR with sector-neutral normalization)
- [ ] **CLI commands**: `score 005930.KS`, `trade kr buy 005930`

### Phase 4: Commercial API (Monetization)

Build last because it wraps everything above:

- [ ] **FastAPI application** with health check, CORS, error handling
- [ ] **API key authentication** and tier-based rate limiting (Redis-backed)
- [ ] **QuantScore endpoints** (`/score/{symbol}`, `/score/{symbol}/detail`, `/screen`)
- [ ] **RegimeRadar endpoints** (`/regime/current`, `/regime/history`)
- [ ] **SignalFusion endpoints** (`/signal/{symbol}`, `/signal/{symbol}/consensus`)
- [ ] **Legal disclaimer middleware** (auto-append to all responses)
- [ ] **Docker deployment configuration**

### Defer to v2+

- [ ] WebSocket streaming for RegimeRadar
- [ ] Webhook notifications for score/regime changes
- [ ] CAN SLIM institutional ownership data ("I" criterion)
- [ ] Korean market-specific regime detection
- [ ] Multi-currency portfolio analytics

---

## Feature Prioritization Matrix

| Feature | User Value | Impl Cost | Strategic Value | Priority |
|---------|------------|-----------|-----------------|----------|
| Technical scoring (5 indicators) | HIGH | LOW | Foundation for signal fusion | P1 |
| Regime data ingestion (VIX, S&P, yield curve) | HIGH | LOW | Required for regime detection to work | P1 |
| RegimeWeightAdjuster concrete impl | HIGH | LOW | Connects regime to scoring (currently NoOp) | P1 |
| Magic Formula implementation | HIGH | MEDIUM | Uses existing financial data, easy win | P1 |
| Trend Following implementation | HIGH | LOW | Uses OHLCV + ADX, straightforward rules | P1 |
| Dual Momentum implementation | MEDIUM | LOW | Simple 12-month return comparison | P1 |
| CAN SLIM implementation (6/7) | MEDIUM | MEDIUM | Requires EPS growth calculation + relative strength | P1 |
| Signal consensus fusion wiring | HIGH | LOW | `SignalFusionService.fuse()` already exists | P1 |
| FastAPI QuantScore endpoint | HIGH | LOW | Core commercial product, reuses existing service | P2 |
| FastAPI RegimeRadar endpoint | HIGH | LOW | Unique commercial product, no competition | P2 |
| FastAPI SignalFusion endpoint | HIGH | LOW | Wraps existing fusion logic | P2 |
| API key auth + rate limiting | HIGH | MEDIUM | Required for commercial viability | P2 |
| KRX data adapter | MEDIUM | MEDIUM | Market expansion | P2 |
| KIS broker integration | MEDIUM | HIGH | New broker integration, token refresh logic | P2 |
| Korean financial statement mapping | MEDIUM | HIGH | K-IFRS differences require field mapping | P2 |
| Batch scoring API endpoint | MEDIUM | LOW | Efficiency for screener use cases | P3 |
| Score history API endpoint | MEDIUM | MEDIUM | Differentiator, no competitor has this | P3 |
| WebSocket regime stream | LOW | HIGH | Premium feature, low initial demand | P3 |
| Webhook notifications | LOW | HIGH | Requires message queue infrastructure | P3 |

**Priority key:**
- **P1**: Must have for this milestone -- creates the core new capabilities
- **P2**: Should have -- enables commercialization and market expansion
- **P3**: Nice to have -- premium features for later iterations

---

## Competitor Feature Analysis (New Capabilities Only)

| Feature | QuantConnect | TradingView | OpenBB | Finviz | Stock Rover | **Ours** |
|---------|-------------|-------------|--------|--------|-------------|----------|
| Technical scoring composite | User-coded | Pine Script indicators | Via libraries | Basic RSI/MACD display | 670 criteria but no composite | **Auto-scored 0-100, weighted by strategy** |
| Regime detection | User-coded | No | No | No | No | **Rule-based 4-regime with 3-day confirmation** |
| Multi-strategy fusion | User-coded | No | No | No | No | **4-strategy consensus with regime-weighted aggregation** |
| Korean market data | Via IBKR | Chart only | Via providers | No | No | **KRX data + KIS broker + scoring** |
| Commercial scoring API | No (platform) | No (platform) | No (OSS toolkit) | Screener only | No API | **REST API with 3 products, tiered pricing** |
| Regime detection API | No | No | No | No | No | **Unique: no competitor offers this** |
| Signal fusion API | No | No | No | No | No | **Unique: 4-strategy consensus as a service** |

### Key Insight

RegimeRadar and SignalFusion as commercial APIs are genuinely novel products. No existing platform offers market regime detection or multi-strategy signal consensus as a standalone API service. This is the commercial differentiation opportunity.

---

## Sources

### Technical Analysis Libraries
- [TA-Lib Python](https://github.com/TA-Lib/ta-lib-python) -- 150+ indicators, C-based performance, Polars/Pandas support
- [Pandas TA](https://github.com/Data-Analisis/Technical-Analysis-Indicators---Pandas) -- 130+ indicators, pure Python, multiprocessing
- [talipp PyPI](https://pypi.org/project/talipp/) -- Incremental indicator calculation

### Regime Detection
- [Regime-Adaptive Trading with HMM and Random Forest (QuantInsti)](https://blog.quantinsti.com/regime-adaptive-trading-python/)
- [Market Regime Detection using HMM (PyQuantLab)](https://www.pyquantlab.com/articles/Market%20Regime%20Detection%20using%20Hidden%20Markov%20Models.html)
- [Regime-Switching Factor Investing with HMM (MDPI)](https://www.mdpi.com/1911-8074/13/12/311)

### Multi-Strategy Methodologies
- [Magic Formula Investing (magicformulainvesting.com)](https://www.magicformulainvesting.com/)
- [Magic Formula Python Implementation (ron-tam.com)](https://www.ron-tam.com/projects/magic)
- [Dual Momentum Strategy Python (Python in Plain English)](https://python.plainenglish.io/dual-momentum-strategy-using-python-a3a7dd337ae3)
- [GEM Python Implementation (GitHub)](https://github.com/alexjansenhome/GEM)
- [Dual Momentum Review (Robot Wealth)](https://robotwealth.com/dual-momentum-review/)
- [Turtle Trading Rules (tosindicators.com)](https://tosindicators.com/research/modern-turtle-trading-strategy-rules-and-backtest)
- [Trend Following Strategies (chartswatcher.com)](https://chartswatcher.com/pages/blog/8-trend-following-strategies-to-boost-profits)

### Korean Market
- [KIS OpenAPI GitHub (official)](https://github.com/koreainvestment/open-trading-api)
- [python-kis (community SDK)](https://github.com/Soju06/python-kis)
- [korea-investment-stock (community wrapper)](https://github.com/kenshin579/korea-investment-stock)
- [KRX Data Marketplace](https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en)

### Commercial API Patterns
- [FastAPI Rate Limiting Best Practices 2025 (techbuddies.io)](https://www.techbuddies.io/2025/12/13/python-rate-limiting-for-apis-implementing-robust-throttling-in-fastapi/)
- [fastapi-limiter (PyPI)](https://pypi.org/project/fastapi-limiter/)
- [API Rate Limiting at Scale (Python in Plain English)](https://python.plainenglish.io/api-rate-limiting-and-abuse-prevention-at-scale-best-practices-with-fastapi-b5d31d690208)

### Existing Codebase (verified)
- `src/regime/domain/services.py` -- RegimeDetectionService with 4-indicator rule-based classification
- `src/regime/domain/value_objects.py` -- VIXLevel (20/30/40 thresholds), TrendStrength (ADX), YieldCurve, SP500Position
- `src/regime/domain/entities.py` -- MarketRegime entity with 3-day confirmation
- `src/scoring/domain/value_objects.py` -- TechnicalScore VO (placeholder), CompositeScore.compute(), STRATEGY_WEIGHTS
- `src/scoring/domain/services.py` -- RegimeWeightAdjuster Protocol, NoOpRegimeAdjuster, CompositeScoringService
- `src/signals/domain/value_objects.py` -- MethodologyType enum (4 strategies), ConsensusThreshold (3/4)
- `src/signals/domain/services.py` -- SignalFusionService.fuse() (consensus logic)

---
*Feature research for: Intrinsic Alpha Trader v1.1 New Capabilities*
*Domain: Technical Scoring, Regime Detection, Signal Fusion, Korean Market, Commercial API*
*Researched: 2026-03-12*
