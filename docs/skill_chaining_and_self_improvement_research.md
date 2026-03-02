# Skill Chaining and Automated Self-Improvement in Trading Systems

## Comprehensive Research Findings

**Focus:** Mid-to-long term trading (swing trading and position trading timeframes)
**Date:** March 2026

---

## Table of Contents

1. [Skill Chaining Concept](#1-skill-chaining-concept)
2. [Multi-Strategy Portfolio Construction](#2-multi-strategy-portfolio-construction)
3. [Automated Strategy Selection and Regime Detection](#3-automated-strategy-selection-and-regime-detection)
4. [Self-Improving Trading Systems](#4-self-improving-trading-systems)
5. [Walk-Forward Optimization and Adaptive Parameter Tuning](#5-walk-forward-optimization-and-adaptive-parameter-tuning)
6. [Ensemble Methods in Trading](#6-ensemble-methods-in-trading)
7. [Meta-Learning for Strategy Selection](#7-meta-learning-for-strategy-selection)
8. [Performance Attribution and Feedback Loops](#8-performance-attribution-and-feedback-loops)
9. [Kelly Criterion and Dynamic Position Sizing](#9-kelly-criterion-and-dynamic-position-sizing)
10. [Risk Management as a Skill in the Chain](#10-risk-management-as-a-skill-in-the-chain)
11. [Unified Skill Chain Architecture](#11-unified-skill-chain-architecture)

---

## 1. Skill Chaining Concept

### Definition and Origin

"Skill chaining" originates from Hierarchical Reinforcement Learning (HRL), where complex
long-horizon tasks are decomposed into a sequence of simpler sub-tasks, each handled by a
specialized policy. Konidaris and Barto formalized the concept: each "skill" (called an
"option" in the RL literature) has an initiation region, a learned policy, and a termination
region. The termination region of one skill becomes the initiation region of the next,
forming a chain.

While the term has not yet been widely adopted in the trading literature, the *concept* maps
directly onto quantitative trading pipeline architecture. A trading system is naturally
decomposed into a chain of specialized skills:

### The Trading Skill Chain

```
Data Ingestion --> Feature Engineering --> Regime Detection --> Signal Generation
     --> Strategy Selection --> Position Sizing --> Risk Management
     --> Execution --> Post-Trade Analysis --> Feedback/Retraining
```

Each stage is a "skill" that:
- Accepts a defined input (the output of the previous skill)
- Applies specialized logic (the learned policy)
- Produces a defined output (the input to the next skill)
- Can be independently trained, tested, and improved

### Hierarchical Decomposition for Trading

Drawing from NeurIPS 2024 research on SCaR (Skill Chaining with Refinement), the key
insight for trading is **bi-directional alignment**: each skill must work well internally
(intra-skill) AND mesh smoothly with adjacent skills (inter-skill). For example:

- A regime detection skill that identifies "high volatility bear" must produce output
  that the strategy selection skill can consume to pick appropriate strategies
- The position sizing skill must understand both the signal strength from the signal
  generator AND the risk constraints from the risk manager

### Practical Framework

| Skill | Input | Output | Key Algorithms |
|-------|-------|--------|----------------|
| Data Ingestion | Raw market feeds, alt data | Clean OHLCV, features | Kalman filters, anomaly detection |
| Regime Detection | Price/vol features | Regime label + confidence | HMM, GMM, clustering |
| Signal Generation | Features + regime context | Alpha signals | Factor models, ML models |
| Strategy Selection | Signals + regime | Strategy weights | Meta-learning, XGBoost |
| Position Sizing | Strategy output + portfolio state | Target positions | Kelly criterion, vol targeting |
| Risk Management | Target positions + risk budget | Adjusted positions | VaR, drawdown controls |
| Execution | Adjusted positions | Filled orders | TWAP, VWAP, adaptive execution |
| Performance Analysis | Trade history, returns | Performance metrics | Attribution analysis |
| Self-Improvement | Performance metrics + market data | Updated parameters/models | Walk-forward optimization, Bayesian opt |

### Key Implementation Principle

The modular, event-driven architecture is the recommended pattern. Each skill operates as
an independent service with well-defined interfaces. The separation of concerns means you
can upgrade, swap, or extend any skill without destabilizing the rest of the system, as
long as the interface contracts remain stable.

---

## 2. Multi-Strategy Portfolio Construction

### Core Principles

Multi-strategy portfolio construction treats each strategy as an "investable security" with
its own return stream. The three foundational principles are:
1. **Diversification** -- use diverse strategies to increase risk-adjusted returns
2. **Risk targeting** -- ensure appropriate risk levels across the portfolio
3. **Active management** -- monitor and adjust allocations dynamically

### Strategy Allocation Methods

#### Equal Weight
- Simplest benchmark: allocate capital equally across all strategies
- Surprisingly robust; often hard to beat after transaction costs
- Best when strategy edge estimates are uncertain

#### Mean-Variance Optimization (Markowitz)
- Maximizes return for a given risk level using the efficient frontier
- Requires estimates of expected returns and covariance matrix
- Sensitive to estimation errors -- use shrinkage estimators or robust methods

#### Risk Parity
- Equalizes risk contributions from each strategy
- Does not require return estimates (only covariance)
- Three main methodologies ensure equal risk among portfolio components
- Practical when strategies have very different volatilities

#### Hierarchical Risk Parity (HRP)
- Introduced by Marcos Lopez de Prado (2016)
- Three-step process: hierarchical tree clustering, matrix seriation, recursive bisection
- Outperforms Markowitz in out-of-sample tests
- Available in PyPortfolioOpt and Riskfolio-Lib (Python)
- Has achieved the best Sharpe ratio in comparative allocation studies

#### Hierarchical Clustering
- Extension of HRP with additional clustering methods
- Agglomerative, k-means, and spectral clustering variants
- Better captures non-linear relationships between strategies

#### Kelly Criterion Allocation
- Maximizes log-utility (geometric growth rate)
- Naturally accounts for correlations in multi-asset formulation
- Aggressive; use fractional Kelly (1/4 to 1/2) in practice

#### Volatility Targeting
- Equalizes volatility contributions across strategies
- After adjustment, all strategies have the same chance of being top/bottom performers
- Especially useful when strategies have very different volatility profiles

### Practical Implementation

```python
# Conceptual allocation pipeline
class StrategyAllocator:
    def __init__(self, strategies, method='hrp'):
        self.strategies = strategies
        self.method = method

    def compute_weights(self, lookback_returns):
        if self.method == 'hrp':
            from pypfopt import HRPOpt
            hrp = HRPOpt(returns=lookback_returns)
            hrp.optimize(linkage_method='single')
            return hrp.clean_weights()
        elif self.method == 'risk_parity':
            # Inverse-volatility weighting
            vols = lookback_returns.std()
            inv_vols = 1.0 / vols
            return inv_vols / inv_vols.sum()
        elif self.method == 'equal':
            n = len(self.strategies)
            return {s: 1.0/n for s in self.strategies}
```

### Overlay and Dynamic Rebalancing

A key question: should you increase weights of well-performing strategies (momentum overlay)
or decrease them (mean-reversion overlay)? Research from QuantPedia shows the answer depends
on the strategy type:
- Trend-following strategies: momentum overlay often works (winners keep winning)
- Mean-reversion strategies: contrarian overlay may be better
- Best approach: use regime detection to decide which overlay to apply

### For Swing/Position Trading

- Rebalance weekly or monthly (not daily -- transaction costs matter)
- Use expanding (anchored) windows for weight estimation to ensure stability
- Monitor factor exposures across the aggregate portfolio
- Maintain a maximum allocation cap per strategy (e.g., 30%) to prevent concentration

---

## 3. Automated Strategy Selection and Regime Detection

### What Are Market Regimes?

Markets transition between distinct behavioral states. Return distributions are non-stationary
and exhibit volatility clustering. Strategies that work in one regime can fail in another.
The canonical regimes are:

| Regime | Characteristics | Favored Strategies |
|--------|----------------|--------------------|
| Low-vol bull (trending up) | Positive autocorrelation, low VIX | Trend following, momentum |
| High-vol bull | Strong trends with sharp pullbacks | Trend following with wide stops |
| Low-vol range | Mean-reverting, low VIX | Mean reversion, pairs trading |
| High-vol bear (crisis) | Negative autocorrelation, high VIX | Short strategies, hedging, cash |
| Transition | Regime changing | Reduced exposure, hedging |

### Regime Detection Algorithms

#### Hidden Markov Models (HMMs)
- **The gold standard for regime detection in trading**
- Model markets as a sequence of hidden states with observable emissions (returns, volatility)
- Use Baum-Welch for parameter estimation, Viterbi for state decoding
- Typically 2-4 states work best for trading applications
- Implementation: `hmmlearn.GaussianHMM` in Python

```python
from hmmlearn.hmm import GaussianHMM
import numpy as np

# Features: log returns and realized volatility
features = np.column_stack([log_returns, realized_vol])

# Fit 3-state HMM
model = GaussianHMM(n_components=3, covariance_type='full', n_iter=1000)
model.fit(features)

# Predict current regime
current_regime = model.predict(features)[-1]
regime_probs = model.predict_proba(features)[-1]
```

#### Gaussian Mixture Models (GMM)
- Similar to HMM but without temporal transition structure
- Faster to fit; useful when you don't need transition probabilities
- Good for clustering return distributions into distinct regimes

#### K-Means and Agglomerative Clustering
- Simpler unsupervised approach
- Cluster on features like: return, volatility, skewness, autocorrelation
- Macrosynergy research uses Wasserstein k-means for robust classification

#### Statistical Measures
- **Autocorrelation**: positive = trending, negative = mean-reverting
- **Hurst exponent**: >0.5 = trending, <0.5 = mean-reverting, 0.5 = random walk
- **ADX (Average Directional Index)**: >25 = trending, <20 = ranging
- **VIX level and term structure**: backwardation = stress, contango = calm

### Automated Strategy Selection Based on Regime

The key innovation is building **regime-specific specialist models**:

1. Train HMM to identify 2-4 regimes on historical data
2. For each regime, train a specialist strategy/ML model on data from that regime only
3. At prediction time, detect current regime and use the corresponding specialist
4. Adjust position sizes based on regime confidence

This approach has been shown to outperform one-size-fits-all models because specialist
models better capture behavior patterns relevant to specific market conditions.

### Practical Implementation for Swing/Position Trading

- **Detection frequency**: Daily or weekly (not intraday for position trading)
- **Features for HMM**: 20-day realized vol, 20-day log returns, VIX, yield curve slope,
  MA50-MA200 spread, breadth indicators
- **Lag handling**: Regime detection inherently lags. Use regime *probabilities* rather
  than hard classifications. Transition to defensive positioning when regime uncertainty
  is high (no regime has >60% probability)
- **Validation**: Compare HMM-filtered strategy vs. unfiltered on out-of-sample data.
  The HMM should reduce false signals and improve Sharpe ratio.

---

## 4. Self-Improving Trading Systems

### Core Architectures

#### Hybrid Expert System + Deep Reinforcement Learning
- Combines rule-based expert systems with DRL for adaptive trading
- Human expertise provides guardrails; DRL optimizes within those bounds
- Robust to stressful market conditions and diverse scenarios
- More interpretable than pure DRL approaches

#### Self-Rewarding Deep Reinforcement Learning (SRDRL)
- Integrates a self-rewarding network within the RL framework
- Shifts from static reward functions to dynamic, self-rewarding models
- The agent autonomously refines its reward function based on continuous learning
- Particularly effective in complex, non-stationary trading environments

#### Self-Updating ML Pipelines
- Weekly or monthly retraining on the most recent market data
- The system doesn't just trade automatically -- it retrains itself
- Key insight: a model that performs well today might struggle tomorrow as conditions shift

#### Automated Adaptive Trading Systems (AATS)
- Continuously adapts and optimizes parameters of embedded forecasting models
- Uses adaptive learning with parameter tuning to accommodate dynamic data
- Shown to improve portfolio performance under volatile conditions

### Self-Improvement Feedback Loop

```
[Live Trading] --> [Performance Monitoring]
       ^                    |
       |                    v
[Deploy Updated Model] <-- [Performance Attribution]
       ^                    |
       |                    v
[Validation Gate] <------- [Model Retraining]
       ^                    |
       |                    v
[Walk-Forward Test] <----- [Parameter Optimization]
```

### Key Design Principles

1. **Never deploy without validation**: Every model update must pass walk-forward
   out-of-sample testing before live deployment
2. **Gradual transitions**: Phase in new parameters/models gradually (e.g., blend
   old and new model outputs for 2-4 weeks)
3. **Anomaly detection**: Monitor for regime breaks that might invalidate recent training
4. **Version control**: Maintain full history of model versions and their performance
5. **Kill switches**: Automatic system shutdown if drawdown exceeds threshold

### For Swing/Position Trading

- Retraining frequency: Monthly (weekly is too frequent for position trading timeframes)
- Lookback for training: 2-5 years of daily data
- Validation period: 6-12 months out-of-sample
- Performance threshold for redeployment: New model must beat current model by >5% Sharpe
  improvement, or show meaningful drawdown reduction

### Key Performance Benchmarks from Research

- PPO (Proximal Policy Optimization) achieved 21.3% annualized return in DRL studies
- LLM + DRL frameworks showed cumulative returns up to 58.47% for individual stocks
  and 27.14% for diversified portfolios, with Sharpe ratio of 1.70
- Self-healing mechanisms with anomaly detection reduce catastrophic failure events

---

## 5. Walk-Forward Optimization and Adaptive Parameter Tuning

### What Is Walk-Forward Optimization (WFO)?

First presented by Robert E. Pardo in 1992, WFO divides historical data into sequential
segments and repeatedly:
1. **Optimizes** strategy parameters on a training set (in-sample)
2. **Tests** those parameters on the next unseen segment (out-of-sample)
3. **Rolls forward** and repeats

The stitched out-of-sample equity curve provides a realistic assessment of live performance.

### Window Types for Swing/Position Trading

#### Anchored (Expanding) Window
- In-sample always starts from the beginning, growing over time
- **Recommended for weekly-bar strategies and position trading**
- Provides more stable parameters by using all available history
- Reduces overreaction to short-term market noise

#### Rolling (Fixed) Window
- In-sample has a fixed length that slides forward
- Better for strategies that need to adapt quickly to recent conditions
- More suitable for shorter timeframes (daily, intraday)

### Recommended Settings for Position Trading

| Parameter | Recommended Value | Rationale |
|-----------|------------------|-----------|
| In-sample window | 2-5 years | Captures multiple market cycles |
| Out-of-sample window | 6-12 months | Matches position trading holding periods |
| Roll step | 3-6 months | Balance between freshness and stability |
| Window type | Anchored | Stability for longer-horizon strategies |
| Fitness function | Sharpe ratio or Sortino ratio | Risk-adjusted, not raw return |

### Walk-Forward Efficiency (WFE)

WFE = Annualized OOS Return / Annualized IS Return

- **WFE > 50-60%**: Strategy is robust and likely to be profitable
- **WFE < 50%**: Strategy is likely overfitted to in-sample data
- If WFO performance is worse than un-optimized strategy, strong signal of curve fitting

### Advanced Optimization Methods

#### Bayesian Optimization
- Uses a surrogate model (Gaussian Process or Tree of Parzen Estimators) to efficiently
  search the parameter space
- Balances exploration (uncertain regions) and exploitation (promising regions)
- Converges faster than grid search or random search
- Tools: Optuna, HyperOpt, GPyOpt

```python
import optuna

def objective(trial):
    # Define parameter search space
    fast_ma = trial.suggest_int('fast_ma', 5, 50)
    slow_ma = trial.suggest_int('slow_ma', 50, 200)
    atr_mult = trial.suggest_float('atr_mult', 1.5, 4.0)

    # Run backtest with these parameters
    result = backtest(fast_ma=fast_ma, slow_ma=slow_ma, atr_mult=atr_mult)

    return result.sharpe_ratio  # Maximize Sharpe

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=200)
```

#### Genetic Algorithms
- Population-based search; particularly good for multi-objective optimization
- Recent research introduced a "genetic switch" mechanism for adaptive multi-asset strategies
- Can optimize both strategy parameters AND strategy selection simultaneously

#### Key Anti-Overfitting Principles

1. **Limit parameters**: Focus on 2-4 key parameters per strategy. More parameters = more
   overfitting risk
2. **Stability testing**: Good parameters should have stable performance in a neighborhood
   (parameter plateau, not spike)
3. **Cross-validation**: Use multiple out-of-sample windows, not just one
4. **Penalty for complexity**: Prefer simpler models with fewer parameters

---

## 6. Ensemble Methods in Trading

### Why Ensembles Work in Finance

Financial data has low signal-to-noise ratios, frequent regime shifts, and high
dimensionality. Ensembles address this by:
- **Reducing variance** (averaging out erratic individual predictions)
- **Reducing bias** (no single flawed assumption dominates)
- **Improving robustness** to regime change

### Key Ensemble Approaches

#### 1. Strategy-Level Ensembles (Combining Trading Strategies)

Combine multiple independent strategies into a "master" strategy:

```
Strategy A (momentum)    --\
Strategy B (mean-rev)    ----> Aggregator --> Final Signal
Strategy C (breakout)    --/
```

**Best practices:**
- Maximize diversity: use strategies based on different data types (volume, price action,
  intermarket signals, fundamentals)
- Require agreement: only take trades when 2+ strategies agree (voting ensemble)
- Weight by recent performance: give more weight to strategies performing well in the
  current regime
- The more diverse the individual strategies, the better the ensemble performs

#### 2. Model-Level Ensembles (Combining ML Models)

**Bagging (Bootstrap Aggregating):**
- Train many versions of the same model on different data subsets
- Random Forests are the most common bagging ensemble
- Reduces overfitting to specific features or time periods

**Boosting:**
- Sequentially train models, each correcting errors of the previous
- XGBoost, LightGBM, CatBoost are popular implementations
- Strong for feature-rich signal generation

**Stacking:**
- Train base models, then train a meta-model on their outputs
- The meta-model learns which base model to trust in which conditions
- Excellent for generalizing to unknown future data
- Research shows stacking outperforms individual algorithms across different periods

#### 3. Reinforcement Learning Ensembles

- Combine PPO, A2C, and SAC agents into an ensemble
- Each agent may specialize in different market conditions
- Recent work combines RL ensembles with massively parallel simulation
- Enhances robustness in volatile markets

### Implementation for Swing/Position Trading

```python
class StrategyEnsemble:
    def __init__(self, strategies, method='weighted_vote'):
        self.strategies = strategies
        self.method = method
        self.weights = {s.name: 1.0/len(strategies) for s in strategies}

    def generate_signal(self, market_data):
        signals = {}
        for strategy in self.strategies:
            signals[strategy.name] = strategy.predict(market_data)

        if self.method == 'weighted_vote':
            # Weighted average of signals
            combined = sum(
                self.weights[name] * signal
                for name, signal in signals.items()
            )
            return combined

        elif self.method == 'majority_vote':
            # Only trade if majority agree on direction
            votes = [1 if s > 0 else -1 if s < 0 else 0
                    for s in signals.values()]
            majority = sum(votes) / len(votes)
            return 1 if majority > 0.5 else -1 if majority < -0.5 else 0

    def update_weights(self, recent_performance):
        """Adaptive weighting based on recent performance"""
        total_perf = sum(max(p, 0) for p in recent_performance.values())
        if total_perf > 0:
            for name in self.weights:
                self.weights[name] = max(recent_performance[name], 0) / total_perf
```

### Critical Best Practice

Use **walk-forward training** on base models to ensure every base prediction is true
out-of-sample. This simulates the impact of non-stationarity (regime change) over time
and prevents information leakage.

### Challenges

- **Diversity is essential**: If individual models are too similar or correlated, ensemble
  benefits diminish
- **Computational cost**: Training large ensembles is resource-intensive
- **Interpretability**: "Black box" effect can hinder regulatory compliance and debugging
- **No free lunch**: Ensembles must be carefully validated; they are not automatic improvement

---

## 7. Meta-Learning for Strategy Selection

### Definition

Meta-learning ("learning to learn") in trading means building a system that learns to
select the right strategy (or strategy weights) for current market conditions. Rather than
optimizing a single strategy, you optimize the *process of selecting strategies*.

### Key Research Approaches

#### Meta-LMPS-online (Shen, Liu & Chen, 2025)

The most recent and sophisticated approach simulates a fund with multiple fund managers:
- Decomposes the long-term investment process into multiple short-term time segments
- Uses clustering to identify historically high-performing and diverse policies
- Employs MAML (Model-Agnostic Meta-Learning) to derive initial parameters that can
  rapidly adapt to new tasks
- Key innovation: learns mixture weights of multiple portfolio policies, independent of
  the number of stocks, which enables transferability across different markets and time periods

#### Meta Portfolio Method (MPM) (Kisiel & Gorse, 2021)

A practical, interpretable approach:
- Uses XGBoost to learn when to switch between HRP and Naive Risk Parity
- NRP grows faster in uptrends; HRP protects better in downturns
- The meta-learner captures the best of both worlds
- High degree of interpretability of allocation decisions

#### Meta-Grammatical Evolutionary Process

- Combines technical, fundamental, and macroeconomic analysis
- Automated trading system achieved average return of 30.14% over 11 years
- Compared to buy-and-hold average of -13.35%

### Practical Meta-Learning Pipeline for Swing/Position Trading

```
Step 1: Define the Strategy Universe
  - 5-10 diverse base strategies covering different market conditions
  - Example: trend following, mean reversion, breakout, carry, value

Step 2: Create Meta-Features
  - Market regime features (HMM state probabilities)
  - Volatility regime (VIX level, VIX term structure)
  - Trend strength (ADX, MA spread)
  - Recent strategy performance (rolling Sharpe of each strategy)
  - Macro indicators (yield curve, credit spreads)

Step 3: Train Meta-Learner
  - XGBoost or Random Forest on meta-features
  - Target: optimal strategy weights for next period
  - Label: weights that would have maximized Sharpe in the next period
  - Walk-forward training to prevent overfitting

Step 4: Deploy
  - Weekly: compute meta-features, predict optimal weights
  - Blend with equal-weight baseline (e.g., 70% meta / 30% equal)
  - Gradually increase meta weight as out-of-sample track record builds
```

### Key Insight from Research

The five recognized categories of online portfolio selection algorithms are:
1. Benchmark algorithms
2. Follow-the-winner
3. Follow-the-loser
4. Pattern matching
5. **Meta-learning algorithms**

Meta-learning is recognized as a distinct, established category -- not a niche approach.

---

## 8. Performance Attribution and Feedback Loops

### The 4-Step Feedback Loop

1. **Define Rules**: Clear, objective entry/exit criteria based on the strategy
2. **Execute and Record**: Comprehensive trade journal capturing all relevant data
3. **Analyze Performance**: Focus on strategy alignment with conditions, not just P&L
4. **Refine Strategy**: Systematic adjustments based on data, not emotional reactions

### Performance Attribution Framework for Multi-Strategy Systems

#### Level 1: Portfolio-Level Attribution
- Total return decomposition: alpha vs. beta vs. risk-free
- Factor attribution: how much return came from market, size, value, momentum, etc.
- Timing attribution: did regime switches add or detract value?

#### Level 2: Strategy-Level Attribution
- Per-strategy Sharpe ratio, Sortino ratio, Calmar ratio
- Per-strategy hit rate, profit factor, average win/loss ratio
- Strategy correlation matrix (are strategies truly diversified?)
- Drawdown analysis: maximum drawdown, drawdown duration, recovery time

#### Level 3: Trade-Level Attribution
- Per-trade metrics: P&L, holding period, slippage, commission
- Entry timing: how much alpha was captured vs. theoretical maximum?
- Exit timing: premature exits vs. late exits
- Position sizing effectiveness: did Kelly/vol-targeting add value?

#### Level 4: Skill Attribution
- Per-skill performance in the chain:
  - Regime detection accuracy (was the regime call correct?)
  - Signal generation quality (information coefficient, information ratio)
  - Strategy selection quality (did the meta-learner pick the right strategy?)
  - Position sizing efficiency (actual growth rate vs. Kelly optimal)
  - Risk management effectiveness (drawdowns prevented vs. alpha sacrificed)

### Automated Feedback Loop Architecture

```python
class FeedbackLoop:
    def __init__(self, performance_window=60):  # 60 trading days
        self.metrics_history = []
        self.performance_window = performance_window

    def collect_metrics(self, trade_results, market_data):
        """Collect and store performance metrics after each period"""
        metrics = {
            'date': trade_results.date,
            'strategy_returns': self.compute_strategy_returns(trade_results),
            'regime_accuracy': self.evaluate_regime_calls(trade_results, market_data),
            'signal_quality': self.compute_information_coefficient(trade_results),
            'sizing_efficiency': self.evaluate_position_sizing(trade_results),
            'risk_adjusted_return': self.compute_sharpe(trade_results),
            'drawdown': self.compute_drawdown(trade_results),
        }
        self.metrics_history.append(metrics)
        return metrics

    def diagnose(self):
        """Identify which skills in the chain are underperforming"""
        recent = self.metrics_history[-self.performance_window:]
        diagnostics = {}

        # Check each skill
        diagnostics['regime_detection'] = np.mean([m['regime_accuracy'] for m in recent])
        diagnostics['signal_quality'] = np.mean([m['signal_quality'] for m in recent])
        diagnostics['sizing_efficiency'] = np.mean([m['sizing_efficiency'] for m in recent])

        # Flag underperforming skills
        flags = []
        if diagnostics['regime_detection'] < 0.55:
            flags.append('regime_detection_degraded')
        if diagnostics['signal_quality'] < 0.03:  # IC below threshold
            flags.append('signal_quality_low')
        if diagnostics['sizing_efficiency'] < 0.7:
            flags.append('position_sizing_suboptimal')

        return diagnostics, flags

    def recommend_actions(self, flags):
        """Generate specific improvement actions"""
        actions = []
        if 'regime_detection_degraded' in flags:
            actions.append('retrain_hmm_model')
            actions.append('increase_hmm_features')
        if 'signal_quality_low' in flags:
            actions.append('walk_forward_reoptimize_signals')
            actions.append('check_feature_importance_drift')
        if 'position_sizing_suboptimal' in flags:
            actions.append('recalibrate_kelly_parameters')
            actions.append('check_volatility_estimation')
        return actions
```

### Why Feedback Loops Fail

Common attribution errors that break the learning cycle:
1. **Confusing luck with skill**: Random wins feel like validation; short-term outcomes
   are confused with long-term edge
2. **Emotional feedback replacing strategic feedback**: Mood management replaces
   systematic analysis
3. **Ignoring friction costs**: Slippage, commissions, and taxes erode actual edge
4. **Lack of statistical rigor**: Making strategy changes based on too few observations
   (need 200+ trades for statistical significance)

### For Swing/Position Trading

- Review frequency: Weekly performance review, monthly deep-dive attribution
- Minimum sample: Wait for 50+ trades before making strategy changes
- Friction tracking: Log all costs -- commissions, slippage, spread, market impact
- Regime-conditional evaluation: Evaluate strategy performance within each regime separately

---

## 9. Kelly Criterion and Dynamic Position Sizing

### The Core Formula

**Single asset**: f* = (bp - q) / b

Where:
- f* = fraction of capital to bet
- b = odds (reward-to-risk ratio)
- p = probability of winning
- q = probability of losing (1 - p)

**Multi-asset**: w* = Sigma_inverse * mu

Where:
- w* = vector of optimal weights
- Sigma_inverse = inverse of the covariance matrix
- mu = vector of expected excess returns

### Why Kelly Matters in the Strategy Chain

Kelly criterion is the mathematically optimal bridge between signal generation and
position sizing. It translates the *strength of the edge* into the *size of the bet*,
which is exactly what a position-sizing skill should do in the chain.

### Fractional Kelly: The Practitioner's Choice

| Kelly Fraction | Expected Return Reduction | Variance Reduction | Use Case |
|---------------|--------------------------|-------------------|----------|
| Full Kelly | 0% | 0% | Theoretical optimum only |
| 1/2 Kelly | ~12% | ~50% | Aggressive practitioners |
| 1/3 Kelly | ~17% | ~67% | Moderate risk tolerance |
| 1/4 Kelly | ~20% | ~80% | Conservative (recommended) |

**Key insight**: 1/4 Kelly reduces expected return by only ~20% but reduces variance by ~80%.
This is the recommended starting point for position trading systems where drawdown control
is critical.

### Dynamic Kelly Implementation

```python
class DynamicKellySizer:
    def __init__(self, kelly_fraction=0.25, lookback=252, min_trades=30):
        self.kelly_fraction = kelly_fraction
        self.lookback = lookback
        self.min_trades = min_trades

    def compute_kelly_size(self, strategy_returns, regime_confidence):
        """
        Compute position size using fractional Kelly with regime adjustment.

        Parameters:
        - strategy_returns: recent trade returns for the specific strategy
        - regime_confidence: confidence in current regime classification (0-1)
        """
        if len(strategy_returns) < self.min_trades:
            return 0.01  # Minimum size until enough data

        # Estimate edge parameters
        win_rate = (strategy_returns > 0).mean()
        avg_win = strategy_returns[strategy_returns > 0].mean()
        avg_loss = abs(strategy_returns[strategy_returns < 0].mean())

        if avg_loss == 0:
            return 0.01

        odds = avg_win / avg_loss

        # Classic Kelly
        kelly = (odds * win_rate - (1 - win_rate)) / odds

        # Apply fraction
        position_size = kelly * self.kelly_fraction

        # Adjust for regime confidence
        # Lower confidence = smaller position
        position_size *= regime_confidence

        # Floor and ceiling
        position_size = max(0.005, min(position_size, 0.15))  # 0.5% to 15%

        return position_size

    def compute_portfolio_kelly(self, expected_returns, cov_matrix):
        """
        Multi-asset Kelly for portfolio of strategies.
        w* = Sigma_inverse * mu
        """
        import numpy as np

        cov_inv = np.linalg.inv(cov_matrix)
        full_kelly_weights = cov_inv @ expected_returns

        # Apply fractional Kelly
        weights = full_kelly_weights * self.kelly_fraction

        # Normalize to ensure sum of absolute weights <= 1
        total_exposure = np.abs(weights).sum()
        if total_exposure > 1.0:
            weights = weights / total_exposure

        return weights
```

### Integration with Risk Management

Kelly provides the *ideal* position size; risk management provides the *maximum* position
size. The actual position size is the minimum of the two:

```
Actual Size = min(Kelly Size, Risk Budget Limit, Volatility Target Limit, Max Position Limit)
```

### Key Challenges

1. **Parameter sensitivity**: Kelly is extremely sensitive to estimation errors. If your
   win rate estimate is off by 5%, your position size can be off by 50%+
2. **Garbage in, garbage out**: Expected returns and covariance structures are estimates
   with significant uncertainty
3. **Rebalancing costs**: Kelly theoretically wants continuous rebalancing, but transaction
   costs erode returns. For position trading, weekly or monthly rebalancing is practical
4. **Non-normal returns**: Kelly assumes log-normal returns; fat tails in real markets
   can cause worse-than-expected drawdowns

### Best Practice for Position Trading

Use 1/4 Kelly as the baseline, with Bayesian updating of edge estimates. As your track
record grows and parameter estimates become more reliable, you can gradually increase
toward 1/3 or 1/2 Kelly. Never use full Kelly in live trading.

---

## 10. Risk Management as a Skill in the Chain

### Risk Management Architecture

Risk management operates at multiple levels, forming its own hierarchy within the chain:

```
Trade-Level Risk
    |
    v
Strategy-Level Risk Management System (SLRMS)
    |
    v
Portfolio-Level / Global Risk Management System (GRMS)
    |
    v
System-Level (circuit breakers, kill switches)
```

### Trade-Level Risk Controls

#### Adaptive ATR-Based Stop Losses

For position trading:
- ATR period: 21-30 days
- Multiplier: 2.5-3.5x ATR (wider than swing trading)
- The stop trails dynamically as volatility changes

```python
class AdaptiveStopLoss:
    def __init__(self, atr_period=21, base_multiplier=3.0):
        self.atr_period = atr_period
        self.base_multiplier = base_multiplier

    def compute_stop(self, prices, adx_value):
        """
        Compute adaptive stop loss using ATR with ADX-based adjustment.

        In strong trends (ADX > 25): use standard multiplier
        In weak trends (ADX < 25): increase multiplier by 50%
        """
        atr = self.compute_atr(prices, self.atr_period)
        current_price = prices[-1]

        if adx_value > 25:
            multiplier = self.base_multiplier  # Strong trend: standard
        else:
            multiplier = self.base_multiplier * 1.5  # Weak trend: wider stop

        stop_distance = atr * multiplier
        stop_price = current_price - stop_distance  # For long positions

        return stop_price, stop_distance

    def compute_position_size(self, account_equity, risk_per_trade, stop_distance):
        """
        ATR-based position sizing:
        Position Size = Dollar Risk / Stop Distance
        """
        dollar_risk = account_equity * risk_per_trade  # e.g., 1% of equity
        position_size = dollar_risk / stop_distance
        return position_size
```

#### Chandelier Exit
- Tracks highest high during the trade
- Stop = Highest High - (ATR x Multiplier)
- Particularly effective for position trading trend-following strategies

#### Time-Based Exits
- Maximum holding period stops for strategies expected to resolve within a timeframe
- Exit if trade hasn't reached target within N bars

### Strategy-Level Risk Management (SLRMS)

- **Maximum drawdown per strategy**: If a strategy draws down more than X% (e.g., 15%),
  reduce its allocation by 50% or halt it entirely
- **Consecutive loss limit**: After N consecutive losses, reduce position size
- **Correlation monitoring**: If strategy behavior deviates from expected correlation
  structure, flag for review
- **Performance-based sizing**: Automatically reduce position sizes during drawdowns,
  increase during equity highs

### Portfolio-Level Risk Management (GRMS)

- **Maximum portfolio drawdown**: Hard limit (e.g., 20% from peak)
- **Concentration limits**: No single position > 5-10% of portfolio
- **Sector/factor exposure limits**: Cap exposure to any single factor
- **Correlation-adjusted VaR**: Monitor Value at Risk across all strategies
- **Stress testing**: Regular stress tests against historical crisis scenarios
  (2008, 2020 COVID crash, 2022 rate shock)

### Portfolio Hedging Strategies

1. **Index options**: Buy put protection on correlated indices when portfolio exposure is high
2. **Pairs trading overlays**: Long/short pairs that provide natural hedging
3. **VIX-based hedging**: VXX or VIX calls as portfolio insurance (strong negative
   correlation with equities)
4. **Dynamic hedge ratios**: Adjust hedge ratios based on regime detection output
5. **Tail risk hedging**: Out-of-the-money puts for catastrophic risk protection

### System-Level Controls

- **Circuit breakers**: Automatic system shutdown if daily loss exceeds threshold
- **Rate limits**: Maximum number of orders per period
- **Kill switches**: Manual override to flatten all positions
- **Redundancy**: Backup systems for critical risk checks

### Risk Management as Part of the Self-Improvement Loop

Risk parameters should be included in the walk-forward optimization:
- Stop-loss multipliers
- Position sizing parameters (Kelly fraction, risk per trade)
- Maximum allocation per strategy
- Drawdown thresholds for strategy reduction

This means risk management itself improves over time through the same feedback loop
that improves signal generation and strategy selection.

---

## 11. Unified Skill Chain Architecture

### Complete System Architecture

```
===========================================================================
                    SKILL CHAIN TRADING SYSTEM
===========================================================================

Layer 1: DATA INFRASTRUCTURE
  [Market Data Feed] --> [Alt Data Sources] --> [Data Validation]
          |                      |                      |
          v                      v                      v
  [Feature Store] <---- [Feature Engineering Pipeline]

Layer 2: REGIME DETECTION (Skill 1)
  [Feature Store] --> [HMM Model] --> [Regime Label + Probabilities]
                      [GMM Model]     [Confidence Score]
                      [Statistical]

Layer 3: SIGNAL GENERATION (Skill 2)
  [Features + Regime] --> [Strategy A: Trend Following]
                          [Strategy B: Mean Reversion]
                          [Strategy C: Breakout]
                          [Strategy D: Factor Model]
                          [Strategy E: ML Ensemble]
                          --> [Raw Signals per Strategy]

Layer 4: STRATEGY SELECTION / META-LEARNING (Skill 3)
  [Raw Signals + Regime + Meta-Features] --> [Meta-Learner (XGBoost)]
                                          --> [Strategy Weights]
                                          --> [Ensemble Signal]

Layer 5: POSITION SIZING (Skill 4)
  [Ensemble Signal + Portfolio State] --> [Fractional Kelly Calculator]
                                      --> [Volatility Targeting]
                                      --> [Target Position Sizes]

Layer 6: RISK MANAGEMENT (Skill 5)
  [Target Positions + Risk Budget] --> [SLRMS per strategy]
                                   --> [GRMS portfolio level]
                                   --> [Drawdown controls]
                                   --> [Adjusted Positions]

Layer 7: EXECUTION (Skill 6)
  [Adjusted Positions] --> [Order Generation]
                       --> [Execution Algo (TWAP/VWAP)]
                       --> [Filled Orders]

Layer 8: PERFORMANCE ATTRIBUTION (Skill 7)
  [Trade History + Market Data] --> [Trade-level attribution]
                                --> [Strategy-level attribution]
                                --> [Factor attribution]
                                --> [Skill-level diagnostics]

Layer 9: SELF-IMPROVEMENT ENGINE (Skill 8)
  [Performance Metrics + Diagnostics] --> [Walk-Forward Reoptimization]
                                      --> [Bayesian Parameter Tuning]
                                      --> [Model Retraining]
                                      --> [Validation Gate]
                                      --> [Gradual Deployment]
                                      --> [Updated Models/Parameters]
                                            |
                                            v
                                  [Feeds back to Layers 2-6]

===========================================================================
```

### Implementation Recommendations

#### Technology Stack
- **Python**: Primary language for research and strategy development
- **Key Libraries**:
  - hmmlearn (regime detection)
  - scikit-learn, XGBoost, LightGBM (ML models, meta-learners)
  - PyPortfolioOpt, Riskfolio-Lib (portfolio optimization, HRP)
  - Optuna (Bayesian hyperparameter optimization)
  - Backtrader or QSTrader (backtesting framework)
  - pandas, numpy (data manipulation)

#### Event-Driven Architecture
- Each skill listens for events and publishes events
- Example: Regime Detection publishes "RegimeChanged" event; Strategy Selection listens
- Enables loose coupling and independent testing/deployment

#### Data Storage
- Feature store for pre-computed features (Redis or dedicated feature store)
- Trade database for execution records and performance tracking
- Model registry for versioned models and parameters

### Rebalancing Schedule for Position Trading

| Action | Frequency | Notes |
|--------|-----------|-------|
| Regime detection update | Daily | Run HMM on latest data |
| Signal generation | Daily | Generate signals from all strategies |
| Strategy weight update | Weekly | Meta-learner re-evaluates weights |
| Position rebalancing | Weekly | Adjust positions to target weights |
| Risk review | Daily | Monitor drawdowns, VaR |
| Walk-forward reoptimization | Monthly | Re-optimize key parameters |
| Full model retraining | Quarterly | Retrain ML models with new data |
| Deep performance review | Monthly | Full attribution analysis |

### Getting Started: Minimum Viable Skill Chain

For an initial implementation, start with this simplified chain:

1. **Regime Detection**: 2-state HMM (low-vol / high-vol) on SPY
2. **Signal Generation**: 2 strategies (trend following + mean reversion)
3. **Strategy Selection**: Simple rule (trend following in trending regime,
   mean reversion in ranging regime)
4. **Position Sizing**: 1/4 Kelly with ATR-based stops
5. **Risk Management**: 1% risk per trade, 15% max strategy drawdown
6. **Feedback**: Monthly walk-forward reoptimization of MA lengths and ATR multipliers

Then progressively add sophistication: more strategies, ML-based meta-learning,
ensemble methods, advanced attribution, and automated retraining.

---

## Key Sources and References

### Skill Chaining and HRL
- [Skill Discovery in Continuous RL Domains using Skill Chaining](https://users.cs.duke.edu/~jab/pubs/skillchain.pdf) (Konidaris & Barto)
- [SCaR: Refining Skill Chaining for Long-Horizon Tasks](https://proceedings.neurips.cc/paper_files/paper/2024/file/ca92ff06d973ece92cecc561757d500e-Paper-Conference.pdf) (NeurIPS 2024)
- [Hierarchical Reinforcement Learning: A Comprehensive Survey](https://dl.acm.org/doi/abs/10.1145/3453160)

### Multi-Strategy Portfolio Construction
- [Multi Strategy Management for Your Portfolio](https://quantpedia.com/multi-strategy-management-for-your-portfolio/) (QuantPedia)
- [Building a Multi-Strategy Portfolio](https://www.man.com/insights/building-a-multi-strategy-portfolio) (Man Group)
- [Multi-Strategy Portfolios: Combining Quantitative Strategies](https://blog.quantinsti.com/multi-strategy-portfolios-combining-quantitative-strategies-effectively/) (QuantInsti)
- [Multi-Strategy Portfolio Allocation](https://www.tradequantixnewsletter.com/p/multi-strategy-portfolio-allocation) (TradeQuantiX)

### Regime Detection
- [Market Regime Detection using HMMs in QSTrader](https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/) (QuantStart)
- [AI Market Regime Detection](https://syntiumalgo.com/ai-market-regime-detection/) (Syntium Algo)
- [Market Regime Detection using Statistical and ML Approaches](https://developers.lseg.com/en/article-catalog/article/market-regime-detection) (LSEG Devportal)
- [Regime-Adaptive Trading Python Guide](https://blog.quantinsti.com/regime-adaptive-trading-python/) (QuantInsti)
- [Decoding Market Regimes with Machine Learning](https://www.ssga.com/library-content/assets/pdf/global/pc/2025/decoding-market-regimes-with-machine-learning.pdf) (SSGA)

### Self-Improving Systems
- [A Self-Rewarding Mechanism in Deep RL for Trading Strategy Optimization](https://www.mdpi.com/2227-7390/12/24/4020) (MDPI Mathematics)
- [Developing a Self-Sustaining AI Trading System Using RL](https://www.researchgate.net/publication/390520469_Developing_a_Self-Sustaining_AI_Trading_System_Using_Reinforcement_Learning) (ResearchGate)
- [An Automated Adaptive Trading System](https://jfin-swufe.springeropen.com/articles/10.1186/s40854-025-00754-3) (Financial Innovation)
- [Building a Self-Updating ML Trading System](https://medium.com/@jsgastoniriartecabrera/building-a-self-updating-machine-learning-trading-system-from-python-training-to-metatrader-5-075659193a7d) (Medium)

### Walk-Forward Optimization
- [Walk-Forward Optimization Introduction](https://blog.quantinsti.com/walk-forward-optimization-introduction/) (QuantInsti)
- [Walk Forward Optimization](https://www.quantconnect.com/docs/v2/writing-algorithms/optimization/walk-forward-optimization) (QuantConnect)
- [Walk-Forward Analysis Deep Dive](https://www.interactivebrokers.com/campus/ibkr-quant-news/the-future-of-backtesting-a-deep-dive-into-walk-forward-analysis/) (Interactive Brokers)
- [How to Use Walk Forward Analysis](https://ungeracademy.com/posts/how-to-use-walk-forward-analysis-you-may-be-doing-it-wrong) (Unger Academy)

### Ensemble Methods
- [Ensemble Learning in Investment: An Overview](https://rpc.cfainstitute.org/research/foundation/2025/chapter-4-ensemble-learning-investment) (CFA Institute, 2025)
- [Ensemble Strategies](https://www.buildalpha.com/trading-ensemble-strategies/) (Build Alpha)
- [Stock Prediction with ML: Ensemble Modeling](https://alphascientist.com/ensemble_modeling.html) (The Alpha Scientist)
- [Ensembles in Machine Learning, Applications in Finance](https://pyfi.com/blogs/articles/ensembles-in-machine-learning-applications-in-finance) (PyFi)

### Meta-Learning
- [Meta-Learning the Optimal Mixture of Strategies for Online Portfolio Selection](https://arxiv.org/abs/2505.03659) (arXiv, 2025)
- [A Meta-Method for Portfolio Management Using ML for Adaptive Strategy Selection](https://arxiv.org/abs/2111.05935) (arXiv)

### Performance Attribution and Feedback
- [The 4-Step Feedback Loop for Consistent Profits](https://edgewonk.com/blog/feedback-loop-in-trading) (Edgewonk)
- [The Psychology of Losing: Broken Feedback Loops](https://www.daytrading.com/psychology-of-losing-broken-feedback-loops) (DayTrading.com)

### Kelly Criterion
- [Kelly Criterion: Practical Portfolio Optimization & Allocation](https://investwithcarl.com/learning-center/investment-basics/dynamic-adaptive-kelly-criterion-bridging-theory-and-practice-for-modern-portfolio-optimization/) (Invest with Carl)
- [Practical Implementation of the Kelly Criterion](https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2020.577050/full) (Frontiers)
- [Kelly Criterion in Portfolio Optimization](https://bsic.it/exploring-the-application-of-kellys-criterion-in-portfolio-optimization/) (BSIC)
- [KellyPortfolio GitHub](https://github.com/thk3421-models/KellyPortfolio)

### Risk Management
- [Risk Management Strategies for Algo Trading](https://www.luxalgo.com/blog/risk-management-strategies-for-algo-trading/) (LuxAlgo)
- [12 Best Risk Management Techniques and Strategies](https://www.quantifiedstrategies.com/risk-management-trading/) (Quantified Strategies)
- [ATR Stop-Loss Strategies](https://www.luxalgo.com/blog/5-atr-stop-loss-strategies-for-risk-control/) (LuxAlgo)
- [Dynamic ATR Trailing Stop Strategy](https://medium.com/@redsword_23261/dynamic-atr-trailing-stop-trading-strategy-market-volatility-adaptive-system-2c2df9f778f2) (Medium)

### System Architecture
- [Algorithmic Trading System Architecture](https://www.turingfinance.com/algorithmic-trading-system-architecture-post/) (Turing Finance)
- [A Modular Architecture for Systematic Quantitative Trading Systems](https://hiya31.medium.com/a-modular-architecture-for-systematic-quantitative-trading-systems-2a8d46463570) (Medium)
- [Quant Trading System Architecture & Infrastructure](https://mbrenndoerfer.com/writing/quant-trading-system-architecture-infrastructure) (Brenndoerfer)
- [Designing Scalable Trading Architectures](https://fintatech.com/blog/designing-scalable-trading-architectures-from-concept-to-execution/) (Fintatech)

### HRP Implementation
- [PyPortfolioOpt Documentation](https://pyportfolioopt.readthedocs.io/en/latest/OtherOptimizers.html)
- [Riskfolio-Lib HRP](https://medium.com/@orenji.eirl/hierarchical-risk-parity-with-python-and-riskfolio-lib-c0e60b94252e)
- [HRP on RAPIDS (GPU-Accelerated)](https://developer.nvidia.com/blog/hierarchical-risk-parity-on-rapids-an-ml-approach-to-portfolio-allocation/) (NVIDIA)
