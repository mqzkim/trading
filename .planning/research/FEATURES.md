# Feature Landscape

**Domain:** AI-Assisted Fundamental Analysis & Valuation Trading System
**Researched:** 2026-03-12 (enhanced with deep competitor analysis)
**Confidence:** HIGH

## Competitor Landscape Summary

Before defining features, understand what exists and where the gaps are.

### Commercial Platforms (Research-Only)

| Platform | Strength | Weakness | Price |
|----------|----------|----------|-------|
| **Stock Rover** | 700+ metrics, Fair Value view (forward DCF), proprietary 0-100 rating engine, 150+ pre-built screeners, 10-year fundamental database | No execution, no position sizing, no risk management, no backtesting, no trade plans | $7.99-27.99/mo |
| **Koyfin** | 500+ metrics, 10+ year historical screening, highest-rated by advisors (9/10 Kitces), 80K+ global companies | No valuation models (analyst estimates only), no execution, no risk tools | $0-49/mo |
| **Alpha Spread** | Best-in-class automated DCF + relative valuation, multi-scenario (base/worst/best), sensitivity analysis, manual DCF calculator | Single-method ensemble only (DCF + relative), no scoring models, no execution, no risk management | $0-24.90/mo |
| **Simply Wall St** | Visual Snowflake (5 axes, 30 checks), open-source analysis model, DCF + DDM + Excess Returns + AFFO models, 95K+ global stocks | Simplified scoring (binary pass/fail per check), no execution, no position sizing, no trade plans | $0-20/mo |
| **Finviz** | Fast screener (67 filters, 8500+ stocks), heat maps, free tier is genuinely useful | Shallow fundamentals (no scoring models), no valuation, no execution, limited historical data (8 years max, Elite only) | $0-39.50/mo |
| **GuruFocus** | Piotroski F-Score, Altman Z-Score, predictability rank, guru portfolio tracking, EPV calculator | Expensive ($499/yr premium), cluttered UI, no execution | $41.58-124.92/mo |

### Quantitative Platforms (Code-First)

| Platform | Strength | Weakness | Price |
|----------|----------|----------|-------|
| **QuantConnect** | Open-source LEAN engine, 400TB+ data, 20+ broker integrations, research notebooks, AI assistant (Mia), 300K+ users | Must code everything from scratch, steep learning curve, fundamental screening requires significant setup | $0-79/mo |
| **QuantRocket** | Zipline backtester (Quantopian successor), JupyterLab, multiple data integrations | Expensive ($19-299/mo), less community than QuantConnect, self-hosted | $19-299/mo |
| **Zipline-Reloaded** | Best for factor-based daily rebalancing, community-maintained Quantopian successor | Minimal maintenance, limited modern data integrations, no live trading built-in | Free (OSS) |

### Open-Source AI Projects (Emerging)

| Project | Strength | Weakness |
|---------|----------|----------|
| **OpenBB Platform** | 100+ data source integrations, Python-first, AI agent support, MCP server, growing ecosystem | Platform/toolkit not a system -- requires assembly, no opinionated strategy |
| **virattt/ai-hedge-fund** (43K+ stars) | 18 specialized agents (Buffett/Graham/Damodaran personas), LangGraph orchestration, React frontend, backtesting | Educational proof-of-concept, not production-grade, depends on LLM for decisions (non-deterministic), requires financialdatasets.ai API |
| **Automated-Fundamental-Analysis** | Rates stocks 0-100 on value/profitability/growth/price, sector-relative scoring | Simple script, no execution, no risk management, unmaintained |

### The Gap Intrinsic Alpha Trader Fills

**No existing retail-accessible tool combines ALL of:**
1. Multi-score quality assessment (F-Score + Z-Score + M-Score + G-Score)
2. Valuation ensemble (DCF + EPV + relative multiples) with disagreement detection
3. Automatic position sizing (Fractional Kelly + ATR)
4. Drawdown defense protocol (tiered escalation)
5. End-to-end pipeline from data to monitored execution
6. Full explainability at every step

Stock Rover does research. Alpaca does execution. QuantConnect requires you to build everything. The virattt/ai-hedge-fund relies on LLMs for decisions (non-deterministic). Nobody provides the opinionated, deterministic, end-to-end pipeline with built-in risk management.

---

## Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete. A fundamental-analysis-driven trading system without these is not credible.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Financial data ingestion** (OHLCV + financial statements) | Cannot analyze without data; every screener has this. Stock Rover has 700+ metrics, Koyfin has 500+, even free Finviz has 67 filters. | M | yfinance for prototyping, EODHD/FMP for production. Need 3+ years history for scoring models. Adjusted close prices mandatory. SEC EDGAR for filings (free, authoritative). |
| **Fundamental scoring** (Piotroski F-Score, Altman Z-Score) | Core screening metrics. GuruFocus, finbox, fintel, Old School Value all offer automated F-Score screening. Equities Lab offers both F-Score and Z-Score testing. | M | F-Score (9 criteria) and Z-Score (bankruptcy risk) are the minimum viable scoring. Beneish M-Score and Mohanram G-Score add differentiation but are less commonly automated (only GuruFocus has M-Score readily available). |
| **Stock screener / ranking** | Every platform from Finviz (free, 67 filters) to Koyfin (500+ metrics with 10-year historical) offers this. Users expect to filter a universe by criteria. Stock Rover's weighted rating (0-100) is the current best-in-class. | M | CLI table output sufficient for v1. Must support custom filter combos (e.g., F-Score >= 7 AND Z-Score > 2.5). Stock Rover's approach of weighting criteria and floating best matches to top is the right UX pattern. |
| **Valuation model** (at least DCF) | Alpha Spread auto-calculates intrinsic value with multi-scenario DCF. Simply Wall St uses 4 DCF variants (2-Stage, DDM, Excess Returns, AFFO) selected by company type. Stock Rover has Fair Value view. Users expect automated valuation, not spreadsheets. | XL | Ensemble approach (DCF + EPV + relative multiples) is correct. Simply Wall St's model selection by company type (financials -> Excess Returns, REITs -> AFFO) is smart -- we should at minimum distinguish financial vs non-financial companies. Sensitivity analysis on growth rate and discount rate is table stakes for credibility per Alpha Spread. |
| **Margin of safety calculation** | Fundamental to value investing since Graham. Every valuation tool (Alpha Spread, Simply Wall St, GuruFocus) shows premium/discount vs intrinsic value. | S | `(intrinsic_value - market_price) / intrinsic_value`. Target 20-30% minimum margin. Alpha Spread shows base/worst/best case scenarios -- showing the range is more honest than a single number. |
| **Stop-loss and take-profit levels** | Any trading system without risk boundaries is irresponsible. ATR-based stops (2.5-3.5x ATR(21)) are industry standard for position trading. Trailing stops that lock in gains while protecting against declines are expected. | M | Need both initial stop and trailing stop logic. ATR-multiples for volatility adjustment (not fixed percentages) are the modern standard per 2025 best practices. |
| **Position sizing** | Required to prevent ruin. Fractional Kelly (Half or Quarter Kelly) is the recommended practical approach -- full Kelly is too aggressive (max drawdown -24.6% at 2% risk per trade is the optimal balance per BacktestBase analysis). | M | Fractional Kelly (1/4 Kelly) already designed. Must integrate with ATR-based stop distance and portfolio-level constraints. |
| **Backtesting** | No credible systematic strategy goes live without historical validation. QuantConnect (cloud, 400TB+ data), Zipline-Reloaded (factor-native), and bt (portfolio-level) are the established options. | XL | Must test full pipeline: screening -> scoring -> signal -> position sizing -> execution simulation. Walk-forward validation essential (Zipline-Reloaded is "factor-native" and best suited for daily selection/rebalancing models per Python backtesting landscape 2026 survey). |
| **Trade plan generation** | Users expect structured output: what to buy, at what price, stop-loss, take-profit, position size. TradersPost auto-calculates exits; capitalise.ai generates plans from natural language. The bar is rising. | S | Text/JSON output combining signal, entry price, stop-loss, take-profit, position size, and reasoning. The "reasoning" part is the differentiator -- most tools give a number, we give the WHY. |
| **Paper trading** | Every serious platform offers simulation before real money. Alpaca Paper Trading is free, supports bracket orders, sub-10ms latency via SIP streams, 99.9% uptime. The MCP server even allows LLM-driven trading. | M | Alpaca Paper Trading API via alpaca-py SDK. Must log all fills, slippage, and compare realized vs planned execution. Bracket orders (entry + stop + target as a single order) are the correct execution pattern. |
| **Portfolio view** | Users need current holdings, exposure, P&L, risk metrics at a glance. PortfoliosLab shows drawdown charts, Sharpe ratio, beta, alpha. Stock Rover tracks performance vs benchmarks. | M | CLI dashboard showing positions, weights, sector exposure, unrealized P&L, drawdown from high-water mark. Rich/Textual library for formatted tables. |
| **Alerting / monitoring** | Positions need monitoring. Stock Alarm supports 65,000+ assets with triggers on price, volume, RSI, MACD via push/email/SMS. Yahoo Finance provides free price alerts. The bar is low but expectations exist. | M | Price-based alerts (stop hit, target reached) plus fundamental alerts (earnings miss, guidance change, score degradation). Daily batch check is sufficient for mid-term holding period -- no need for real-time streaming. |
| **Human approval workflow** | For a system targeting serious retail investors, automated execution without human review is a dealbreaker in v1. PROJECT.md constraint: "V1 requires explicit human approval before any live order." | S | Present trade plan, wait for explicit approval before order submission. Simple y/n CLI prompt is enough. Show full reasoning alongside the decision. |
| **Watchlist management** | Track candidates before they hit entry price. Every screener and broker app has this. Stock Rover watchlists include fundamentals, ratings, and performance tracking. | S | CRUD on SQLite, monitor price vs. entry target. Track when screened candidates approach entry zone. |

### Complexity Key
- **S (Small)**: 1-3 days, well-understood problem, few external dependencies
- **M (Medium)**: 3-10 days, moderate complexity, some integration work
- **L (Large)**: 10-20 days, significant complexity, multiple components
- **XL (Extra Large)**: 20+ days, high complexity, multiple integrations, iterative refinement needed

---

## Differentiators (Competitive Advantage)

Features that set the product apart. Not required for basic operation, but these are where Intrinsic Alpha Trader competes against generic screeners and robo-advisors.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Explainable scoring with full audit trail** | Every score traces to specific data points. Stock Rover shows a 0-100 rating but buries the "why" behind a paywall. Simply Wall St shows binary pass/fail per check but not the underlying calculation. Alpha Spread shows model inputs but only for valuation. This system shows WHY at every layer: which F-Score criteria passed/failed, what drove the Z-Score, why the DCF disagreed with EPV. | M | Core differentiator per PROJECT.md: "Every recommendation must be explainable and risk-controlled." This is what Simply Wall St's open-source model aspires to but doesn't fully deliver in their product (simplified to colored Snowflake). |
| **Safety filter hard gates** (Z-Score + M-Score) | Auto-reject companies with bankruptcy risk (Z < 1.81) or earnings manipulation (M > -1.78) before scoring begins. Most screeners treat these as optional filters. Stock Rover doesn't even expose M-Score. GuruFocus has both but as optional columns, not enforced gates. | S | Prevents the common retail mistake of buying "cheap" stocks that are cheap for good reason. The dual-gate pattern (bankruptcy risk + fraud risk) is unusual in retail tools. |
| **Valuation ensemble with confidence bands** | No single valuation model is reliable. Alpha Spread does DCF + relative but in parallel, not as a weighted ensemble. Simply Wall St selects ONE model based on company type (2-Stage DCF, DDM, Excess Returns, AFFO). This system runs DCF + EPV + relative simultaneously and flags when models disagree significantly. | XL | EPV (no growth assumptions) acts as conservative floor. DCF (growth-dependent) acts as optimistic ceiling. When they converge, high conviction. When they diverge by >30%, low confidence -- stay away. This ensemble logic is how institutional analysts think but is not available in any retail tool. |
| **Multi-methodology signal consensus** | CAN SLIM + Magic Formula + Dual Momentum + Trend Following running in parallel with regime-weighted aggregation. The virattt/ai-hedge-fund runs multiple "investor persona" agents but relies on LLMs (non-deterministic). This system uses deterministic rule-based strategies. | XL | 3/4 agreement for strong signal, regime-based weight adjustment. Deterministic > LLM-based for reproducibility and backtestability. |
| **Regime-adaptive weighting** | Strategy weights shift based on market regime (bull/bear, low/high vol). No retail tool does this. QuantConnect users can code it, but it's not built-in. | L | Requires regime-detect skill (VIX, yield curve, breadth indicators). Changes how fundamental vs technical vs momentum scores are weighted. In bear markets, emphasize quality (Z-Score, health); in bull markets, emphasize growth (G-Score, earnings momentum). |
| **Three-tier drawdown defense protocol** | Systematic risk escalation (10% warn -> 15% reduce -> 20% liquidate) with enforced cooling periods. No retail tool enforces this. Most give you a max drawdown metric after the fact (PortfoliosLab, Portfolio Visualizer). | M | Already designed in risk-auditor agent. Prevents the behavioral trap of "diamond hands" during crashes. The 2% per-trade risk level with Half Kelly produces optimal +95% returns with manageable -24.6% max drawdown per BacktestBase analysis. |
| **Sector-neutral normalization** | All scores ranked within GICS sector before composite calculation. Stock Rover's 0-100 rating already does industry-relative ranking -- this is proven UX. Simply Wall St compares against sector peers. The key is making this automatic and transparent. | M | Requires sector classification data and minimum peer count (10+). Prevents tech always scoring higher on growth metrics than utilities. Stock Rover validates this approach commercially. |
| **Beneish M-Score as hard gate** | Earnings manipulation detection. Only GuruFocus automates this among commercial platforms. Most retail investors have never heard of it. Catching fraud before it crashes saves portfolios. | S | 8-variable formula. Combined with Z-Score as dual safety gate. This two-gate pattern (bankruptcy + fraud) is genuinely differentiated for retail. |
| **Mohanram G-Score** | Growth stock quality scoring complements value-focused F-Score. Bridges value and growth investing. Very few platforms automate this (virtually none in retail). | S | 8-point binary scoring. Extends the system beyond deep value into quality growth. Broadens addressable user base. |
| **EPV (Earnings Power Value)** | Alternative to DCF that avoids growth assumptions. Bruce Greenwald's methodology. Available on Old School Value and MarketXLS but not automated in any major screener. | M | Normalized earnings / cost of capital. EPV acts as "what is this company worth if it never grows?" -- a conservative anchor that makes the ensemble more robust. |
| **Daily automated screening workflow** | Scheduled daily scan of entire US market universe. Stock Rover does this with screener alerts. Alpha Spread has watchlist alerts. But neither generates trade plans from screening results. | M | Cron-style daily job: data refresh -> score -> rank -> filter -> generate trade plans for top N -> notify user. Transforms from "pull" (user queries) to "push" (system surfaces opportunities). |
| **Score trend tracking** | Detect improving/deteriorating fundamentals over quarters. Simply Wall St shows historical Snowflake changes. Stock Rover shows 10-year trend data. But neither alerts on score degradation for held positions specifically. | M | Track F-Score, Z-Score changes across quarters. Alert when scores degrade below thresholds for held positions. "Your held stock XYZ's F-Score dropped from 8 to 5 this quarter" is actionable intelligence. |
| **Bias checker** | Detect disposition effect, recency bias, overconcentration from trading history. No commercial platform actively diagnoses behavioral patterns. TradesViz journals track metrics but don't diagnose biases. | M | Needs months of decision history to detect patterns. "You've held 3 losing positions past their stop-loss in the last month -- disposition effect detected." Genuinely novel for retail. |
| **Company-type-aware valuation model selection** | Simply Wall St's approach of selecting DCF variant by company type (financials -> Excess Returns, REITs -> AFFO, dividend payers -> DDM) is correct. Most tools apply one model to all companies. | M | Minimum: distinguish financial vs non-financial companies (Excess Returns vs 2-Stage DCF). Advanced: REITs (AFFO), utilities (DDM), growth (revenue-based DCF). Prevents applying inappropriate models. |

---

## Anti-Features (Commonly Requested, Deliberately NOT Built)

Features that seem good but create problems. Explicitly NOT building these, with reasoning.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Full auto-execution in v1** | "Just let the AI trade for me" | Untested strategies with real money = guaranteed losses. Paper trading validation is non-negotiable. Auto-execution also creates regulatory and liability exposure. The virattt/ai-hedge-fund explicitly warns "not intended for real trading." | Paper trading first with human approval workflow. Graduate to semi-auto only after demonstrated positive expectancy over 3+ months. |
| **Real-time intraday trading** | "More data = better decisions" | Mid-term holding (1-3 months) doesn't benefit from tick data. Intraday data is expensive, creates latency requirements, and encourages overtrading. Daily granularity is optimal for position trading. Alpaca SIP streams are available but unnecessary for this use case. | Daily EOD data with batch processing. ATR-based stops provide sufficient granularity for 1-3 month holds. |
| **Social/sentiment from Reddit/Twitter** | "The crowd knows something" | Social sentiment is extremely noisy, easily manipulated, and has negative predictive value for mid-term holding periods. Meme stock detection fights the system's value investing thesis. 2025 research shows integration requires sophisticated NLP that adds massive complexity. | Analyst revision sentiment + insider trading patterns (structured, reliable data) instead of unstructured social media noise. SEC EDGAR insider transactions are free and reliable. |
| **Options and derivatives** | "I want leverage and hedging" | Massive complexity increase (Greeks, expiry management, combinatorial strategies). Completely different risk model. Dilutes focus from the core stock-picking mission. Even QuantConnect treats options as a separate asset class. | Stock-only for MVP and v1. Protective puts only in v2+ as a separate bounded context, if portfolio hedging demand is validated. |
| **Web GUI dashboard in v1** | "CLI is not user-friendly" | Building a web UI before the core engine is validated is premature optimization. The virattt/ai-hedge-fund spent significant effort on a React frontend that doesn't improve strategy quality. Web dashboards consume 40-60% of total effort. | CLI-first (Rich/Textual for formatted tables). Streamlit dashboard as first GUI in v1.x -- 10x faster to build than React/Next.js and sufficient for single-user operation. |
| **Multi-market support (Korea, Europe)** | "I trade globally" | Different data sources, market hours, accounting standards, regulatory environments. Koyfin covers 80K+ global companies but is a research-only platform with no execution. Each market doubles integration effort. | US market only for MVP (best data availability, Alpaca supports US, most liquid market). Korean market as first expansion in v2. |
| **ML-based price prediction** | "AI should predict where the price goes" | False precision creates false confidence. Overfitting risk is enormous. The virattt/ai-hedge-fund uses LLMs for decisions, making strategies non-reproducible and non-backtestable. Explainability nightmare -- contradicts core value. | Rule-based scoring with transparent formulas. Composite scores rank candidates, not predict prices. Deterministic > stochastic for this domain. |
| **Prediction confidence percentages** | "Tell me the probability this stock goes up" | A "78% buy probability" implies calibrated probabilistic forecasting that scoring models do NOT provide. Dangerous false precision that encourages over-sizing positions. | Ordinal rankings (STRONG BUY / BUY / HOLD / SELL) with clear reasoning, not pseudo-probabilities. Ensemble agreement level (3/4 models agree = high conviction) is honest confidence communication. |
| **Copy trading / social features** | "Let me follow top performers" | Orthogonal to explainable, risk-controlled value proposition. Encourages blind following without understanding. Simply Wall St has community features but they're disconnected from their analysis model. | Focus on explainability so users learn to make their own decisions. The audit trail IS the educational tool. |
| **Portfolio optimization (mean-variance)** | "Optimize my Sharpe ratio" | Assumes normal distribution of returns (doesn't hold). Extremely sensitive to input estimation errors. Results in unstable, over-concentrated portfolios. Academic consensus increasingly favors constraints over optimization. | Simpler Fractional Kelly + max sector allocation limits (8% single stock, 25% sector). Constraints-based approach rather than optimization-based. |
| **High-frequency execution optimization** | "Minimize execution cost with smart routing" | Position trading with limit orders has negligible market impact. Smart order routing only matters at institutional scale. QuantConnect supports FIX 5.0 for $5B+ monthly volume -- irrelevant for retail. | Simple limit orders via Alpaca API with basic slippage tracking. Bracket orders (entry + stop + target) are the correct execution pattern. |
| **LLM-based decision making** | "Use GPT to analyze stocks" | Non-deterministic outputs make backtesting impossible. Different results on re-run. No audit trail of reasoning that's reproducible. The virattt/ai-hedge-fund's biggest weakness is LLM dependency. | Rule-based scoring is deterministic, backtestable, and explainable. LLMs can summarize/explain results (presentation layer) but must not make the investment decision (domain layer). |

---

## Feature Dependencies

```
[Data Ingestion Pipeline]
    |
    +--requires--> [Financial Data Sources (yfinance/EODHD/FMP + SEC EDGAR)]
    |
    +--feeds------> [Fundamental Scoring Engine]
    |                   |
    |                   +--requires--> [Safety Filters (Z-Score, M-Score)] -- HARD GATES
    |                   +--requires--> [Sector Classification Data (GICS)]
    |                   +--feeds-----> [Valuation Engine]
    |                   |                  |
    |                   |                  +--requires--> [Company Type Classification]
    |                   |                  |              (financial/REIT/dividend/growth)
    |                   |                  +--feeds--> [Signal Engine]
    |                   |                                  |
    |                   +--feeds------------------------> [Signal Engine]
    |                                                      |
    +--feeds------> [Technical Indicators]                 |
    |                   +--feeds------------------------> [Signal Engine]
    |                                                      |
    +--feeds------> [Market Regime Detection]              |
                        +--feeds (weights)---------------> [Signal Engine]
                                                           |
                                                           +--feeds--> [Trade Plan Generation]
                                                                           |
                                                                           +--requires--> [Position Sizing Engine]
                                                                           |                  +--requires--> [Risk Management Engine]
                                                                           |                  +--requires--> [Portfolio State]
                                                                           |
                                                                           +--feeds--> [Human Approval Workflow]
                                                                                           |
                                                                                           +--feeds--> [Order Execution (Alpaca)]
                                                                                                           |
                                                                                                           +--feeds--> [Portfolio Monitoring]
                                                                                                           +--feeds--> [Alerting Engine]

[Backtesting Engine]
    +--requires--> [Data Ingestion Pipeline]
    +--requires--> [Scoring Engine]
    +--requires--> [Signal Engine]
    +--requires--> [Position Sizing Engine]
    +--validates-> [Strategy Parameters (before live)]

[Performance Attribution]
    +--requires--> [Portfolio Monitoring]
    +--requires--> [Execution Logs]
    +--enhances--> [Strategy Improvement Loop]

[Daily Screening Workflow]
    +--requires--> [Data Ingestion Pipeline]
    +--requires--> [Scoring Engine]
    +--requires--> [Signal Engine]
    +--enhances--> [Trade Plan Generation]

[Watchlist Management]
    +--requires--> [Stock Screener / Ranking]
    +--enhances--> [Monitoring / Alerting]

[Bias Checker]
    +--requires--> [Execution Logs (weeks of history)]
    +--requires--> [Portfolio Monitoring]
    +--enhances--> [Human Approval Workflow]

[Score Trend Tracking]
    +--requires--> [Scoring Engine (multi-quarter history)]
    +--enhances--> [Alerting Engine]
    +--enhances--> [Portfolio Monitoring]
```

### Dependency Notes

- **Scoring Engine requires Data Ingestion:** Cannot calculate F-Score, Z-Score, M-Score without 3+ years of financial statements and price data. This is the absolute foundation.
- **Safety filters are HARD GATES:** Z-Score and M-Score must execute before any further analysis. No point valuing a bankrupt or fraud-risk company.
- **Valuation Engine requires company type classification:** Simply Wall St's model selection by company type is correct -- applying a standard 2-Stage DCF to a bank (which requires Excess Returns model) produces garbage. At minimum: financial vs non-financial distinction.
- **Signal Engine requires Scoring + Valuation (minimum):** Basic signal = quality score + valuation gap. Technical indicators and regime detection enhance but don't block.
- **Trade Plan requires Signal + Position Sizing + Risk:** A trade plan without size, stop, and target is just an opinion, not an actionable plan.
- **Backtesting is parallel to but validates the live pipeline:** Same code path as live, replayed against historical data. Must be built alongside, not after, the scoring/signal pipeline. Zipline-Reloaded is the recommended engine for factor-based daily rebalancing.
- **Performance Attribution requires live execution history:** Can only be built after paper trading generates sufficient data (weeks/months of trades).
- **Bias Checker requires execution logs:** Needs months of user decisions to detect patterns.
- **Regime Detection enhances but doesn't block Signal Engine:** Basic signals work without regime awareness.

---

## MVP Definition

### Launch With (v1)

Minimum viable product -- validates that fundamental scoring + valuation ensemble produces actionable, risk-controlled trade plans.

- [ ] **Data ingestion pipeline** -- yfinance for prototyping, OHLCV + financial statements for US market
- [ ] **Safety filters** (Altman Z-Score >= 1.81, Beneish M-Score < -1.78) -- hard gates before any analysis
- [ ] **Fundamental scoring** (Piotroski F-Score + composite scoring) -- core quality assessment
- [ ] **Valuation engine** (DCF + EPV + relative multiples ensemble) -- identify undervalued companies
- [ ] **Margin of safety calculation** -- premium/discount with 20-30% target
- [ ] **Stock screener/ranker** -- filter US market universe by composite score, show top N
- [ ] **Basic signal generation** -- combine fundamental score + valuation gap into BUY/HOLD signal
- [ ] **Position sizing** (Fractional Kelly + ATR stops) -- right-sized positions with defined risk
- [ ] **Trade plan generation** -- entry, stop, target, size, reasoning in structured output
- [ ] **Human approval workflow** -- CLI prompt before any order submission
- [ ] **Alpaca paper trading** -- execute approved plans in paper mode with bracket orders
- [ ] **Basic CLI dashboard** -- portfolio view, P&L, current positions (Rich/Textual)
- [ ] **Backtesting engine** (basic) -- walk-forward validation on historical data
- [ ] **Watchlist management** -- track screened candidates, monitor vs entry targets

### Add After Validation (v1.x)

Features to add once core scoring/valuation pipeline is validated through paper trading results.

- [ ] **Daily automated screening** -- once manual screening confirms pipeline quality
- [ ] **Regime detection** -- when paper trading shows strategy underperforms in specific conditions
- [ ] **Multi-methodology signal consensus** (CAN SLIM, Magic Formula, Dual Momentum, Trend Following)
- [ ] **Regime-adaptive weighting** -- connect regime detection to strategy weights
- [ ] **Alerting engine** (price + fundamental alerts) -- once positions need monitoring
- [ ] **Mohanram G-Score integration** -- extend to growth stock assessment
- [ ] **Sector-neutral normalization** -- refine scoring precision
- [ ] **Company-type-aware valuation model selection** -- financial vs non-financial distinction
- [ ] **Score trend tracking** -- detect improving/deteriorating fundamentals
- [ ] **Streamlit dashboard** -- first GUI when CLI friction is a bottleneck
- [ ] **EODHD/FMP data source upgrade** -- when yfinance free tier limits are hit
- [ ] **Explainable audit trail (enhanced)** -- detailed sub-score breakdown in reports

### Future Consideration (v2+)

Features requiring extensive execution history, representing market expansion, or adding qualitative layers.

- [ ] **SEC filing NLP analysis** (10-K/10-Q narrative) -- using EdgarTools + LLM for qualitative signals
- [ ] **Performance attribution** -- decompose returns by factor with sufficient trade history
- [ ] **Bias checker** -- detect behavioral patterns after months of decisions
- [ ] **Semi-automated execution** -- human approves plan, system manages orders
- [ ] **Korean market (KOSPI/KOSDAQ)** -- second market expansion
- [ ] **Earnings call transcript analysis** -- tone change detection via FinBERT/LLM
- [ ] **Options hedging** (protective puts only) -- separate bounded context
- [ ] **Insider transaction monitoring** -- SEC EDGAR insider trading signals

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Strategic Importance | Priority |
|---------|------------|---------------------|---------------------|----------|
| Data ingestion pipeline | HIGH | M | Foundation for everything | P1 |
| Safety filters (Z/M-Score) | HIGH | S | Core differentiator (dual gate) | P1 |
| Fundamental scoring (F-Score + composite) | HIGH | M | Primary analysis capability | P1 |
| Valuation ensemble (DCF+EPV+relative) | HIGH | XL | Core differentiator (ensemble) | P1 |
| Stock screener / ranker | HIGH | M | Primary user interaction | P1 |
| Basic signal generation | HIGH | M | Links scoring to action | P1 |
| Position sizing (Fractional Kelly) | HIGH | M | Risk management foundation | P1 |
| Trade plan generation | HIGH | S | Core output of the system | P1 |
| Backtesting engine (basic) | HIGH | XL | Validates entire pipeline | P1 |
| Human approval workflow | MEDIUM | S | Safety constraint | P1 |
| Alpaca paper trading | HIGH | M | Execution validation | P1 |
| Basic CLI dashboard | MEDIUM | M | User experience baseline | P1 |
| Watchlist management | MEDIUM | S | Candidate tracking | P1 |
| Daily automated screening | HIGH | M | Workflow automation | P2 |
| Regime detection | MEDIUM | L | Market adaptability | P2 |
| Multi-methodology signals | HIGH | XL | Ensemble signal strength | P2 |
| Alerting engine | MEDIUM | M | Position monitoring | P2 |
| Sector-neutral normalization | MEDIUM | M | Scoring precision | P2 |
| Score trend tracking | MEDIUM | M | Proactive risk management | P2 |
| Explainable audit trail (enhanced) | HIGH | M | Core value proposition | P2 |
| Streamlit dashboard | MEDIUM | M | UX improvement | P2 |
| Company-type valuation selection | MEDIUM | M | Valuation accuracy | P2 |
| SEC filing NLP | MEDIUM | L | Qualitative analysis layer | P3 |
| Performance attribution | MEDIUM | L | Strategy improvement | P3 |
| Bias checker | LOW | M | Behavioral insight | P3 |
| Korean market | LOW | XL | Market expansion | P3 |

**Priority key:**
- **P1**: Must have for launch -- validates the core thesis
- **P2**: Should have -- adds strategic depth once core is validated
- **P3**: Nice to have -- requires history, represents expansion, or adds qualitative layer

---

## Detailed Competitor Feature Matrix

| Feature | Stock Rover | Alpha Spread | Koyfin | Simply Wall St | Finviz | QuantConnect | GuruFocus | OpenBB | **Ours** |
|---------|-------------|--------------|--------|---------------|--------|-------------|-----------|--------|----------|
| **Piotroski F-Score** | Via 670 criteria | No | No | Via checks | No | User-coded | Yes | Via data | Auto-scored with sub-criteria breakdown |
| **Altman Z-Score** | Via criteria | No | No | Via health checks | No | User-coded | Yes | Via data | Hard gate (Z >= 1.81) |
| **Beneish M-Score** | No | No | No | No | No | User-coded | Yes (paid) | No | Hard gate (M < -1.78) |
| **Mohanram G-Score** | No | No | No | No | No | User-coded | No | No | Planned (v1.x) |
| **DCF valuation** | Fair Value (forward DCF) | Multi-scenario DCF | No (analyst est. only) | 4 variants by type | No | User-coded | Yes | Via data | DCF as ensemble member |
| **EPV valuation** | No | No | No | No | No | User-coded | Yes | No | EPV as conservative floor |
| **Relative valuation** | Peer comparison | Relative value model | Peer metrics | Peer comparison | Basic ratios | User-coded | Yes | Via data | Multiple-based (PER/PBR/EV) |
| **Valuation ensemble** | No | DCF + relative (parallel) | No | Single model selected | No | User-coded | No | No | **DCF + EPV + relative (weighted, disagreement detection)** |
| **Sensitivity analysis** | No | Yes (sliders) | No | No | No | User-coded | No | No | Growth rate + discount rate ranges |
| **Screener** | 700+ metrics, 150 prebuilt | Valuation-based | 500+ metrics | Snowflake-based | 67 filters | Algorithmic | 20+ guru screens | Programmatic | CLI, composite-score ranked |
| **Backtesting** | Limited (portfolio) | None | None | None | None | Full engine (LEAN) | None | None | Walk-forward validation |
| **Risk management** | None | None | None | None | None | User-coded | None | None | **Fractional Kelly + ATR + 3-tier drawdown** |
| **Position sizing** | None | None | None | None | None | User-coded | None | None | **Automatic via Fractional Kelly** |
| **Trade plan generation** | None | None | None | None | None | User-coded | None | None | **Entry/stop/target/size/reasoning** |
| **Order execution** | None | None | None | None | None | 20+ brokers | None | None | Alpaca (paper first) |
| **Human approval** | N/A | N/A | N/A | N/A | N/A | Optional | N/A | N/A | **Mandatory in v1** |
| **Regime detection** | None | None | None | None | None | User-coded | None | None | VIX + yield curve + breadth |
| **Explainability** | Raw metric values | Model input display | Raw data | Snowflake + checks | Minimal | Code IS explanation | Guru methodology | Data access | **Full audit trail at every layer** |
| **Fraud detection** | None | None | None | None | None | User-coded | M-Score available | None | **M-Score hard gate (auto-reject)** |
| **Drawdown defense** | None | None | None | None | None | User-coded | None | None | **3-tier protocol (10/15/20%)** |
| **Bias detection** | None | None | None | None | None | None | None | None | **Planned (v2+)** |
| **Price** | $8-28/mo | $0-25/mo | $0-49/mo | $0-20/mo | $0-40/mo | $0-79/mo | $42-125/mo | Free (OSS) | Free (self-hosted) |

### Key Competitive Insights

1. **Research-execution divide:** Stock Rover, Koyfin, Alpha Spread, Simply Wall St, and Finviz are all research-only. None generate trade plans or manage positions. QuantConnect bridges both but requires coding everything.

2. **Risk management void:** No commercial retail platform provides automatic position sizing, drawdown defense, or systematic risk management. This is the single biggest gap in the market. Retail investors are left to figure out position sizing and stop management on their own.

3. **Explainability gap:** Simply Wall St comes closest with their Snowflake (30 binary checks across 5 dimensions) and open-source model, but the visual simplification loses the detailed reasoning. Stock Rover's 0-100 rating is a black box. Our full audit trail (sub-score breakdown, data lineage, reasoning at each step) fills this gap.

4. **Valuation ensemble is genuinely novel:** Alpha Spread does DCF + relative in parallel but not as a weighted ensemble with disagreement detection. Simply Wall St selects one model per company type but doesn't combine them. Nobody does DCF + EPV + relative as a confidence-weighted ensemble with divergence flags.

5. **Fraud detection as mandatory gate:** Only GuruFocus offers Beneish M-Score, and it's a $500/year premium feature displayed as an optional metric, not a hard gate. Making fraud detection a mandatory pre-screening gate is genuinely differentiated.

6. **AI hedge fund comparison:** The virattt/ai-hedge-fund (43K+ stars) proves market demand for multi-agent trading analysis. But its LLM dependency makes decisions non-deterministic and non-backtestable. Our deterministic, rule-based approach is more reliable for real money.

---

## Sources

### Commercial Platform Research
- [Stock Rover - Investment Research Platform](https://www.stockrover.com/)
- [Stock Rover Review 2026 - StockBrokers.com](https://www.stockbrokers.com/review/tools/stockrover)
- [Stock Rover: 92 Tests - Liberated Stock Trader](https://www.liberatedstocktrader.com/stock-rover-review-screener-value-investors/)
- [Alpha Spread - Stock Valuation Platform](https://www.alphaspread.com/)
- [Alpha Spread DCF Calculator](https://www.alphaspread.com/dcf-value-calculator)
- [Koyfin Features](https://www.koyfin.com/features/)
- [Koyfin Review 2026 - TraderHQ](https://traderhq.com/koyfin-review-best-investment-analysis-tool/)
- [Simply Wall St - Analysis Model (GitHub)](https://github.com/SimplyWallSt/Company-Analysis-Model)
- [Simply Wall St - Snowflake Methodology](https://support.simplywall.st/hc/en-us/articles/360001740916-How-does-the-Snowflake-work)
- [Simply Wall St - Valuation Documentation](https://support.simplywall.st/hc/en-us/articles/4751563581071-Understanding-the-Valuation-section-in-the-company-report)
- [Finviz - Stock Screener](https://finviz.com/)
- [Finviz Review 2026 - Bullish Bears](https://bullishbears.com/finviz-review/)
- [GuruFocus - EPV Calculator](https://www.gurufocus.com/glossary/EPV)

### Quantitative Platform Research
- [QuantConnect - Algorithmic Trading Platform](https://www.quantconnect.com/)
- [LEAN Engine - Open Source](https://www.lean.io/)
- [QuantRocket - Python Trading Platform](https://www.quantrocket.com/)
- [Zipline/Quantopian Successor Guide](https://www.quantrocket.com/alternatives/quantopian/)
- [Python Backtesting Landscape 2026](https://python.financial/)
- [10 Best Python Backtesting Libraries - QuantVPS](https://www.quantvps.com/blog/best-python-backtesting-libraries-for-trading)

### Open-Source AI Projects
- [virattt/ai-hedge-fund (43K+ stars)](https://github.com/virattt/ai-hedge-fund)
- [AI Hedge Fund Architecture - DeepWiki](https://deepwiki.com/virattt/ai-hedge-fund/2-system-architecture)
- [AI Hedge Fund Analysis - DecisionCrafters](https://www.decisioncrafters.com/ai-hedge-fund-the-revolutionary-multi-agent-trading-system-thats-transforming-financial-ai-with-43k-github-stars/)
- [OpenBB - AI Workspace for Finance](https://openbb.co/)
- [OpenBB for Financial Analysis Guide](https://dasroot.net/posts/2026/02/openbb-financial-analysis-python-data-retrieval/)
- [Automated Fundamental Analysis - GitHub](https://github.com/faizancodes/Automated-Fundamental-Analysis)

### Domain Research
- [AlphaSense - Fundamental Analysis Tools 2026](https://www.alpha-sense.com/resources/product-articles/fundamental-analysis-tools/)
- [Old School Value - Earnings Power Value (EPV)](https://www.oldschoolvalue.com/stock-analysis/earnings-power-value-epv/)
- [Wall Street Prep - EPV Formula](https://www.wallstreetprep.com/knowledge/earnings-power-value-epv/)
- [StableBread - EPV Methodology](https://stablebread.com/earnings-power-value/)
- [BacktestBase - Kelly Criterion Calculator](https://www.backtestbase.com/education/how-much-risk-per-trade)
- [Alpaca Paper Trading Docs](https://docs.alpaca.markets/docs/paper-trading)
- [Alpaca-py Python SDK](https://alpaca.markets/sdks/python/)
- [EdgarTools - Python SEC EDGAR](https://pypi.org/project/edgartools/)
- [EDGAR-CRAWLER - ACM 2025](https://dl.acm.org/doi/10.1145/3701716.3715289)
- [LLMs for Financial Document Analysis](https://intuitionlabs.ai/articles/llm-financial-document-analysis)
- [Portfolio Risk Management Tools 2026](https://www.wallstreetzen.com/blog/best-portfolio-risk-management-tools/)

---
*Feature research for: Intrinsic Alpha Trader*
*Domain: AI-Assisted Fundamental Analysis & Valuation Trading System*
*Researched: 2026-03-12*
