# Domain Pitfalls

**Domain:** AI-assisted fundamental analysis mid-term trading system (US equities)
**Researched:** 2026-03-12
**Confidence:** HIGH (multiple authoritative sources corroborate each pitfall)

---

## Critical Pitfalls

Mistakes that cause rewrites, invalidate all downstream analysis, or risk capital loss.

---

### Pitfall 1: Look-Ahead Bias in Fundamental Data

**Severity:** CRITICAL
**Phase to address:** Phase 1 -- Data Ingestion Pipeline

**What goes wrong:**
The backtesting engine uses financial data (earnings, balance sheet ratios, SEC filings) that was not yet publicly available at the simulated decision date. For example, a Q4 earnings report filed on February 15 gets used for a simulated trade on January 10. The system shows spectacular backtested returns that evaporate in live trading.

**Why it happens:**
- Free data sources like yfinance and SEC EDGAR provide the *final* version of financial data, not point-in-time snapshots. Financial statements are frequently restated -- revised data silently replaces original data.
- Developers grab the latest financials by ticker and assume they were available historically.
- The Piotroski F-Score, Altman Z-Score, and other scoring inputs all depend on balance sheet and income statement data that has specific filing dates and frequent restatements.
- SEC "revision restatements" (immaterial errors corrected by revising prior periods) are disclosed in footnotes, not in separate notifications. Automated systems miss these entirely.

**Consequences:**
- All backtest results are invalidated. A strategy that appears profitable with a Sharpe ratio of 2.0+ collapses to near-zero in production.
- According to CFA Institute materials, look-ahead bias generates "excessively optimistic results" and "real application is likely to deliver dramatically different results."
- Retrofitting point-in-time awareness after building the system requires a complete data layer rewrite and re-running all backtests.

**Prevention:**
1. Store the `filing_date` (not the period-end date) alongside every financial data point. Never use data before its filing date in backtests.
2. Track SEC EDGAR `filedAt` timestamps for all filings. Build a point-in-time data layer that answers "what did we know on date X?"
3. For the scoring engine (Piotroski F, Altman Z, Beneish M, Mohanram G), always join on filing date, not fiscal period.
4. Add an assertion layer: if a backtest trade uses data with a filing date *after* the trade date, raise an error, not a warning.
5. Accept ~60-90 day lag between fiscal period end and data availability as normal. Q4 data is often not available until mid-February or later.

**Warning signs:**
- Backtested Sharpe ratio exceeds 2.0 on a daily-rebalancing fundamental strategy (suspiciously high for monthly/quarterly-driven signals).
- Backtest performance degrades dramatically (>50% reduction in returns) when you add a 90-day filing lag buffer.
- No `filing_date` or `reported_date` column in the data schema.
- "Very smooth equity curve, a straight line in a log chart" -- classic indicator per Harris (2024).

**References:**
- [CFA Level 2 -- Problems in Backtesting](https://analystprep.com/study-notes/cfa-level-2/problems-in-backtesting/) (HIGH confidence)
- [Look-Ahead Bias -- Corporate Finance Institute](https://corporatefinanceinstitute.com/resources/career-map/sell-side/capital-markets/look-ahead-bias/) (HIGH confidence)
- [Point-in-Time Data -- FactSet Whitepaper](https://insight.factset.com/hubfs/Resources%20Section/White%20Papers/ID11996_point_in_time.pdf) (HIGH confidence)
- [The Seven Sins of Quantitative Investing](https://bookdown.org/palomar/portfoliooptimizationbook/8.2-seven-sins.html) (HIGH confidence)

---

### Pitfall 2: Survivorship Bias in Stock Universe

**Severity:** CRITICAL
**Phase to address:** Phase 1 -- Data Ingestion Pipeline

**What goes wrong:**
The screening and backtesting engine only considers stocks that currently exist in the market. Delisted, bankrupt, and acquired companies are excluded from historical analysis. This inflates backtested returns by 1-4% annually and dramatically understates drawdown risk. A fundamental scoring system that filters for "strong balance sheets" appears to work brilliantly because all the companies that *failed* those filters and subsequently went bankrupt are invisible.

**Why it happens:**
- yfinance and most free data sources only serve data for currently-traded tickers. When a company is delisted, its historical data vanishes or becomes inaccessible.
- Developers naturally build screeners against current ticker lists.
- Quantitative Investment Management (QIM) documented a case where a strategy they expected to yield 20% actually returned only 8% after properly accounting for survivorship bias.
- A dataset covering the last 10 years in North America could exclude up to 75% of the stocks that were actually trading during that period.

**Consequences:**
- 1-4% annual return inflation, which is the difference between a profitable and unprofitable strategy in many cases.
- Drawdown risk is dramatically understated because the worst-performing stocks (the ones that went to zero) are excluded.
- Once discovered in production, requires rebuilding the entire securities master database and re-running all backtests.

**Prevention:**
1. Build the stock universe as a time-series, not a snapshot. For each historical date, define which stocks were available to trade.
2. Source delisted company data explicitly. SEC EDGAR retains filings for delisted companies. Historical price data can be obtained from Sharadar (via Nasdaq Data Link) or by preserving yfinance data before delisting occurs.
3. Include `delisted_date` and `listing_date` fields in the securities master database. Filter the universe per-date during backtests.
4. Validate: run the same backtest with and without survivorship-bias correction. If results differ by more than 1% CAGR, the bias is material.
5. The universe size should vary over time. If it is constant across all historical dates, the data is wrong.

**Warning signs:**
- Stock universe contains only currently-traded tickers with no historical universe reconstruction.
- No `delisted_date`, `listing_date`, or `status` fields in the securities master table.
- The backtest stock universe size is constant across all dates (it should grow/shrink as companies list/delist).
- Backtest does not include any stocks that went to zero.

**References:**
- [Survivorship Bias in Backtesting Explained -- LuxAlgo](https://www.luxalgo.com/blog/survivorship-bias-in-backtesting-explained/) (MEDIUM confidence)
- [Dealing with Delistings -- Alpha Architect](https://alphaarchitect.com/dealing-with-delistings-a-critical-aspect-for-stock-selection-research/) (HIGH confidence)
- [Survivorship Bias in Backtesting -- QuantifiedStrategies](https://www.quantifiedstrategies.com/survivorship-bias-in-backtesting/) (MEDIUM confidence)
- [A Primer on Survivorship Bias -- QuantRocket](https://www.quantrocket.com/blog/survivorship-bias/) (MEDIUM confidence)

---

### Pitfall 3: Value Trap Blindness in Scoring/Screening

**Severity:** CRITICAL
**Phase to address:** Phase 2 (Scoring Engine) + Phase 3 (Signal Engine)

**What goes wrong:**
The scoring engine identifies a stock as "high quality + undervalued" because it has a high Piotroski F-Score (7-9) and trades below intrinsic value per the DCF/EPV model. But the stock is a *value trap* -- fundamentals are deteriorating, and the low price is justified. The system repeatedly recommends positions that lose money despite appearing fundamentally strong.

**Why it happens:**
- Piotroski F-Score is backward-looking: it measures *improvement* over the last 1-2 fiscal periods. A company can score 7/9 while its competitive position is permanently impaired.
- Piotroski's model has been "fiercely criticized" because "the selection of the ratios does not follow any robust methodology, which makes it prone to suffer from selection and human behavioural biases" (CFA UK, 2024).
- The F-Score works best for traditional manufacturing/industrial companies and is less suitable for "service-based firms, tech companies with many intangible assets, or financial institutions" which have different accounting practices.
- Altman Z-Score was designed for manufacturing firms. Software companies with low tangible assets score misleadingly low. Financial firms often cannot report current ratios at all.
- Static valuation models (DCF, relative multiples) do not account for structural decline in earnings power.
- The system lacks a *momentum* or *trend* filter -- fundamental scores alone cannot distinguish "cheap and improving" from "cheap and dying."

**Consequences:**
- Portfolio concentrates in declining industries (brick-and-mortar retail, legacy energy).
- Average holding period loss exceeds 15% despite high aggregate quality scores.
- User loses confidence in the system after repeated losses on "high quality" picks.

**Prevention:**
1. **Momentum overlay (most effective):** Require that the stock is not in a sustained downtrend (e.g., price above 200-day MA, or 6-month relative strength > 0). Per Research Affiliates analysis, this is the single most effective value-trap filter.
2. **Sector-adjusted scoring:** The Piotroski F-Score average differs by industry. Compare scores within sector, not across the entire universe.
3. **Use Z''-Score for non-manufacturing:** Altman's Z''-Score variant is designed for non-manufacturing and service companies. The original Z-Score misclassifies software, tech, and financial companies.
4. **Revenue trajectory checks:** Flag stocks where trailing 3-year revenue is declining even if profitability ratios look healthy.
5. **Strict Beneish M-Score threshold:** Stocks flagged as potential earnings manipulators (M > -1.78) should be excluded regardless of other scores.
6. **Key financial red flags:** Asset quality deterioration (goodwill write-downs >10% of total assets), interest coverage ratios below 1.5x, inventory growing faster than sales by >15%, declining book value per share over 3+ consecutive quarters.

**Warning signs:**
- Portfolio concentrates in declining industries.
- The system has no sector-normalization logic in the scoring engine.
- The screening output contains zero momentum or trend data points.
- Financial companies are consistently excluded or consistently score low.

**References:**
- [Avoiding Value Traps -- Research Affiliates](https://www.researchaffiliates.com/publications/articles/1013-avoiding-value-traps) (HIGH confidence)
- [How Equity Investors Can Avoid Value Traps -- Lord Abbett](https://www.lordabbett.com/en-us/financial-advisor/insights/investment-objectives/2025/how-equity-investors-can-avoid-value-traps.html) (MEDIUM confidence)
- [Why Piotroski's F-Score No Longer Works -- Portfolio123](https://blog.portfolio123.com/why-piotroskis-f-score-no-longer-works/) (MEDIUM confidence)
- [Evolution of Fundamental Scoring Models -- CFA UK](https://www.cfauk.org/pi-listing/man-machine-the-evolution-of-fundamental-scoring-models-and-ml-implications) (HIGH confidence)
- [Imperfections with the Piotroski F-Score -- GuruFocus](https://www.gurufocus.com/news/196826/imperfections-with-the-piotroski-fscore) (MEDIUM confidence)

---

### Pitfall 4: DCF/Valuation Model Brittleness and Systematic Errors

**Severity:** CRITICAL
**Phase to address:** Phase 2-3 -- Valuation Engine

**What goes wrong:**
The automated valuation engine (DCF + EPV + relative multiples ensemble) produces wildly inaccurate intrinsic values. DCF is hypersensitive to assumptions: a 1% change in discount rate changes valuation by 10-15%. Terminal value typically accounts for 60-85% of total DCF value. When automated across hundreds of stocks, small systematic errors compound into systematically biased valuations.

**Why it happens:**
- Automated DCF requires estimating future free cash flows, WACC, and terminal growth -- all subjective. When a human analyst does DCF, they apply judgment. An automated system applies the same formula uniformly, which fails for companies with non-standard capital structures, cyclical earnings, or lumpy CapEx.
- **Maintenance CapEx vs. Growth CapEx is unknowable from GAAP filings.** Companies are not required to disclose this split, and it is not audited. Automated systems typically use total CapEx, which understates FCF for high-growth companies and overstates it for capital-light companies.
- Using depreciation as a proxy for maintenance CapEx is fragile: if the company understates depreciation to manage earnings upward, growth CapEx will be materially overstated.
- Working capital changes are volatile year-to-year. Using a single year's change produces unstable FCF estimates.
- EPV (Earnings Power Value) assumes no growth, which systematically undervalues growth companies and overvalues declining ones.
- **A 0.5% difference in perpetual growth rate can shift enterprise value by tens or hundreds of millions** (Financial-Modeling.com, 2025).

**Consequences:**
- Intrinsic value estimates swing >30% quarter-to-quarter for stable companies.
- Terminal value contribution exceeds 85% for most valuations.
- All stocks in a sector appear uniformly over/undervalued (sector-wide WACC miscalibration).
- The system produces negative intrinsic values from negative FCF + wrong terminal growth assumptions.

**Prevention:**
1. Use the ensemble approach but weight models differently by sector: DCF for stable businesses, EPV for mature cash-cow companies, relative multiples for high-growth companies.
2. Normalize FCF: average working capital changes over 3-5 years, not 1 year. Estimate maintenance CapEx as depreciation * 1.1 (rough proxy) when the company does not disclose it.
3. Cap terminal value contribution: if terminal value exceeds 85% of total DCF, flag the valuation as unreliable and increase the weight of EPV/relative multiples in the ensemble.
4. Implement valuation confidence bands, not point estimates. The signal engine should use the "margin of safety" (difference between price and the *conservative* end of the valuation range), not the midpoint.
5. Validate the valuation engine against known benchmarks: run it against historical analyst consensus targets and measure deviation.
6. Present sensitivity tables: show how valuation changes with +/-1% WACC and +/-0.5% terminal growth rate.
7. **Mismatching FCFF and FCFE with discount rates** is a common error: use WACC to discount FCFF, cost of equity to discount FCFE. Never mix them.

**Warning signs:**
- Intrinsic value estimates swing >30% quarter-to-quarter for stable companies.
- Terminal value contribution exceeds 85% for most valuations.
- The system produces negative intrinsic values.
- All stocks in a sector appear uniformly over/undervalued (sector-wide WACC miscalibration).

**References:**
- [Common Errors in DCF Models -- Wall Street Prep](https://www.wallstreetprep.com/knowledge/common-errors-in-dcf-models/) (HIGH confidence)
- [Terminal Value Sensitivity -- Financial-Modeling.com](https://www.financial-modeling.com/terminal-value-in-dcf-perpetual-growth-rate-sensitivity/) (MEDIUM confidence)
- [5 Common Errors in DCF Models -- Phoenix Strategy Group](https://www.phoenixstrategy.group/blog/5-common-errors-in-dcf-models-and-how-to-fix-them) (MEDIUM confidence)
- [FCF Maintenance CapEx Calculation -- Old School Value](https://www.oldschoolvalue.com/stock-valuation/calculate-maintenance-capital-expenditure-in-fcf/) (MEDIUM confidence)
- [Growth Capex -- Corporate Finance Institute](https://corporatefinanceinstitute.com/resources/valuation/growth-capex/) (HIGH confidence)

---

### Pitfall 5: Kelly Criterion Blow-Up Risk in Position Sizing

**Severity:** CRITICAL
**Phase to address:** Phase 3-4 -- Risk Management Engine

**What goes wrong:**
The Fractional Kelly position sizing recommends positions that are too large, leading to catastrophic drawdowns. Even with the "fractional" adjustment, estimation errors in win rate and payoff ratio cause the Kelly formula to output dangerously oversized positions. A portfolio of multiple Kelly-sized positions with correlated risk factors amplifies the problem.

**Why it happens:**
- Kelly Criterion requires *exact* knowledge of win rate and payoff ratio. In trading, these are estimated from backtests, which are themselves biased. "Errors in the means average about 20 times in importance in objective value than errors in co-variances" (MacLean, Thorp, Ziemba).
- When a trader overestimates true win rate, the Kelly output diverges from optimal, "increasing the risk of ruin."
- Kelly does not account for correlation between positions. Five "independent" Kelly-sized positions in tech stocks share sector and macro risk.
- Full Kelly produces severe drawdowns: >50% peak-to-trough within 250 trades is normal even with a genuine edge.
- ATR-based stop-loss placement interacts with Kelly sizing in non-obvious ways: if ATR is low (calm market), Kelly sizes up aggressively, but ATR-based stops are tight, leading to frequent stop-outs.

**Consequences:**
- A portfolio drawdown exceeding 20% triggers the system's own emergency liquidation protocol, crystallizing losses.
- Estimated win rate of 55% when true win rate is 50% leads to persistent losses compounded by oversized positions.
- Correlated positions blow up simultaneously during market stress events.

**Prevention:**
1. **Use Quarter Kelly (Kelly / 4)** as the default, not Half Kelly. This sacrifices ~25% of optimal growth rate but reduces drawdown severity by ~75%. The project CLAUDE.md already specifies 1/4 Kelly -- enforce this strictly.
2. Implement portfolio-level correlation adjustment: reduce individual position sizes when portfolio-level correlation increases. Use rolling 60-day correlation matrix.
3. Hard-cap individual position size at 5% of portfolio regardless of Kelly output. Hard-cap sector exposure at 25%.
4. The drawdown tiers (10/15/20%) must *override* Kelly sizing -- when portfolio hits 10% drawdown, halve all new position sizes.
5. Stress-test position sizing with pessimistic win-rate estimates: subtract 5-10% from backtested win rate before feeding into Kelly.
6. Never use estimated parameters directly from in-sample backtests as Kelly inputs. Use out-of-sample estimates only.

**Warning signs:**
- Any single position exceeds 10% of portfolio.
- Kelly formula recommends sizes that exceed the hard caps (indicating estimation error, not a genuine edge).
- No correlation-adjustment logic in the position sizer.
- Backtest shows maximum drawdown below 15% (unrealistically optimistic, likely masking estimation bias).

**References:**
- [Kelly Criterion -- Wikipedia (academic citations)](https://en.wikipedia.org/wiki/Kelly_criterion) (HIGH confidence)
- [Tackling Estimation Risk in Kelly Investing -- arXiv (2025)](https://arxiv.org/html/2508.18868v1) (HIGH confidence)
- [Risk-Constrained Kelly Criterion -- QuantInsti](https://blog.quantinsti.com/risk-constrained-kelly-criterion/) (MEDIUM confidence)
- [Why Do Even Excellent Traders Go Broke? -- Medium](https://medium.com/@idsts2670/why-do-even-excellent-traders-go-broke-the-kelly-criterion-and-position-sizing-risk-62c17d279c1c) (MEDIUM confidence)
- [Practical Implementation of the Kelly Criterion -- Frontiers](https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2020.577050/full) (HIGH confidence)

---

### Pitfall 6: Backtesting Overfitting (Data Snooping)

**Severity:** CRITICAL
**Phase to address:** Phase 4 -- Backtesting Engine

**What goes wrong:**
The backtesting engine shows a strategy with a Sharpe ratio of 2.5, 25% CAGR, and maximum drawdown of 8%. In live paper trading, it underperforms the S&P 500. Institutional investors report that **over 90% of academic strategies fail when implemented with real capital** despite generating double-digit annual returns through backtesting.

**Why it happens:**
- With enough parameter combinations (scoring weights, entry thresholds, holding periods, sector filters), it is trivially easy to find a combination that worked historically. Standard backtesting suffers from "multiple testing" -- testing many model variations on the same data without accounting for increased false positive rates (Bailey et al., 2014).
- The developer tests dozens of parameter combinations and (consciously or not) selects the best one. This is data snooping.
- "Meta-overfitting" is a subtler form: optimizing the walk-forward process itself by adjusting window sizes, fitness functions, and parameter ranges until walk-forward results look attractive, defeating the entire purpose of out-of-sample validation.
- Fundamental scoring systems have many tunable parameters: F-Score threshold (6? 7? 8?), valuation discount threshold (20%? 30%?), holding period (30 days? 60? 90?), sector inclusion/exclusion. Each multiplies the search space.

**Consequences:**
- Total strategy invalidation -- the entire development effort is wasted.
- False confidence leads to deploying real capital on a strategy with no genuine edge.
- The system appears to work until it doesn't, often during the worst market conditions (when real edge matters most).

**Prevention:**
1. **Strict train/validate/test split:** Use 2010-2018 for development, 2019-2021 for validation, 2022-present for final test. Never touch the test set until the strategy is finalized.
2. **Limit free parameters to fewer than 10.** A fundamental strategy should have 5-8 tunable parameters total. More parameters = more overfitting risk.
3. **Walk-forward analysis** with caveats: use rolling window optimization, but be aware that WFA itself has "notable shortcomings in false discovery prevention" compared to Combinatorial Purged Cross-Validation (CPCV). Consider implementing both.
4. **Apply the Deflated Sharpe Ratio (DSR)** to adjust for the number of parameter combinations tested. A "significant" Sharpe of 2.0 after testing 100 parameter sets may not be statistically significant.
5. **Apply PBO (Probability of Backtest Overfitting).** Target PBO < 10%.
6. **Require economic sense:** The fundamental thesis must be articulable independent of the backtest results (e.g., "companies with improving profitability and low debt that trade below intrinsic value tend to outperform" is a thesis; "F-Score > 7 AND PBR < 1.3 AND holding period = 47 days" is curve-fitting).

**Warning signs:**
- Strategy performance is highly sensitive to small parameter changes (fragile).
- Backtested Sharpe > 2.0 for a monthly-rebalancing fundamental strategy (too good to be true).
- Parameters have specific, non-round values (47 days vs. 45 or 60 days = likely overfitted).
- No out-of-sample test period preserved.
- Developer has tested more than 50 parameter variations.
- Walk-forward window sizes were themselves tuned to produce good results.

**References:**
- [Statistical Overfitting and Backtest Performance -- Bailey et al.](https://sdm.lbl.gov/oapapers/ssrn-id2507040-bailey.pdf) (HIGH confidence)
- [The Deflated Sharpe Ratio -- Bailey & Lopez de Prado](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) (HIGH confidence)
- [Backtest Overfitting in the ML Era -- ScienceDirect (2025)](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110) (HIGH confidence)
- [Walk-Forward Validation Framework -- arXiv (2025)](https://arxiv.org/html/2512.12924v1) (HIGH confidence)
- [Mitigating Backtest Overfitting -- Digital Finance News](https://digitalfinancenews.com/research-reports/mitigating-backtest-overfitting-in-quantitative-trading-systems-advanced-detection-and-prevention-strategies/) (MEDIUM confidence)

---

## High Pitfalls

Mistakes that cause significant rework or degrade system quality substantially.

---

### Pitfall 7: yfinance and Free Data Source Fragility

**Severity:** HIGH
**Phase to address:** Phase 1 -- Data Ingestion Pipeline

**What goes wrong:**
The entire data pipeline depends on yfinance (unofficial Yahoo Finance scraper) and SEC EDGAR (free but rate-limited API). yfinance breaks when Yahoo Finance changes its website layout -- this has happened multiple times. Data quality issues are pervasive and documented in dozens of GitHub issues.

**Why it happens:**
- yfinance is an *unofficial* scraper, not an API with SLA guarantees. Yahoo Finance has no obligation to maintain backward compatibility.
- **The `Adj Close` column was removed** in recent yfinance versions; the library now uses a different adjustment methodology (`auto_adjust`). Code that references `Adj Close` silently breaks.
- **The `repair=True` option in `history()` has false positives:** a January 2026 bug report (GitHub #2660) documents yfinance "making up stock splits that never happened."
- **Stock split adjustments fail intermittently:** Yahoo sometimes fails to apply stock split adjustments to past prices (GitHub #1531). Dividends data is not split-adjusted while OHLC data is (quantmod #253).
- SEC EDGAR rate-limits at 10 requests per second per IP. Bulk ingestion hits this quickly.
- XBRL data in SEC filings is wildly inconsistent: companies use custom extensions and varying taxonomies. edgartools v5.22+ maps 234 standardized concepts from 32,240 real filings, but ~20% of filings still use non-standard tags.

**Consequences:**
- Silent data corruption: the system ingests bad data and produces bad signals without any visible error.
- Pipeline breaks entirely during yfinance outages, potentially missing market screening days.
- XBRL parsing failures cause missing financial data for specific companies, creating gaps in the scoring universe.

**Prevention:**
1. Implement a data validation layer that checks every ingested data point: price > 0, volume > 0, no gaps in trading days, split-adjusted prices are continuous (no sudden 2x or 0.5x jumps without a corresponding split event).
2. Cache all raw data locally in DuckDB/SQLite immediately after ingestion. Never depend on live yfinance calls for backtesting.
3. Build a fallback data source: if yfinance fails, fall back to Alpha Vantage (free tier: 25 requests/day) or Financial Modeling Prep API.
4. For SEC EDGAR: respect the 10 req/s rate limit (implement at 8 req/s with backoff), use bulk download files for initial data load, set a proper User-Agent header with contact email as SEC requires.
5. **Pin yfinance version** in pyproject.toml and test data output format before upgrading. Specifically test `auto_adjust` behavior and `repair` flag behavior.
6. Cross-validate: compare yfinance prices against at least one other source for a sample of tickers weekly.
7. Be cautious with `repair=True`: validate against known corporate actions before trusting the repair results.

**Warning signs:**
- No data validation layer between ingestion and storage.
- Data pipeline has no fallback when yfinance raises exceptions.
- SEC EDGAR requests hit rate limits frequently (429 responses).
- Historical price data contains unexplained jumps >20% without corresponding corporate actions.
- yfinance version is unpinned or frequently updated without testing.
- Code references `Adj Close` column (removed in recent yfinance).

**References:**
- [Why Adj Close Disappeared in yfinance -- Medium](https://medium.com/@josue.monte/why-adj-close-disappeared-in-yfinance-and-how-to-adapt-6baebf1939f6) (MEDIUM confidence)
- [Yahoo fails to apply stock split -- yfinance GitHub #1531](https://github.com/ranaroussi/yfinance/issues/1531) (HIGH confidence)
- [Price repair split false-positive -- yfinance GitHub #2660](https://github.com/ranaroussi/yfinance/issues/2660) (HIGH confidence)
- [yfinance Price Repair docs](https://ranaroussi.github.io/yfinance/advanced/price_repair.html) (HIGH confidence)
- [edgartools XBRL mappings from 32,000 SEC filings](https://www.edgartools.io/i-learnt-xbrl-mappings-from-32-000-sec-filings/) (HIGH confidence)
- [SEC EDGAR XBRL Guide Feb 2026](https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide.pdf) (HIGH confidence)

---

### Pitfall 8: Paper Trading to Live Trading Gap

**Severity:** HIGH
**Phase to address:** Phase 5 -- Broker Integration & Paper Trading

**What goes wrong:**
The system performs well in Alpaca paper trading, but results diverge in live trading. Paper trading does not simulate slippage, partial fills, market impact, dividend payments, or corporate actions. Orders that fill instantly in paper trading take seconds to minutes in live markets.

**Why it happens:**
- Alpaca paper trading is a simulation. "Paper trading works the same way as live trading end to end -- except the order is not routed to a live exchange. Instead, the system simulates the order filling based on real-time quotes" (Alpaca docs).
- **Paper trading does NOT simulate dividends** (confirmed in Alpaca docs). For a mid-term holding system (1-3 months), dividend income is material (1-3% annualized for dividend-paying stocks) and its absence distorts paper trading P&L.
- Stop-loss orders in paper trading execute at the stop price. In live markets, they become market orders that can fill at significantly worse prices during gap-down opens. The April 2025 crash saw the Dow lose 4,000+ points in two days -- stop-losses would gap through substantially.
- Paper trading API uses different credentials (different API key, different base URL). Environment misconfiguration risks are real.

**Consequences:**
- False confidence from paper trading leads to deploying real capital on a strategy whose edge is smaller than transaction costs.
- Stop-loss fills at much worse prices than expected during high-volatility events, causing drawdowns that exceed position-sizing models.
- Missing dividend income in paper trading P&L understates true return by 1-3% annually, potentially making a marginal strategy appear unprofitable.

**Prevention:**
1. Track dividends separately in the paper trading phase. Manually add expected dividend income to paper trading P&L.
2. Add realistic slippage modeling: subtract 0.05-0.10% per trade from paper trading results.
3. Use strict environment variable naming (`ALPACA_PAPER_KEY` vs `ALPACA_LIVE_KEY`) and add an environment check at startup that prints which environment is active.
4. Implement a "paper trading graduation" checklist: minimum 3 months, minimum 50 trades, Sharpe > 0.5 after slippage adjustment, maximum drawdown within tolerance.
5. For stop-loss orders, assume gap risk: model stop-loss fills at 1-2% worse than the stop price during backtesting.
6. Use limit orders for entries instead of market orders to avoid adverse fills.

**Warning signs:**
- Paper trading period is less than 3 months (insufficient sample size for mid-term strategy).
- No slippage adjustment in paper trading P&L reporting.
- Same API key variable name used for both paper and live (environment confusion risk).
- The system uses market orders for entries/exits instead of limit orders.

**References:**
- [Paper Trading -- Alpaca Official Docs](https://docs.alpaca.markets/docs/paper-trading) (HIGH confidence)
- [Paper Trading vs Live Trading -- Alpaca](https://alpaca.markets/learn/paper-trading-vs-live-trading-a-data-backed-guide-on-when-to-start-trading-real-money) (HIGH confidence)
- [Slippage Paper vs Real Trading -- Alpaca Forum](https://forum.alpaca.markets/t/slippage-paper-trading-vs-real-trading/2801) (MEDIUM confidence)
- [2025 Stock Market Crash -- Wikipedia](https://en.wikipedia.org/wiki/2025_stock_market_crash) (HIGH confidence)

---

### Pitfall 9: Regime Blindness -- Models Trained on One Market State

**Severity:** HIGH
**Phase to address:** Phase 3 (Signal Engine) + Phase 6 (Regime Detection)

**What goes wrong:**
The scoring and signal engine performs well during the market regime it was developed in (e.g., 2020-2024 bull market) but fails catastrophically during regime changes (bear market, high-volatility crisis, rising rate environment). Fundamental strategies that worked in a low-rate environment produce opposite results when rates spike. Correlations that were stable for years change abruptly during crises, breaking all portfolio risk assumptions.

**Why it happens:**
- Backtesting on 2015-2024 data captures mostly one regime (low interest rates, tech dominance). The model learns patterns specific to this environment.
- During the April 2025 crash, the VIX spiked to 45.31 (highest since 2020), the S&P lost 10% in two days, and "support zones collapsed under wave after wave of stop-loss selling and algorithmic liquidations."
- Factor premiums (value, momentum, quality) are not constant -- they vary by regime. Value underperformed growth by 40%+ during 2017-2020, then dramatically outperformed in 2021-2022. A system calibrated on one period makes exactly wrong bets in the next.
- Portfolio correlations spike toward 1.0 during crises, making diversification assumptions invalid precisely when they matter most.

**Consequences:**
- The system's worst performance occurs during the highest-risk periods (regime transitions).
- Position sizing assumes stable correlations that break down during stress events, amplifying losses.
- A drawdown triggers the system's emergency protocols, but by then the damage is already large.

**Prevention:**
1. Backtest across multiple regimes: include 2008-2009 (financial crisis), 2020 (COVID crash), 2022 (rate hike bear), 2025 (tariff crash) in test data. If data doesn't cover these, the backtest is incomplete.
2. Implement regime detection (already planned for Phase 6) but move basic regime awareness to Phase 3: at minimum, track VIX level and market trend (200-day MA). Pause new entries when VIX > 30.
3. Adjust correlations dynamically: use stressed-period correlations for risk calculations when VIX is elevated, not long-term averages.
4. Include factor-regime analysis: measure whether the strategy's factor exposures (value, momentum, quality) are concentrated in factors that historically underperform during certain regimes.
5. Implement the circuit breaker from the existing methodology: daily 3% loss triggers trading halt.

**Warning signs:**
- Backtest data does not include at least 2 distinct market crises.
- No VIX or volatility-based signal in the system.
- Position sizing uses static correlation assumptions.
- The signal engine has identical behavior in bull and bear markets.

**References:**
- [Systemic Failures in Algorithmic Trading -- PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8978471/) (HIGH confidence)
- [Early Warning of Regime Switching -- ScienceDirect (2025)](https://www.sciencedirect.com/science/article/pii/S2589004225001841) (HIGH confidence)
- [2025 Stock Market Crash -- Wikipedia](https://en.wikipedia.org/wiki/2025_stock_market_crash) (HIGH confidence)
- [Market State Transitions -- Frontiers in Physics (2025)](https://www.frontiersin.org/journals/physics/articles/10.3389/fphy.2025.1647667/full) (HIGH confidence)

---

### Pitfall 10: Operational Kill Switch and Safety Gate Absence

**Severity:** HIGH
**Phase to address:** Phase 5 -- Broker Integration (start in Phase 1)

**What goes wrong:**
The system executes trades without adequate safety mechanisms. A bug in the signal engine, a data corruption event, or an environment misconfiguration causes the system to submit rapid-fire orders, massively oversized positions, or trades in the wrong direction. Without kill switches and safety gates, a single bug can drain the trading account.

**Why it happens:**
- The Knight Capital incident (2012): an inconsistent deployment where 7 of 8 servers received a code update caused $440 million in losses in 45 minutes. "The system lacked automated circuit breakers to halt trading during unusual patterns."
- It took Knight Capital staff ~30 minutes to activate the kill switch -- "compared to the response time of algorithmic trading systems, which are often measured in microseconds, this is not fast."
- Developers focus on the happy path (correct signals, normal market conditions) and underinvest in defensive infrastructure.
- Many teams treat "the model as the entire product, investing disproportionately in algorithmic sophistication while neglecting the architecture around it" -- and "in trading, this mistake is caught immediately, as a model with poor execution logic or missing constraints loses real money."

**Consequences:**
- Catastrophic financial loss from runaway orders.
- Accidental live trades during development (environment confusion).
- Undetected bugs silently corrupting positions over days/weeks.

**Prevention:**
1. **Pre-trade validation gate:** Every order must pass checks before submission: position size within limits, price within reasonable range (not >10% from last close), no duplicate orders within cooldown period, portfolio exposure within caps.
2. **Kill switch:** A single command that cancels all pending orders and prevents new order submission. Must work even if the main application is crashed/hanging.
3. **Environment isolation:** Startup banner prints "PAPER TRADING" or "LIVE TRADING" in bold. Live trading credentials never exist on development machine. Environment switch requires explicit confirmation.
4. **Order rate limiting:** Maximum 1 order per 30 seconds for non-urgent trades. Confirmation prompt for all order-related commands. `--confirm` flag required for execution.
5. **Anomaly detection:** If the system recommends positions that diverge significantly from recent behavior (e.g., position size 3x normal, sector concentration spike), require human review before execution.
6. **Daily reconciliation:** Compare the system's internal state (expected positions) against the broker's reported positions. Alert on any discrepancy.

**Warning signs:**
- No pre-trade validation layer exists.
- No kill switch command is implemented.
- Live and paper trading share configuration files or credential storage.
- No order rate limiting or cooldown between trades.
- The system has never been tested with intentionally corrupted input data.

**References:**
- [Knight Capital Disaster -- Sound of Development](https://soundofdevelopment.substack.com/p/the-knight-capital-disaster-how-a) (HIGH confidence)
- [Algorithmic Trading Controls: Best Practices -- NASDAQ](https://www.nasdaq.com/articles/fintech/regulatory-roundup-september-2025) (HIGH confidence)
- [Lessons from Algo Trading Failures -- LuxAlgo](https://www.luxalgo.com/blog/lessons-from-algo-trading-failures/) (MEDIUM confidence)
- [Risk Management Strategies for Algo Trading -- LuxAlgo](https://www.luxalgo.com/blog/risk-management-strategies-for-algo-trading/) (MEDIUM confidence)

---

## Moderate Pitfalls

Mistakes that cause noticeable quality degradation or wasted development time.

---

### Pitfall 11: SQLite/DuckDB Concurrency on Windows

**Severity:** MEDIUM
**Phase to address:** Phase 1 -- Data Layer

**What goes wrong:**
When data ingestion (writing new price data), the scoring engine (computing scores), and the CLI dashboard (displaying results) run concurrently, SQLite file locks cause "database is locked" errors. On Windows, filesystem locking behavior is less predictable than on Linux. The system freezes or crashes during daily screening workflow.

**Prevention:**
1. Enable WAL (Write-Ahead Logging) journal mode for both SQLite and DuckDB from day one.
2. Separate databases by access pattern: prices/financials (append-mostly) in DuckDB, operational state (CRUD) in SQLite. Different files avoid cross-contention.
3. Use connection pooling with high `busy_timeout` (10-20 seconds). Values below 5 seconds cause intermittent "database is locked" errors under concurrent write load.
4. Consider separate reader/writer processes with the DuckDB database, since DuckDB supports concurrent reads but single writer.
5. Test concurrency on Windows specifically -- do not assume Linux-tested code works identically.

**References:**
- [SQLite File Locking and Concurrency](https://sqlite.org/lockingv3.html) (HIGH confidence)
- [SQLite Concurrent Writes -- Ten Thousand Meters](https://tenthousandmeters.com/blog/sqlite-concurrent-writes-and-database-is-locked-errors/) (MEDIUM confidence)

---

### Pitfall 12: XBRL Tag Mapping Incompleteness

**Severity:** MEDIUM
**Phase to address:** Phase 1 -- Data Ingestion Pipeline

**What goes wrong:**
SEC XBRL filings use inconsistent tag names across companies. Even with edgartools' 234 standardized concepts (built from 32,240 filings), ~20% of filings use non-standard or custom extension tags for common financial concepts like revenue, net income, and total assets. The scoring engine silently produces incomplete scores for affected companies, or worse, uses wrong financial data mapped from incorrect tags.

**Prevention:**
1. Build a tag mapping validation test: run the XBRL parser against a representative sample (100+ companies across all sectors) and measure coverage percentage for each required financial field.
2. Implement explicit "data completeness" tracking: for each company, record which financial fields were successfully parsed and which are missing. Score calculations should require minimum data completeness (e.g., 90% of required fields) before producing a score.
3. Monitor edgartools releases closely -- the library is releasing 2-3 times per week with XBRL mapping improvements.
4. Build fallback data sourcing: if XBRL parsing fails for a company, attempt to get the same data from yfinance fundamentals.

**References:**
- [edgartools XBRL mappings from 32,000 SEC filings](https://www.edgartools.io/i-learnt-xbrl-mappings-from-32-000-sec-filings/) (HIGH confidence)
- [SEC XBRL Filing: Common Mistakes](https://www.ez-xbrl.com/blog/sec-xbrl-filing-mistakes/) (MEDIUM confidence)

---

### Pitfall 13: Transaction Cost and Slippage Underestimation

**Severity:** MEDIUM
**Phase to address:** Phase 4 -- Backtesting Engine

**What goes wrong:**
Backtests assume zero transaction costs (Alpaca is commission-free) but ignore spread and slippage. For a mid-term strategy with 1-3 month holding periods and ~4-8 round-trip trades per year per position, slippage of 0.05-0.10% per trade seems negligible. But across a portfolio of 15-20 positions with quarterly rebalancing, the cumulative drag is 0.3-1.6% annually -- enough to turn a marginal strategy unprofitable.

**Prevention:**
1. Model spread/slippage at 0.05-0.10% per trade in all backtests, even though commissions are $0.
2. Use conservative slippage for less liquid stocks: small-cap and micro-cap names may have spreads of 0.5%+ that eat into returns significantly.
3. Include market impact costs for position sizes that exceed 1% of average daily volume.
4. Deduct slippage from paper trading P&L reporting to get realistic performance comparison.

**References:**
- [The 7 Deadly Sins of Backtesting -- StarQube](https://starqube.com/backtesting-investment-strategies/) (MEDIUM confidence)

---

## Minor Pitfalls

Mistakes that cause inconvenience or minor quality issues.

---

### Pitfall 14: Alert Fatigue and Information Overload

**Severity:** LOW
**Phase to address:** Phase 5 -- Monitoring and CLI

**What goes wrong:**
The monitoring engine sends alerts for every price movement, every stop-loss approach, every data refresh. The user receives 50+ alerts per day and ignores all of them, including critical ones (actual stop-loss triggers, dramatic changes in fundamentals).

**Prevention:**
1. Implement alert priority tiers: CRITICAL (stop-loss hit, drawdown tier breached), HIGH (target reached, fundamental score changed significantly), LOW (routine price movement, data refresh).
2. Rate-limit alerts: maximum 5 alerts per day for LOW priority, no limit for CRITICAL.
3. Aggregate similar alerts: "3 positions approaching stop-loss" instead of 3 separate alerts.
4. Show data freshness timestamp on every screen to make stale data visible.

---

### Pitfall 15: Single-Number Precision Fallacy in Reporting

**Severity:** LOW
**Phase to address:** Phase 5 -- CLI Dashboard

**What goes wrong:**
Displaying intrinsic value as "$47.23" and F-Score as "7" without context creates false precision. Users treat estimates as facts, make decisions based on exact numbers that have wide error margins, and lose trust when reality diverges.

**Prevention:**
1. Show valuation as a range: "Intrinsic Value: $42-$58 (median $50, 18% margin of safety at current $41)."
2. Show score with sector context: "F-Score: 7 (89th percentile in Technology; range 4-8)."
3. Every recommendation must show the top 3 contributing factors and the top 1 risk factor.
4. Limit daily screening output to top 10 opportunities ranked by conviction score; provide drill-down for details.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using yfinance `Close` instead of properly adjusted prices | Faster implementation | Incorrect returns calculation after splits/dividends, compounding backtest errors | Never for backtesting; acceptable for current-day screening only |
| Storing all data in a single SQLite file | Simple setup | Write contention with concurrent access; file lock issues on Windows | Never -- use DuckDB + SQLite split from day one |
| Hardcoding scoring thresholds (F-Score > 7) | Ships faster | Cannot adapt to sector-specific norms; unable to test alternative thresholds | MVP prototype only; must be configurable before backtesting |
| Skip sector normalization in scoring | Simpler scoring engine | Financial and capital-heavy companies always score low; tech companies always score high; portfolio concentrates | Never -- must address in the scoring engine from the start |
| Using total CapEx instead of maintenance CapEx for FCF | Only data available without manual research | Systematically biased FCF estimates | MVP only with explicit documentation of the bias |
| Ignoring corporate actions (M&A, spin-offs) in data pipeline | Simpler data model | Phantom price jumps, incorrect return calculations | MVP with a data quality flag column marking suspicious movements |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| yfinance `auto_adjust` | Assuming `Adj Close` column still exists; or assuming `auto_adjust=True` (new default) handles all adjustments correctly | Check yfinance version; test adjustment behavior against known split dates; handle both `auto_adjust=True` and `False` cases |
| yfinance `repair=True` | Trusting repair results blindly | Validate against known corporate actions; watch for false-positive split detection (GitHub #2660); disable repair for data you can validate independently |
| SEC EDGAR rate limit | Hitting 10 req/s and getting IP-banned | Implement at 8 req/s with exponential backoff; set User-Agent with contact email; use bulk download files for initial load |
| SEC EDGAR XBRL | Assuming consistent tag names across filers | Build tag mapping layer; expect ~20% non-standard tags; use edgartools' standardized concepts; validate coverage per company |
| Alpaca API environments | Using same credential config for paper and live | Separate config files per environment; startup banner prints environment; switch requires explicit confirmation |
| Alpaca stop-loss orders | Assuming fill at exact stop price | Model as "stop triggers market order"; add gap-risk buffer of 1-2% in position sizing |
| DuckDB on Windows | Assuming same file locking as Linux | Enable WAL mode; test concurrent access on Windows; use separate files for different workloads |
| edgartools XBRL parser | Assuming complete financial data for all companies | Track data completeness per company; require minimum field coverage before scoring; log parsing failures |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading full price history per ticker in pandas | Screening takes 30+ min for 3000+ stocks | Store pre-computed features in DuckDB; load only required date range; use parquet for bulk historical data | Universe exceeds 500 tickers with 10+ years |
| Running DCF valuation for every stock daily | Valuation run takes hours | Only revalue on new filings or price movements >5%; cache valuations with 7-day TTL for stable companies | Universe exceeds 200 stocks |
| SEC EDGAR full-text parsing per screening run | Memory exhaustion; hours-long ingestion | Parse once, store structured data; only re-parse when new filings appear | Filing count exceeds 5000 |
| SQLite single-writer bottleneck | "Database is locked" errors; CLI freezes | WAL mode; separate databases; use DuckDB for analytics; high `busy_timeout` | Concurrent processes exceed 3 |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing Alpaca API keys in code/config committed to git | Unauthorized trading; financial loss | Environment variables only; `*.env` in `.gitignore`; secrets manager for production |
| Same API key for paper and live | Accidental live trades during development | Completely separate credential sets; live credentials never on dev machine |
| No rate limiting on trade commands | Accidental rapid-fire order submission | Confirmation prompts; cooldown period; `--confirm` flag required |
| Logging order details with account info | Account exposure in log files | Sanitize logs: mask account IDs, redact API keys |

## "Looks Done But Isn't" Checklist

- [ ] **Data Pipeline:** Every financial data row has `filing_date`; backtest assertion rejects trades using future data
- [ ] **Data Pipeline:** Securities master has `listing_date` and `delisted_date` columns; universe size varies by date
- [ ] **Data Pipeline:** Data validation layer checks every ingested price/financial data point
- [ ] **Scoring Engine:** Sector normalization exists -- F-Score thresholds differ by industry group
- [ ] **Scoring Engine:** Uses Altman Z''-Score for non-manufacturing/service companies
- [ ] **Valuation Engine:** Output includes confidence band, not just point estimate
- [ ] **Valuation Engine:** Terminal value contribution capped at 85%; sensitivity report per valuation
- [ ] **Signal Engine:** Momentum filter exists to avoid value traps
- [ ] **Signal Engine:** Regime awareness exists (at minimum VIX-based, signals paused when VIX > 30)
- [ ] **Backtesting Engine:** Walk-forward validation built in; train/validate/test split enforced
- [ ] **Backtesting Engine:** Transaction costs modeled (0.05-0.10% slippage per trade)
- [ ] **Backtesting Engine:** Survivorship-bias correction -- test universe includes delisted stocks
- [ ] **Backtesting Engine:** Deflated Sharpe Ratio and PBO calculated
- [ ] **Risk Management:** Hard cap 5% per position, 25% per sector; correlation adjustment active
- [ ] **Risk Management:** Drawdown tiers override Kelly sizing
- [ ] **Trade Plans:** Every plan has entry, take-profit, stop-loss, AND time-based exit (holding period limit)
- [ ] **Broker Integration:** Kill switch implemented and tested
- [ ] **Broker Integration:** Pre-trade validation gate exists
- [ ] **Broker Integration:** Environment isolation verified; startup banner shows environment
- [ ] **Monitoring:** Alerts are prioritized and rate-limited
- [ ] **Human Approval:** Approval screen shows enough context for informed decision (not just "Buy AAPL?")

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Look-ahead bias discovered | HIGH | Rebuild data layer with point-in-time awareness; re-run ALL backtests; discard all previously validated strategies |
| Survivorship bias in universe | HIGH | Source delisted company data; rebuild securities master; re-run ALL backtests |
| Value trap concentration | MEDIUM | Add momentum overlay to signal engine; close positions in confirmed value traps; adjust scoring weights |
| DCF producing nonsensical values | MEDIUM | Cap terminal value; add sector-specific model weighting; implement confidence bands; re-run affected valuations |
| Kelly oversizing causing drawdown | MEDIUM | Immediately reduce to Quarter Kelly; add hard caps; implement correlation adjustment; trigger drawdown tiers |
| Overfitted backtest failing live | HIGH | Discard strategy; implement walk-forward + CPCV; start with simpler strategy; fewer parameters |
| yfinance breaking | LOW | Switch to cached data; activate fallback source; pin working version; monitor yfinance GitHub issues |
| Paper-to-live performance gap | MEDIUM | Add slippage model; adjust stop-loss buffers; extend paper trading period; switch to limit orders |
| Regime change causing losses | MEDIUM | Activate drawdown tiers; pause new entries; implement basic regime filter (VIX > 30); reduce position sizes |
| Operational incident (runaway orders) | HIGH | Activate kill switch; cancel all pending orders; reconcile positions; audit pre-trade validation gates |

## Pitfall-to-Phase Mapping

| Pitfall | Severity | Prevention Phase | Verification |
|---------|----------|------------------|--------------|
| 1. Look-ahead bias | CRITICAL | Phase 1: Data Ingestion | Every financial data row has `filing_date`; assertion layer rejects trades using future data |
| 2. Survivorship bias | CRITICAL | Phase 1: Data Ingestion | Securities master has `listing_date` and `delisted_date`; universe size varies by date |
| 3. Value trap blindness | CRITICAL | Phase 2: Scoring + Phase 3: Signal | Sector-normalization active; momentum filter in signal engine; Z''-Score for non-manufacturing |
| 4. DCF model brittleness | CRITICAL | Phase 2-3: Valuation Engine | Confidence band output; terminal value capped at 85%; sensitivity report per valuation |
| 5. Kelly blow-up risk | CRITICAL | Phase 3-4: Risk Management | Hard cap 5%/position, 25%/sector; correlation adjustment active; drawdown tiers override |
| 6. Backtesting overfitting | CRITICAL | Phase 4: Backtesting Engine | Walk-forward + CPCV built in; parameter count < 10; DSR + PBO calculated; train/validate/test split |
| 7. Data source fragility | HIGH | Phase 1: Data Ingestion | Validation layer active; fallback source configured; yfinance pinned; cross-validation weekly |
| 8. Paper-to-live gap | HIGH | Phase 5: Broker Integration | Slippage model applied; minimum 3 months paper; environment isolation; dividend tracking |
| 9. Regime blindness | HIGH | Phase 3 + Phase 6 | Backtest includes 2+ crises; VIX-based regime filter; dynamic correlation adjustment |
| 10. Kill switch absence | HIGH | Phase 1 (start) + Phase 5 | Kill switch command exists and tested; pre-trade validation gate; daily reconciliation |
| 11. DB concurrency | MEDIUM | Phase 1: Data Layer | WAL mode enabled; separate databases; tested on Windows specifically |
| 12. XBRL incompleteness | MEDIUM | Phase 1: Data Ingestion | Coverage validation test; completeness tracking per company; fallback data sourcing |
| 13. Transaction costs | MEDIUM | Phase 4: Backtesting | 0.05-0.10% slippage modeled; market impact for illiquid stocks; slippage in paper P&L |
| 14. Alert fatigue | LOW | Phase 5: Monitoring | Priority tiers; rate limiting; aggregation; freshness timestamps |
| 15. Precision fallacy | LOW | Phase 5: CLI | Ranges not point estimates; sector context; factor attribution; drill-down available |

## Sources

### Academic and Institutional (HIGH confidence)
- [CFA Level 2: Problems in Backtesting](https://analystprep.com/study-notes/cfa-level-2/problems-in-backtesting/)
- [The Seven Sins of Quantitative Investing -- Portfolio Optimization Book](https://bookdown.org/palomar/portfoliooptimizationbook/8.2-seven-sins.html)
- [Statistical Overfitting and Backtest Performance -- Bailey et al.](https://sdm.lbl.gov/oapapers/ssrn-id2507040-bailey.pdf)
- [The Deflated Sharpe Ratio -- Bailey & Lopez de Prado](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
- [Backtest Overfitting in the ML Era -- ScienceDirect (2025)](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110)
- [Walk-Forward Validation Framework -- arXiv (2025)](https://arxiv.org/html/2512.12924v1)
- [Tackling Estimation Risk in Kelly Investing -- arXiv (2025)](https://arxiv.org/html/2508.18868v1)
- [Practical Implementation of the Kelly Criterion -- Frontiers](https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2020.577050/full)
- [Evolution of Fundamental Scoring Models -- CFA UK](https://www.cfauk.org/pi-listing/man-machine-the-evolution-of-fundamental-scoring-models-and-ml-implications)
- [Avoiding Value Traps -- Research Affiliates](https://www.researchaffiliates.com/publications/articles/1013-avoiding-value-traps)
- [Systemic Failures in Algorithmic Trading -- PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8978471/)
- [Early Warning of Regime Switching -- ScienceDirect (2025)](https://www.sciencedirect.com/science/article/pii/S2589004225001841)
- [Point-in-Time Data -- FactSet Whitepaper](https://insight.factset.com/hubfs/Resources%20Section/White%20Papers/ID11996_point_in_time.pdf)
- [SEC EDGAR XBRL Guide Feb 2026](https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide.pdf)

### Official Documentation (HIGH confidence)
- [Paper Trading -- Alpaca Docs](https://docs.alpaca.markets/docs/paper-trading)
- [yfinance Price Repair Docs](https://ranaroussi.github.io/yfinance/advanced/price_repair.html)
- [SQLite File Locking and Concurrency](https://sqlite.org/lockingv3.html)
- [Alpaca Paper vs Live Trading](https://alpaca.markets/support/difference-paper-live-trading)

### Practitioner Sources (MEDIUM confidence)
- [Common Errors in DCF Models -- Wall Street Prep](https://www.wallstreetprep.com/knowledge/common-errors-in-dcf-models/)
- [Terminal Value Sensitivity -- Financial-Modeling.com](https://www.financial-modeling.com/terminal-value-in-dcf-perpetual-growth-rate-sensitivity/)
- [Knight Capital Disaster -- Sound of Development](https://soundofdevelopment.substack.com/p/the-knight-capital-disaster-how-a)
- [Algorithmic Trading Controls -- NASDAQ](https://www.nasdaq.com/articles/fintech/regulatory-roundup-september-2025)
- [Dealing with Delistings -- Alpha Architect](https://alphaarchitect.com/dealing-with-delistings-a-critical-aspect-for-stock-selection-research/)
- [Value Trap Identification -- Lord Abbett](https://www.lordabbett.com/en-us/financial-advisor/insights/investment-objectives/2025/how-equity-investors-can-avoid-value-traps.html)
- [Why Piotroski's F-Score No Longer Works -- Portfolio123](https://blog.portfolio123.com/why-piotroskis-f-score-no-longer-works/)
- [edgartools XBRL mappings](https://www.edgartools.io/i-learnt-xbrl-mappings-from-32-000-sec-filings/)
- [Key Risks in Automated Trading -- DarkBot](https://darkbot.io/blog/key-risks-in-automated-trading-what-traders-miss)
- [Why Adj Close Disappeared in yfinance](https://medium.com/@josue.monte/why-adj-close-disappeared-in-yfinance-and-how-to-adapt-6baebf1939f6)

### GitHub Issues (HIGH confidence for specific bugs)
- [yfinance #1531: Yahoo fails to apply stock split](https://github.com/ranaroussi/yfinance/issues/1531)
- [yfinance #2660: Price repair false-positive splits](https://github.com/ranaroussi/yfinance/issues/2660)
- [yfinance #1749: Close vs Adj Close](https://github.com/ranaroussi/yfinance/issues/1749)
- [quantmod #253: Yahoo OHLC split-adjusted but dividends not](https://github.com/joshuaulrich/quantmod/issues/253)

---
*Pitfalls research for: AI-assisted fundamental analysis mid-term trading system (US equities)*
*Researched: 2026-03-12*
*15 distinct pitfalls identified (6 Critical, 4 High, 3 Medium, 2 Low)*
