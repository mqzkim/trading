# Quantitative Scoring Methodologies for Securities Trading

## Research Compilation: Mid-to-Long Term Trading Strategies

**Timeframes Covered**: Swing Trading (weeks to months) and Position Trading (months to years)

---

## Table of Contents

1. [Multi-Factor Quantitative Scoring Models](#1-multi-factor-quantitative-scoring-models)
2. [Building Systematic Scoring Frameworks](#2-building-systematic-scoring-frameworks)
3. [Weighting and Normalization Techniques](#3-weighting-and-normalization-techniques)
4. [Academic Research on Factor Investing](#4-academic-research-on-factor-investing)
5. [Position Sizing Based on Conviction Scores](#5-position-sizing-based-on-conviction-scores)
6. [Risk-Adjusted Scoring](#6-risk-adjusted-scoring)
7. [Machine Learning Approaches](#7-machine-learning-approaches)
8. [Backtesting Frameworks](#8-backtesting-frameworks)

---

## 1. Multi-Factor Quantitative Scoring Models

### 1.1 Piotroski F-Score (Value Quality Screen)

**Source**: Joseph Piotroski, Stanford, 2000. "Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers."

**Purpose**: Assess the financial strength of value stocks. Score range: 0-9.

**Formula**: F-Score = F1 + F2 + F3 + F4 + F5 + F6 + F7 + F8 + F9

**Profitability (4 criteria)**:
| Signal | Condition | Score |
|--------|-----------|-------|
| F1: ROA | Net Income / Total Assets > 0 | +1 |
| F2: Operating Cash Flow | CFO > 0 | +1 |
| F3: Change in ROA | ROA(t) > ROA(t-1) | +1 |
| F4: Accruals | CFO > Net Income (cash quality) | +1 |

**Leverage, Liquidity & Source of Funds (3 criteria)**:
| Signal | Condition | Score |
|--------|-----------|-------|
| F5: Change in Leverage | Long-term debt ratio decreased YoY | +1 |
| F6: Change in Liquidity | Current ratio increased YoY | +1 |
| F7: Equity Offering | No new shares issued in prior year | +1 |

**Operating Efficiency (2 criteria)**:
| Signal | Condition | Score |
|--------|-----------|-------|
| F8: Change in Gross Margin | Gross margin improved YoY | +1 |
| F9: Change in Asset Turnover | Asset turnover improved YoY | +1 |

**Interpretation**:
- **8-9**: Strong financial position (buy candidates)
- **0-2**: Weak financial position (avoid/short candidates)

**Performance**: Piotroski's original study showed 23% annual return (1976-1996). Backtests show average yearly outperformance of 13.4% over the market. Effectiveness varies by economic cycle -- during contractions, macro factors dominate firm-level factors.

**Best Use for Swing/Position Trading**: Screen value stocks (low P/B) then filter by F-Score >= 7. Rebalance quarterly.

### 1.2 Altman Z-Score (Bankruptcy Risk Screen)

**Source**: Edward Altman, NYU, 1968.

**Purpose**: Predict probability of corporate bankruptcy within 2 years.

**Formula**:
```
Z = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E

Where:
A = Working Capital / Total Assets          (liquidity)
B = Retained Earnings / Total Assets        (cumulative profitability)
C = EBIT / Total Assets                     (operating efficiency)
D = Market Cap / Total Liabilities           (solvency)
E = Revenue / Total Assets                  (asset utilization)
```

**Interpretation**:
| Zone | Z-Score | Meaning |
|------|---------|---------|
| Safe | > 2.99 | Low bankruptcy risk |
| Grey | 1.81 - 2.99 | Moderate risk, needs monitoring |
| Distress | < 1.81 | High bankruptcy probability |

**Best Use**: Use as a negative filter -- exclude any stock with Z < 1.81 from your universe. Particularly valuable when combined with value screens to avoid "value traps."

### 1.3 Beneish M-Score (Earnings Manipulation Detection)

**Source**: Messod Beneish, Indiana University, 1999.

**Purpose**: Detect likelihood of earnings manipulation/fraud.

**8-Variable Formula**:
```
M = -4.84 + 0.92*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
    + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
```

**5-Variable Formula** (simplified):
```
M = -6.065 + 0.823*DSRI + 0.906*GMI + 0.593*AQI + 0.717*SGI + 0.107*TATA
```

**Variables**:
| Variable | Name | What It Measures |
|----------|------|------------------|
| DSRI | Days Sales in Receivables Index | Revenue inflation risk |
| GMI | Gross Margin Index | Margin deterioration |
| AQI | Asset Quality Index | Asset capitalization risk |
| SGI | Sales Growth Index | Growth pressure to manipulate |
| DEPI | Depreciation Index | Depreciation policy changes |
| SGAI | SGA Expense Index | SGA efficiency signals |
| TATA | Total Accruals to Total Assets | Discretionary accruals |
| LVGI | Leverage Index | Debt-driven manipulation incentive |

**Interpretation**:
- M-Score > -1.78 (8-variable) or > -2.22 (5-variable): **Likely manipulator**
- M-Score < threshold: **Low manipulation probability**

**Track Record**: Correctly identified 76% of manipulators with only 17.5% false positives. Cornell students used it to flag Enron before its collapse. Companies flagged as manipulators underperformed by 9.7% annually (1993-2007).

**Best Use**: Binary filter -- exclude any stock with M-Score above the threshold.

### 1.4 Mohanram G-Score (Growth Stock Quality)

**Source**: Partha Mohanram, Columbia Business School, 2004.

**Purpose**: Separate winners from losers among growth stocks (low book-to-market). Score range: 0-8.

**Formula**: G-Score = G1 + G2 + G3 + G4 + G5 + G6 + G7 + G8

**Profitability Signals (3 criteria)**:
| Signal | Condition | Score |
|--------|-----------|-------|
| G1: ROA | ROA > Industry Median | +1 |
| G2: Cash Flow ROA | CFO/Assets > Industry Median | +1 |
| G3: Cash vs. Earnings | CFO > Net Income | +1 |

**Earnings Stability Signals (2 criteria)**:
| Signal | Condition | Score |
|--------|-----------|-------|
| G4: Earnings Variability | 5yr ROA Variance < Industry Median | +1 |
| G5: Sales Growth Variability | 5yr Sales Growth Variance < Industry Median | +1 |

**Accounting Conservatism Signals (3 criteria)**:
| Signal | Condition | Score |
|--------|-----------|-------|
| G6: R&D Intensity | R&D/Assets > Industry Median | +1 |
| G7: CapEx Intensity | CapEx/Assets > Industry Median | +1 |
| G8: Advertising Intensity | Ad Spend/Assets > Industry Median | +1 |

**Performance**: Long high-G-Score / short low-G-Score earned positive returns in all 21 years tested (1979-1999). Works across large/small caps and with/without analyst coverage.

**Best Use for Position Trading**: Apply to growth stock universe (lowest 20% book-to-market). Buy G-Score >= 6, avoid G-Score <= 2.

### 1.5 Combined Scoring Framework

The complementary nature of these scores enables a layered screening approach:

```
Step 1: Universe = All stocks meeting liquidity requirements
Step 2: Remove Altman Z-Score < 1.81              (bankruptcy filter)
Step 3: Remove Beneish M-Score > -1.78             (manipulation filter)
Step 4: For value stocks (high B/M): Rank by Piotroski F-Score >= 7
Step 5: For growth stocks (low B/M): Rank by Mohanram G-Score >= 6
Step 6: Apply composite multi-factor scoring (Section 2)
```

---

## 2. Building Systematic Scoring Frameworks

### 2.1 Three-Pillar Architecture: Fundamental + Technical + Sentiment

A robust composite scoring framework integrates three signal types:

```
Composite Score = w_F * Fundamental_Score + w_T * Technical_Score + w_S * Sentiment_Score

Where: w_F + w_T + w_S = 1.0
```

**Typical weight ranges for swing/position trading**:
| Pillar | Swing Trading (weeks-months) | Position Trading (months-years) |
|--------|------------------------------|----------------------------------|
| Fundamental | 0.30 - 0.40 | 0.50 - 0.60 |
| Technical | 0.35 - 0.45 | 0.20 - 0.30 |
| Sentiment | 0.15 - 0.25 | 0.10 - 0.20 |

### 2.2 Fundamental Sub-Score Components

```
Fundamental_Score = w1*Value + w2*Quality + w3*Growth + w4*Financial_Health

Value factors:
  - P/E ratio (inverse, lower is better)
  - P/B ratio (inverse)
  - EV/EBIT (inverse)
  - EV/EBITDA (inverse)
  - EV/FCF (inverse)
  - Earnings Yield (E/P)

Quality factors:
  - ROE, ROA, ROIC
  - Gross margin stability (5yr)
  - Debt/Equity ratio (inverse)
  - Interest coverage ratio
  - Piotroski F-Score
  - Accruals ratio (lower is better)

Growth factors:
  - Revenue growth (3yr CAGR)
  - EPS growth (3yr CAGR)
  - FCF growth (3yr CAGR)
  - Mohanram G-Score components

Financial Health:
  - Altman Z-Score
  - Beneish M-Score (as filter)
  - Current ratio
  - Debt-to-EBITDA
```

### 2.3 Technical Sub-Score Components

For swing and position trading timeframes, use weekly/monthly indicators:

```
Technical_Score = w1*Trend + w2*Momentum + w3*Mean_Reversion + w4*Volume

Trend factors:
  - Price relative to 50-day and 200-day MA
  - ADX (Average Directional Index) > 25
  - Weekly MACD signal direction
  - Price position within 52-week range

Momentum factors:
  - 6-month price momentum (most validated factor academically)
  - 12-month momentum minus last month (12-1 momentum)
  - Relative strength vs. sector and market
  - Rate of change (ROC) over 3, 6, 12 months

Mean Reversion signals:
  - RSI(14) weekly: oversold (< 30) or overbought (> 70)
  - Distance from 200-day MA (Bollinger Band position)
  - 52-week high/low proximity

Volume signals:
  - On-Balance Volume (OBV) trend
  - Volume relative to 50-day average
  - Accumulation/Distribution line direction
```

### 2.4 Sentiment Sub-Score Components

```
Sentiment_Score = w1*Analyst + w2*News + w3*Market + w4*Insider

Analyst Sentiment:
  - Consensus rating changes (upgrades/downgrades)
  - Earnings estimate revisions (FY1, FY2)
  - Price target revisions
  - MSCI defines this as equal-weighted composite of changes in:
    sales, EPS, CPS, price targets, buy/sell recommendations

News Sentiment:
  - Composite Sentiment Score (CSS) from news analytics
  - Event Sentiment Score (ESS) from market-moving events
  - NLP-derived sentiment from earnings calls/filings

Market Sentiment:
  - Short interest ratio changes
  - Put/Call ratio (sector level)
  - Institutional ownership changes (13F filings)
  - Fund flow data

Insider Activity:
  - Insider buying/selling ratios
  - Cluster buying signals
  - Form 4 filing analysis
```

### 2.5 Step-by-Step Framework Construction

```
1. DEFINE UNIVERSE
   - Liquidity filter: min avg daily volume, min market cap
   - Sector/geography constraints
   - Exclude financials for certain fundamental metrics

2. COLLECT RAW DATA
   - Fundamental: quarterly/annual financial statements
   - Technical: daily/weekly OHLCV data
   - Sentiment: analyst estimates, news feeds, insider transactions

3. CALCULATE RAW FACTOR VALUES
   - Compute each individual metric for every stock

4. NORMALIZE (cross-sectional, per time period)
   - Z-score or percentile rank within sector/industry
   - See Section 3 for detailed techniques

5. AGGREGATE INTO SUB-SCORES
   - Fundamental_Score = weighted sum of normalized fundamental factors
   - Technical_Score = weighted sum of normalized technical factors
   - Sentiment_Score = weighted sum of normalized sentiment factors

6. COMPUTE COMPOSITE SCORE
   - Composite = w_F*Fund + w_T*Tech + w_S*Sent

7. RANK AND SELECT
   - Rank all stocks by composite score
   - Select top N or top decile/quintile

8. APPLY RISK FILTERS
   - Maximum sector concentration (e.g., 25%)
   - Maximum single position size (e.g., 5%)
   - Minimum Z-Score threshold
   - Correlation constraints

9. DETERMINE POSITION SIZES
   - Score-weighted or Kelly-based (Section 5)

10. EXECUTE AND MONITOR
    - Rebalance period: monthly for swing, quarterly for position
    - Monitor for score degradation triggers
```

---

## 3. Weighting and Normalization Techniques

### 3.1 Normalization Methods

#### Z-Score Normalization
```
Z_i = (X_i - mean(X)) / std(X)

Where:
  X_i = raw factor value for stock i
  mean(X) = cross-sectional mean of factor X
  std(X) = cross-sectional standard deviation of factor X
```

**Advantages**: Preserves distribution shape, intuitive interpretation (deviations from mean).
**Disadvantages**: Sensitive to outliers, assumes near-normal distribution.

**Practical Enhancement -- Winsorized Z-Score**:
```
Step 1: Clip raw values at 1st and 99th percentile (or 5th/95th)
Step 2: Compute Z-score on clipped data
```

#### Percentile Rank Normalization
```
Rank_i = Percentile_Rank(X_i) / 100

Result: uniform distribution from 0 to 1
```

**Advantages**: Immune to outliers, uniform distribution, no distributional assumptions.
**Disadvantages**: Loses information about magnitude of differences between stocks.

**This is the preferred method for most practitioners** because financial data is rarely normally distributed. Factors like P/B can have extreme outliers that distort z-scores.

#### Min-Max Scaling
```
Scaled_i = (X_i - min(X)) / (max(X) - min(X))

Result: range [0, 1]
```

**Disadvantages**: Dominated by outliers at extremes. Generally not recommended for cross-sectional stock scoring.

#### Cumulative Normal Transformation (0 to 1)
```
Step 1: Compute Z-score
Step 2: Apply cumulative normal function: Score_i = Phi(Z_i)

Result: score from 0 to 1, where 0.5 = average exposure
```

Used by FTSE Russell for factor exposure indexes. Provides smooth scoring with natural center at 0.5.

### 3.2 Cross-Sectional vs. Time-Series Normalization

**Cross-Sectional** (recommended for scoring):
- Normalize across all stocks at each point in time
- Tells you: "How does this stock rank relative to peers RIGHT NOW?"
- Mean z-score for every factor = 0 at each date
- Limitation: loses information about how the overall market level of a factor changes over time

**Time-Series**:
- Normalize each stock's factor across time
- Tells you: "Is this stock's valuation cheap relative to its own history?"
- Useful as supplementary signal, not primary scoring method

**Sector-Neutral Normalization** (best practice):
```
Z_sector_i = (X_i - mean(X_sector)) / std(X_sector)

Normalize within each sector/industry group to avoid sector biases
(e.g., tech stocks always appearing "expensive" on P/E)
```

### 3.3 Weighting Approaches for Composite Scores

#### Equal Weighting
```
Composite = (1/N) * SUM(normalized_factor_i) for i = 1 to N
```
- Simplest approach; surprisingly effective
- Avoids concentration risk in any single factor
- Robust when factor efficacy is uncertain

#### Expert/Judgment-Based Weighting
Assign weights based on domain knowledge:
```
Example for Position Trading:
  Value:      0.25
  Quality:    0.25
  Momentum:   0.20
  Growth:     0.15
  Sentiment:  0.15
  Total:      1.00
```

#### IC-Weighted (Information Coefficient)
```
w_i = IC_i / SUM(IC_j) for all j

Where IC_i = average historical Information Coefficient of factor i
```
- Weights factors by their historical predictive power
- Dynamic: recalculate IC monthly or quarterly
- Risk: past IC may not predict future IC

#### Inverse Volatility Weighting
```
w_i = (1/sigma_i) / SUM(1/sigma_j)

Where sigma_i = standard deviation of factor i's returns
```
- Gives more weight to more stable factors
- Risk-parity inspired

#### Optimization-Based Weighting
```
Maximize: Expected_Portfolio_Return(w)
Subject to:
  SUM(w_i) = 1
  w_i >= 0
  Portfolio_Volatility(w) <= target
```
- Most sophisticated but highest overfitting risk
- Requires robust out-of-sample validation
- Consider Bayesian shrinkage estimators for stability

#### Dynamic IC-Based Weighting (from recent ML research)
```
w_i(t) = f(IC_i(t-1), IC_i(t-2), ..., IC_i(t-k))

Where weights are adjusted based on rolling IC windows
Captures factor cyclicality and regime changes
```

### 3.4 Tilt-Tilt vs. Composite Approach (FTSE Russell Framework)

**Composite Index** (simpler):
- Take weighted average of single-factor indexes
- Example: 50% Value Index + 50% Quality Index
- Advantage: top-down simplicity
- Disadvantage: diluted factor exposures

**Tilt-Tilt** (sequential):
- First tilt toward factor 1, then tilt result toward factor 2
- Preserves stronger factor exposures
- Produces less dilution than composite approach

**Intersectional** (most concentrated):
- Select stocks that score highly on ALL factors simultaneously
- Highest factor exposure but smallest universe
- Best for high-conviction position trading

---

## 4. Academic Research on Factor Investing

### 4.1 Fama-French Factor Models

**Three-Factor Model (1993)**:
```
R_i - R_f = alpha + beta_M*(R_M - R_f) + beta_S*SMB + beta_V*HML + epsilon

Where:
  R_M - R_f = Market excess return
  SMB = Small Minus Big (size premium)
  HML = High Minus Low book-to-market (value premium)
```
Explains >90% of diversified portfolio returns (vs. 70% for CAPM alone).

**Five-Factor Model (2015)**:
```
R_i - R_f = alpha + beta_M*(R_M - R_f) + beta_S*SMB + beta_V*HML
            + beta_P*RMW + beta_I*CMA + epsilon

New factors:
  RMW = Robust Minus Weak (profitability premium)
  CMA = Conservative Minus Aggressive (investment premium)
```

**Key findings**:
- Adding RMW and CMA made HML redundant in U.S. data (1963-2013)
- CMA has 0.7 correlation with HML
- Model still ignores momentum (widely accepted anomaly)
- 2010-2019 was a "lost decade" for Fama-French factors
- But similar underperformance in 1990-1999 was followed by strong 2000-2009 comeback

### 4.2 Validated Factor Premia

Based on decades of academic research, the most robust factor premia are:

| Factor | Description | Annual Premium | Persistence |
|--------|-------------|---------------|-------------|
| Market | Equity risk premium | 5-8% | Very High |
| Value | Cheap vs. expensive | 3-5% | High (cyclical) |
| Size | Small vs. large cap | 2-3% | Moderate |
| Momentum | Winners vs. losers (12-1 month) | 6-8% | High |
| Quality/Profitability | Profitable vs. unprofitable | 3-5% | High |
| Low Volatility | Low risk vs. high risk | 4-6% | High |
| Investment | Conservative vs. aggressive capex | 2-4% | Moderate |

### 4.3 Factor Cyclicality and Regime Dependence

Research confirms factor effectiveness varies with market conditions:
- **High interest rate + high sentiment**: Value factor outperforms
- **Low interest rate + low sentiment**: Size factor outperforms
- **Low volatility** factors generated 6-10% premium even during the "lost decade" (2010-2019)
- Factor variances exhibit power-law behavior (alpha approximately 2), limiting diversification benefits

### 4.4 The Fundamental Law of Active Management

```
IR approximately equals IC * sqrt(Breadth)

Where:
  IR = Information Ratio (risk-adjusted active return)
  IC = Information Coefficient (correlation of forecasts to outcomes)
  Breadth = Number of independent investment decisions per year
```

**Practical Interpretation**:
- IC of 0.05 (typical for good factor) with 500 stocks = IR of 0.05 * sqrt(500) = 1.12
- Improve performance by: better signals (higher IC) OR more independent bets (wider breadth)
- For position trading (low breadth), you need higher IC to compensate

### 4.5 Information Coefficient (IC) as Factor Evaluation

**Pearson IC** (raw):
```
IC = Correlation(Factor_Scores, Forward_Returns)
```

**Spearman Rank IC** (preferred, robust to outliers):
```
Rank_IC = Correlation(Rank(Factor_Scores), Rank(Forward_Returns))
```

**Interpretation**:
| IC Value | Interpretation |
|----------|---------------|
| > 0.10 | Exceptionally strong (check for overfitting) |
| 0.05 - 0.10 | Very strong, actionable |
| 0.02 - 0.05 | Good, typical for validated factors |
| 0.00 - 0.02 | Weak but potentially useful in combination |
| < 0.00 | Negative signal (potentially useful if reversed) |

**Best Practice**: Report both Pearson and Spearman IC, average IC over time, IC standard deviation, and IC Information Ratio (IC_mean / IC_std).

### 4.6 Key Academic References

- Fama & French (1993): Three-factor model
- Fama & French (2015): Five-factor model
- Carhart (1997): Four-factor model (added momentum)
- Piotroski (2000): F-Score for value stocks
- Mohanram (2005): G-Score for growth stocks
- Beneish (1999): M-Score for manipulation detection
- Altman (1968): Z-Score for bankruptcy prediction
- Grinold & Kahn (1999): Fundamental Law of Active Management
- Asness, Moskowitz & Pedersen (2013): "Value and Momentum Everywhere"
- Novy-Marx (2013): Quality factor (gross profitability)
- Blitz & van Vliet (2007): Low volatility anomaly
- Jegadeesh & Titman (1993): Momentum returns

---

## 5. Position Sizing Based on Conviction Scores

### 5.1 Kelly Criterion

**Binary Outcome Formula**:
```
f* = (b*p - q) / b

Where:
  f* = optimal fraction of capital to bet
  b  = odds received (win/loss ratio)
  p  = probability of winning
  q  = probability of losing (1 - p)
```

**Continuous Distribution Formula** (for investing):
```
f* = (mu - r) / sigma^2

Where:
  f*    = optimal fraction of capital
  mu    = expected return of the investment
  r     = risk-free rate
  sigma = standard deviation of returns
```

**Multi-Asset Kelly** (portfolio):
```
w* = Sigma^(-1) * mu

Where:
  w*    = vector of optimal weights
  Sigma = covariance matrix of returns
  mu    = vector of expected excess returns
```

### 5.2 Fractional Kelly (Recommended)

Full Kelly maximizes geometric growth but creates extreme volatility. Practitioners universally recommend fractional Kelly:

| Fraction | Use Case | Risk Profile |
|----------|----------|-------------|
| Full Kelly (1.0x) | Theoretical optimum only | Very high volatility, large drawdowns |
| Half Kelly (0.5x) | Aggressive systematic | ~75% of full Kelly growth, ~50% of variance |
| Quarter Kelly (0.25x) | Conservative systematic | ~50% of growth, ~25% of variance |
| Tenth Kelly (0.1x) | Very conservative | Minimal drawdowns, slow growth |

**Recommendation for swing/position trading**: Use 0.25x to 0.50x Kelly.

### 5.3 Conviction Score to Position Size Mapping

**Method 1: Linear Mapping**
```
Position_Size_i = Base_Size * (Composite_Score_i / Max_Score)

Example:
  Base_Size = 5% of portfolio
  Stock A composite score = 0.85 (out of 1.0)
  Position_Size_A = 5% * 0.85 = 4.25%
```

**Method 2: Tiered Sizing**
```
Score >= 0.90 (top 10%):   "High Conviction"  -> 4-5% position
Score 0.70 - 0.89:         "Medium Conviction" -> 2-3% position
Score 0.50 - 0.69:         "Low Conviction"    -> 1-2% position
Score < 0.50:              "No Position"        -> 0%
```

**Method 3: Kelly-Score Hybrid**
```
Step 1: Compute Kelly fraction for each stock
        f_i = (mu_i - r) / sigma_i^2

Step 2: Apply fractional Kelly
        f_adj_i = 0.5 * f_i

Step 3: Scale by composite score
        Position_i = f_adj_i * Composite_Score_i

Step 4: Normalize to sum to 100%
        Final_Position_i = Position_i / SUM(Position_j)

Step 5: Apply caps
        Max single position: 5-8%
        Min position (if included): 0.5-1%
```

### 5.4 Volatility-Adjusted Position Sizing

```
Position_Size_i = Target_Risk / Volatility_i

Where:
  Target_Risk = desired dollar risk per position (e.g., 1% of portfolio)
  Volatility_i = ATR(20) or annualized standard deviation of stock i

This ensures each position contributes roughly equal risk to the portfolio.
```

**Combined with Conviction Score**:
```
Position_Size_i = (Target_Risk / Volatility_i) * Score_Multiplier_i

Where Score_Multiplier ranges from 0.5 (low conviction) to 1.5 (high conviction)
```

### 5.5 Practical Position Sizing Rules

For a 20-40 stock portfolio (typical for swing/position trading):
- **Maximum single position**: 8% of portfolio
- **Minimum single position**: 1% of portfolio
- **Maximum sector exposure**: 25-30% of portfolio
- **Maximum correlated cluster**: 20% of portfolio
- **Cash buffer**: 5-15% of portfolio

```
Rebalancing triggers:
  - Position grows to 2x original weight -> trim
  - Composite score drops below threshold -> exit
  - Sector concentration exceeds limit -> redistribute
  - Monthly/quarterly scheduled rebalance
```

---

## 6. Risk-Adjusted Scoring

### 6.1 Core Risk-Adjusted Performance Metrics

**Sharpe Ratio**:
```
SR = (R_p - R_f) / sigma_p

Where:
  R_p    = portfolio return
  R_f    = risk-free rate
  sigma_p = portfolio standard deviation

Annualized: SR_annual = sqrt(gamma) * SR_period
  where gamma = trading periods per year (252 for daily, 52 for weekly, 12 for monthly)
```

**Sortino Ratio** (downside-focused):
```
SoR = (R_p - R_f) / sigma_downside

Where sigma_downside = sqrt(SemiVariance)
SemiVariance = E[((mu - R_t)^+)^2]
  (only counts negative deviations)
```

**Information Ratio**:
```
IR = (R_p - R_b) / TE

Where:
  R_b = benchmark return
  TE  = tracking error (std of active returns)
```

### 6.2 Drawdown-Based Metrics

**Maximum Drawdown (MDD)**:
```
Drawdown_t = (HWM_t - NAV_t) / HWM_t
MDD = max(Drawdown_t) over all t

Where HWM_t = highest portfolio value up to time t
```

**Calmar Ratio**:
```
Calmar = (R_p - R_f) / MDD

Replaces volatility with maximum drawdown as risk measure.
More intuitive for practitioners: "return per unit of worst-case loss."
```

**Sterling Ratio**:
```
Sterling = (R_p - R_f) / (MDD + 0.10)

Adds 10% cushion to maximum drawdown denominator.
```

**Conditional Drawdown at Risk (CDaR)**:
```
CDaR_alpha = E[Drawdown | Drawdown >= VaR_alpha(Drawdown)]

Average drawdown in the worst alpha% of cases.
More robust than single-point MDD.
```

### 6.3 Integrating Risk into Scoring

**Method 1: Risk-Adjusted Composite Score**
```
Risk_Adjusted_Score_i = Composite_Score_i / Risk_Score_i

Where Risk_Score_i = weighted combination of:
  - Historical volatility (annualized, 1yr)
  - Beta relative to market
  - Maximum drawdown (trailing 1yr)
  - Downside deviation
```

**Method 2: Return-to-Risk Scoring**
```
For each stock, compute:
  Expected_Return_i = f(Composite_Score_i)  [map score to expected return]
  Expected_Risk_i   = f(Historical_Vol_i, Beta_i, Sector_Risk)

  Risk_Adj_Score_i = Expected_Return_i / Expected_Risk_i

This is essentially a forward-looking Sharpe ratio at the stock level.
```

**Method 3: Drawdown-Aware Scoring**
```
Drawdown_Penalty_i = max(0, MDD_i - Threshold) * Penalty_Coefficient

Adjusted_Score_i = Composite_Score_i - Drawdown_Penalty_i

Example:
  If MDD threshold = 20% and stock had 35% MDD:
  Penalty = (0.35 - 0.20) * 2.0 = 0.30
  If composite score was 0.85, adjusted = 0.85 - 0.30 = 0.55
```

**Method 4: Tail Risk Integration**
```
VaR_95_i = Percentile(Returns_i, 5th)  [5th percentile of returns]
CVaR_95_i = E[Returns_i | Returns_i <= VaR_95_i]

Tail_Risk_Score_i = -CVaR_95_i  (higher = more tail risk)

Final_Score_i = Composite_Score_i - lambda * Tail_Risk_Score_i
  where lambda = risk aversion parameter
```

### 6.4 Portfolio-Level Risk-Adjusted Scoring

When evaluating entire portfolios of scored stocks:

```
Portfolio Metrics to Track:
  1. Sharpe Ratio (target: > 1.0 for good strategy)
  2. Sortino Ratio (target: > 1.5)
  3. Calmar Ratio (target: > 0.5 over 3+ years)
  4. Maximum Drawdown (target: < 20% for moderate risk)
  5. Win Rate (target: > 55% for swing trading)
  6. Profit Factor (target: > 1.5)
  7. Recovery Time (target: < 6 months from drawdown)
```

### 6.5 The Omega Ratio

```
Omega(r) = integral from r to infinity of [1 - F(x)] dx
           / integral from -infinity to r of F(x) dx

Where:
  F(x) = CDF of returns
  r    = threshold return (often 0 or risk-free rate)
```

Omega > 1 means more probability mass above threshold than below. Captures entire return distribution, not just mean and variance.

---

## 7. Machine Learning Approaches

### 7.1 Factor Scoring with Machine Learning

**Feature Engineering Pipeline**:
```
Raw Data -> Feature Construction -> Feature Selection -> Model Training -> Scoring

Feature categories:
  1. Fundamental factors (value, quality, growth)
  2. Technical factors (momentum, volatility, volume)
  3. Alternative data (sentiment, satellite, web traffic)
  4. Derived factors (interactions, ratios, transformations)

Typical scale: 100-1000 candidate factors
After selection: 20-100 retained factors
```

### 7.2 Feature Selection Methods

**Filtering Methods** (pre-model):
```
For each candidate factor:
  1. Compute Information Coefficient (IC) with forward returns
  2. Compute Rank IC (Spearman correlation)
  3. Retain factors with |IC| > threshold (e.g., 0.02)
  4. Remove factors with high pairwise correlation (> 0.7)

IC_i = Correlation(Factor_Score_i, Forward_Return)
IC_IR_i = Mean(IC_i) / Std(IC_i)  [IC Information Ratio]

Retain if IC_IR > 0.5 (signal is consistent over time)
```

**Wrapper Methods** (model-based):
```
- Forward selection: Add factors one at a time, keep if improves OOS performance
- Backward elimination: Start with all, remove least useful
- Recursive Feature Elimination (RFE) with cross-validation
```

**Embedded Methods** (within model):
```
- LASSO (L1 regularization): automatically zeros out irrelevant factors
  Minimize: SUM[(y_i - X_i*beta)^2] + lambda * SUM|beta_j|

- Ridge (L2 regularization): shrinks coefficients of weak factors
  Minimize: SUM[(y_i - X_i*beta)^2] + lambda * SUM(beta_j^2)

- Elastic Net: combines L1 and L2
  Minimize: SUM[(y_i - X_i*beta)^2] + lambda_1*SUM|beta_j| + lambda_2*SUM(beta_j^2)

- Random Forest feature importance
- Gradient Boosting (XGBoost/LightGBM) feature importance
```

**Dimensionality Reduction**:
```
- PCA: Extract principal components from factor matrix
  Retain components explaining > 95% of variance
  Advantage: uncorrelated components
  Disadvantage: components lack interpretability

- Autoencoders: Neural network-based dimensionality reduction
  Encoder: high-dim factors -> low-dim latent space
  Decoder: latent space -> reconstructed factors
```

### 7.3 ML Model Architectures for Scoring

**For Cross-Sectional Stock Ranking (swing/position trading)**:

| Model | Strengths | Weaknesses | Typical Use |
|-------|-----------|------------|-------------|
| Ridge Regression | Stable, interpretable, handles multicollinearity | Linear only | Baseline model |
| LASSO | Feature selection built in | Linear only | Sparse factor models |
| Random Forest | Non-linear, feature importance, robust | Overfitting risk with deep trees | Factor interaction capture |
| XGBoost/LightGBM | Best tabular data performance, fast | Overfitting, less interpretable | Primary scoring model |
| SVM | Works well in high dimensions | Slow, opaque | Alternative classifier |
| MLP (Neural Net) | Universal approximator, flexible | Overfitting, data hungry | Complex non-linear patterns |
| LSTM/GRU | Temporal pattern capture | Needs lots of data, slow | Time-series factor evolution |
| Transformer | Attention mechanisms, state-of-the-art | Very data hungry | Cutting edge research |
| GNN (Graph Neural Net) | Captures stock interconnections | Complex, new | Sector/supply chain relationships |

**Recommended approach for swing/position trading**:
```
1. Start with Ridge Regression or XGBoost as baseline
2. Use ensemble of 2-3 models for robustness
3. Score = weighted average of model outputs
4. Weight by recent OOS performance (dynamic IC-based weighting)
```

### 7.4 ML-Enhanced Scoring Pipeline

```python
# Conceptual pipeline (pseudocode)

# Step 1: Feature preparation
features = compute_factors(universe, date)           # 500+ raw factors
features = winsorize(features, lower=0.01, upper=0.99)
features = normalize(features, method='percentile_rank')

# Step 2: Feature selection
ic_scores = compute_rolling_IC(features, forward_returns, window=252)
selected = features[ic_scores.mean() > 0.02]        # IC filter
selected = remove_correlated(selected, threshold=0.7) # Correlation filter

# Step 3: Model training (walk-forward)
for train_end in rebalance_dates:
    train_data = selected[train_end - lookback : train_end]
    test_data  = selected[train_end : train_end + holding_period]

    model = XGBoostRanker()
    model.fit(train_data.features, train_data.forward_returns)

    scores = model.predict(test_data.features)       # Raw ML scores

# Step 4: Combine with traditional scores
    composite = 0.5 * ml_score + 0.3 * fundamental_score + 0.2 * technical_score

# Step 5: Portfolio construction
    portfolio = select_top_n(composite, n=30)
    weights = conviction_weighted_sizing(portfolio, composite)
```

### 7.5 Multi-Task Learning for Scoring

Recent research (HGA-MT model) jointly predicts:
```
Task 1: Expected Return prediction
Task 2: Volatility/Risk prediction

Combined Score = f(predicted_return, predicted_risk)
              = predicted_return / predicted_risk    (Sharpe-like)
```

This approach produces stock rankings that are inherently risk-adjusted, rather than scoring return and risk separately.

### 7.6 Guard Rails for ML in Trading

**Overfitting Prevention**:
- Never use in-sample performance for model selection
- Use walk-forward validation (not simple train/test split)
- Apply regularization (L1, L2, dropout)
- Limit model complexity relative to training data size
- Rule of thumb: need 10x observations per feature

**Interpretability**:
- Use SHAP values to understand factor contributions
- Monitor feature importance stability over time
- Prefer interpretable models for core scoring; use ML as overlay
- Every trade should have an explainable thesis

**Data Pitfalls**:
- Survivorship bias: include delisted stocks
- Look-ahead bias: ensure no future data leaks
- Point-in-time data: use as-reported financials, not restated
- Transaction costs: include realistic spread + commission estimates

---

## 8. Backtesting Frameworks

### 8.1 Backtesting Methodology Hierarchy

```
Level 1: Simple Backtest (historical simulation)
  - Single in-sample/out-of-sample split
  - Quick but high overfitting risk

Level 2: Walk-Forward Analysis (WFA)
  - Rolling train/test windows
  - Multiple out-of-sample periods
  - More robust but window selection sensitivity

Level 3: Combinatorial Purged Cross-Validation (CPCV)
  - Multiple train/test splits with purging and embargoing
  - Produces distribution of performance outcomes
  - Most robust, highest computational cost

Level 4: Live Paper Trading
  - Real-time execution simulation
  - True out-of-sample validation
  - Slowest but most reliable
```

### 8.2 Walk-Forward Analysis (WFA) in Detail

```
Timeline: |----Train----|--Test--|----Train----|--Test--|----Train----|--Test--|

Parameters:
  - Training window: 12-36 months (longer for position trading)
  - Test window: 1-6 months
  - Step size: 1-3 months
  - Number of walk-forward periods: 10-30+

Process:
  1. Train model on window [t_0, t_train]
  2. Generate scores for [t_train, t_train + t_test]
  3. Record OOS performance
  4. Slide window forward by step_size
  5. Repeat until end of data
  6. Concatenate all OOS results for total performance

Walk-Forward Efficiency (WFE):
  WFE = Average_OOS_Performance / Average_IS_Performance
  Target: WFE > 0.5 (50%+ of IS performance carries forward)
```

### 8.3 Combinatorial Purged Cross-Validation (CPCV)

Developed by Marcos Lopez de Prado (2017):

```
Key mechanisms:
  1. PURGING: Remove training observations whose labels overlap with test period
     - Prevents leakage from label horizons spanning train/test boundary

  2. EMBARGOING: After each test period, remove additional observations
     - Prevents leakage from autocorrelated features
     - Typical embargo: 1-5% of data length

  3. COMBINATORIAL SPLITS: Generate many train/test combinations
     - Produces multiple backtest "paths"
     - Each path is a plausible market scenario

Output: Distribution of Sharpe ratios (not single point estimate)
  - If distribution is centered > 0: robust strategy
  - Wide distribution: parameter sensitive
  - Left tail below 0: potential for loss
```

### 8.4 Overfitting Detection Metrics

**Probability of Backtest Overfitting (PBO)**:
```
PBO = P(strategy with best IS performance ranks below median OOS)

Computed via CSCV (Combinatorially Symmetric Cross-Validation):
  1. Collect performance matrix M (T observations x N trials)
  2. Generate all combinatorial train/test splits
  3. For each split: find IS-optimal strategy, check OOS rank
  4. PBO = fraction where OOS rank < median

Target: PBO < 0.10 (less than 10% probability of overfitting)
```

**Deflated Sharpe Ratio (DSR)**:
```
DSR adjusts observed Sharpe Ratio for:
  - Number of trials tested (N)
  - Variance of Sharpe Ratios across trials
  - Non-normality of returns (skewness, kurtosis)

If DSR < critical value: observed SR is likely due to luck/data mining
```

**Sharpe Ratio Regression**:
```
OOS_Sharpe = alpha + beta * IS_Sharpe + epsilon

If beta < 0: IS optimization is counterproductive (overfitting)
If beta > 0 and significant: IS skill transfers to OOS
```

### 8.5 Python Backtesting Frameworks Comparison

| Framework | Speed | Live Trading | Learning Curve | Best For |
|-----------|-------|-------------|----------------|----------|
| **VectorBT** | Fastest (vectorized, Numba) | No | Steep | Large-scale parameter optimization, factor research |
| **Backtrader** | Moderate (event-driven) | Yes (IB, OANDA, Alpaca) | Moderate | Swing trading systems with broker integration |
| **Zipline-reloaded** | Moderate | No | Moderate | Factor-based equity research, scikit-learn integration |
| **Backtesting.py** | Fast | No | Easy | Quick research prototypes |
| **QSTrader** | Moderate | No | Moderate | Institutional-style portfolio simulation |
| **NautilusTrader** | Fast (Rust core) | Yes | Steep | Production-grade institutional systems |
| **BT** | Moderate | No | Easy | Mixing and matching algorithmic strategies |
| **QuantConnect/LEAN** | Moderate | Yes | Moderate | Cloud-based strategy development |

**Recommendations by use case**:
```
Scoring model research & optimization -> VectorBT
  - Vectorized operations for scoring thousands of stocks
  - Built-in parameter optimization
  - Excellent performance metrics

Swing trading implementation -> Backtrader
  - Event-driven logic matches real trading
  - Multi-timeframe support
  - Broker integration for live execution

Factor-based position trading -> Zipline-reloaded or QSTrader
  - Pipeline API for factor computation
  - scikit-learn integration for ML scoring
  - Institutional-style portfolio analytics
```

### 8.6 Essential Backtesting Checklist for Scoring Models

```
DATA INTEGRITY:
  [ ] Point-in-time fundamentals (no restatement look-ahead)
  [ ] Survivorship-bias-free universe (includes delisted stocks)
  [ ] Corporate actions adjusted (splits, dividends)
  [ ] Sufficient history (10+ years, multiple market cycles)

METHODOLOGY:
  [ ] Walk-forward or CPCV validation (never single IS/OOS split)
  [ ] Realistic rebalancing frequency (monthly or quarterly)
  [ ] Transaction costs included (commission + spread + market impact)
  [ ] Slippage modeled (especially for small/mid cap)
  [ ] Capacity constraints considered (can strategy absorb target AUM?)

SCORING MODEL SPECIFIC:
  [ ] Factors computed only with information available at rebalance date
  [ ] Cross-sectional normalization done independently at each date
  [ ] Factor weights determined only from prior data
  [ ] ML model trained only on prior data (walk-forward)

RISK MANAGEMENT:
  [ ] Maximum drawdown within acceptable limits
  [ ] Sector concentration within bounds
  [ ] Position size limits enforced
  [ ] Correlation to benchmark tracked
  [ ] Turnover and tax efficiency monitored

STATISTICAL VALIDATION:
  [ ] Sharpe ratio significantly different from zero (t-stat > 2)
  [ ] Probability of Backtest Overfitting (PBO) < 10%
  [ ] Walk-Forward Efficiency > 50%
  [ ] Performance consistent across sub-periods
  [ ] Results robust to reasonable parameter variations
```

### 8.7 Complete Validation Pipeline

```
Phase 1: DEVELOPMENT (in-sample)
  - Explore factors, build scoring model
  - Use first 60-70% of data

Phase 2: WALK-FORWARD VALIDATION
  - Rolling train/test across remaining data
  - Compute distribution of Sharpe ratios
  - Check WFE > 50%

Phase 3: CPCV ANALYSIS
  - Generate multiple train/test paths
  - Compute PBO (target < 10%)
  - Compute Deflated Sharpe Ratio

Phase 4: ROBUSTNESS CHECKS
  - Vary rebalance frequency (+/- 1 week)
  - Vary factor weights (+/- 10%)
  - Vary universe definition (market cap cutoffs)
  - Test across different time periods and geographies

Phase 5: PAPER TRADING (minimum 3-6 months)
  - Execute scoring model in real time
  - Track live vs. backtest performance
  - Monitor execution quality and slippage

Phase 6: LIVE DEPLOYMENT (small allocation initially)
  - Start with 10-25% of target allocation
  - Scale up if live performance matches expectations
  - Continuous monitoring and model retraining schedule
```

---

## Summary: Recommended Architecture for a Scoring System

For a swing/position trading scoring system, the recommended architecture combines classical scoring models with modern techniques:

```
LAYER 1: SAFETY FILTERS (binary pass/fail)
  - Altman Z-Score > 1.81 (no bankruptcy risk)
  - Beneish M-Score < -1.78 (no manipulation)
  - Minimum liquidity (avg volume, market cap)
  - No pending delistings or major corporate actions

LAYER 2: MULTI-FACTOR COMPOSITE SCORE (0-100 scale)
  Fundamental Sub-Score (weight: 0.40-0.50):
    - Value (percentile rank, sector-neutral)
    - Quality (ROE, margins, F-Score)
    - Growth (revenue, earnings, FCF growth)
    - Financial Health (Z-Score continuous, debt metrics)

  Technical Sub-Score (weight: 0.25-0.35):
    - Trend (MA relationships, ADX)
    - Momentum (6-12 month, relative strength)
    - Volume (OBV, accumulation/distribution)

  Sentiment Sub-Score (weight: 0.15-0.25):
    - Analyst revisions (EPS, price targets)
    - Insider activity
    - Short interest changes
    - News sentiment (if available)

LAYER 3: RISK ADJUSTMENT
  - Penalize high-volatility stocks (unless compensated by score)
  - Apply drawdown-awareness
  - Adjust for tail risk (CVaR)

LAYER 4: POSITION SIZING
  - Fractional Kelly (0.25-0.50x) based on score and volatility
  - Sector and concentration limits
  - Minimum/maximum position bounds

LAYER 5: VALIDATION
  - Walk-forward analysis with 12+ OOS periods
  - CPCV for PBO estimation
  - Monthly IC monitoring for factor decay
  - Quarterly model retraining cycle
```

---

## Sources

### Scoring Models
- [Piotroski F-Score - Wikipedia](https://en.wikipedia.org/wiki/Piotroski_F-score)
- [Piotroski F-Score Back Test - Quant Investing](https://www.quant-investing.com/blog/piotroski-f-score-back-test)
- [Piotroski's F-Score Under Varying Economic Conditions - Springer](https://link.springer.com/article/10.1007/s11156-024-01331-y)
- [Altman Z-Score and Piotroski Score - EODHD](https://eodhd.medium.com/altman-z-score-and-piotrosky-score-99328ab325f3)
- [Beneish M-Score - StableBread](https://stablebread.com/beneish-m-score/)
- [Detecting Financial Fraud with Beneish M-Score - Portfolio123](https://blog.portfolio123.com/detecting-financial-fraud-a-close-look-at-the-beneish-m-score/)
- [Mohanram G-Score - StableBread](https://stablebread.com/mohanram-g-score/)
- [Mohanram G-Score - AAII](https://www.aaii.com/journal/article/calculating-mohanram-g-score-using-si-pro-and-microsoft-excel)
- [Creating Quality Portfolios Using Score-Based Models - Nature](https://www.nature.com/articles/s41599-024-03888-4)

### Multi-Factor Frameworks
- [MSCI Analyst Sentiment Factor Research](https://www.msci.com/downloads/web/msci-com/research-and-insights/paper/analyst-sentiment-from-factor-to-indexation/Analyst%20Sentiment.pdf)
- [Composite Sentiment Score - RavenPack](https://www.ravenpack.com/research/composite-sentiment-score/)
- [Multi-Factor Indexes: The Power of Tilting - FTSE Russell](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/research/multi-factor-indexes-power-of-tilting.pdf)
- [How to Implement Multi-Factor Strategy - Quant Investing](https://www.quant-investing.com/blog/how-to-implement-a-multi-factor-quantitative-investment-strategy)
- [Discovering Optimal Weights in Stock-Picking Models - Springer](https://link.springer.com/article/10.1186/s40854-020-00209-x)

### Normalization and Weighting
- [Cross-Sectional Analysis in Finance - Medium](https://medium.com/algorithmic-and-quantitative-trading/how-to-rank-stocks-an-introduction-to-cross-sectional-analysis-in-finance-f10dbac02779)
- [Scaling/Normalization/Standardization - Quantdare](https://quantdare.com/scaling-normalisation-standardisation-a-pervasive-question/)
- [OECD Handbook on Constructing Composite Indicators](https://www.oecd.org/content/dam/oecd/en/publications/reports/2005/08/handbook-on-constructing-composite-indicators_g17a16e3/533411815016.pdf)
- [FTSE Russell Factor Exposure Index Methodology](https://research.ftserussell.com/products/downloads/factor-index-construction-methodology-paper.pdf)

### Academic Research
- [Fama-French Three-Factor Model - Wikipedia](https://en.wikipedia.org/wiki/Fama%E2%80%93French_three-factor_model)
- [Fama-French Five-Factor Model - SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2287202)
- [Five-Factor Model: Why More Is Not Always Better - Robeco](https://www.robeco.com/en-int/insights/2024/10/fama-french-5-factor-model-why-more-is-not-always-better)
- [Factor Investing: Going Beyond Fama and French - Robeco](https://www.robeco.com/en-us/insights/2020/11/factor-investing-going-beyond-fama-and-french)
- [Factor-Based Investing in Market Cycles - MDPI](https://www.mdpi.com/1911-8074/15/10/460)
- [Information Coefficient as Performance Measure - arXiv](https://arxiv.org/pdf/2010.08601)
- [Information Coefficient - FE Training](https://www.fe.training/free-resources/portfolio-management/information-coefficient-ic/)

### Position Sizing
- [Kelly Criterion for Position Sizing - Astute Investors Calculus](https://astuteinvestorscalculus.com/the-kelly-criterion/)
- [Kelly Criterion Position Sizing - Quantified Strategies](https://www.quantifiedstrategies.com/kelly-criterion-position-sizing/)
- [Position Sizing in Trading - QuantInsti](https://blog.quantinsti.com/position-sizing/)
- [Kelly Criterion in Portfolio Optimization - Bocconi Students](https://bsic.it/exploring-the-application-of-kellys-criterion-in-portfolio-optimization/)
- [Kelly Criterion - Wikipedia](https://en.wikipedia.org/wiki/Kelly_criterion)

### Risk-Adjusted Scoring
- [Portfolio Optimization Book: Performance Measures](https://portfoliooptimizationbook.com/book/6.3-performance-measures.html)
- [Drawdowns - Duke University (Harvey)](https://people.duke.edu/~charvey/Research/Published_Papers/P147_Drawdowns.pdf)
- [Portfolio Management with Drawdown-Based Measures - CME Group](https://www.cmegroup.com/education/files/portfolio-management-with-drawdown-based-measures.pdf)
- [Risk-Adjusted Performance Ratios - TradingCenter](https://tradingcenter.org/index.php/learn/fundamental-analysis/355-portfolio-ratios)
- [Risk-Adjusted DRL for Portfolio Optimization - Springer](https://link.springer.com/article/10.1007/s44196-025-00875-8)

### Machine Learning
- [From Deep Learning to LLMs: AI in Quantitative Investment - arXiv](https://arxiv.org/html/2503.21422v1)
- [Combined ML for Stock Selection with Dynamic Weighting - arXiv](https://arxiv.org/html/2508.18592v1)
- [ML Enhanced Multi-Factor Quantitative Trading - arXiv](https://arxiv.org/html/2507.07107)
- [Multi-Factor Models with SVM - IEEE](https://ieeexplore.ieee.org/iel8/10569142/10569145/10569485.pdf)
- [S&P 500 Stock Selection Using ML - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0275531924001296)

### Backtesting
- [Walk-Forward Analysis vs. Backtesting - Surmount](https://surmount.ai/blogs/walk-forward-analysis-vs-backtesting-pros-cons-best-practices)
- [Walk-Forward Analysis Guide - Medium](https://medium.com/funny-ai-quant/ai-algorithmic-trading-walk-forward-analysis-a-comprehensive-guide-to-advanced-backtesting-f3f8b790554a)
- [Walk-Forward Optimization - QuantInsti](https://blog.quantinsti.com/walk-forward-optimization-introduction/)
- [Walk-Forward Analysis - Interactive Brokers](https://www.interactivebrokers.com/campus/ibkr-quant-news/the-future-of-backtesting-a-deep-dive-into-walk-forward-analysis/)
- [CPCV Method - Towards AI](https://towardsai.net/p/l/the-combinatorial-purged-cross-validation-method)
- [Probability of Backtest Overfitting - SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253)
- [Backtest Overfitting in ML Era - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110)
- [Backtesting Framework Comparison - AutoTradeLab](https://autotradelab.com/blog/backtrader-vs-nautilusttrader-vs-vectorbt-vs-zipline-reloaded)
