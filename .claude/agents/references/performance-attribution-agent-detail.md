## Attribution Hierarchy

```
Level 1 — Portfolio:
  total_return = benchmark_return + portfolio_alpha
  risk_decomposition: market_beta * market_return + factor_tilts + residual

Level 2 — Strategy:
  portfolio_alpha = Σ (strategy_weight_i * strategy_alpha_i)
  per-strategy: Sharpe, Sortino, Calmar, win_rate, profit_factor, max_drawdown

Level 3 — Trade:
  strategy_alpha = Σ (trade_pnl_j / NAV_at_entry_j)
  per-trade: entry_score, exit_reason, holding_days, realized_r_multiple (pnl / initial_risk)

Level 4 — Skill:
  skill = individual signal or rule within a strategy (e.g., "momentum_12_1", "piotroski_filter")
  skill_IC = rank_corr(signal_value_at_entry, realized_return_over_holding_period)
  skill contribution = IC * sqrt(breadth) * sigma_p  (Fundamental Law of Active Management)
```

## Key Performance Thresholds

```
Signal IC (rolling 63-day)  >= 0.03        (below = signal degraded, flag for review)
Signal IC (rolling 252-day) >= 0.03        (below = signal structurally broken, retire candidate)
Kelly Efficiency            >= 0.70        (realized / theoretical; below = sizing or execution issue)
Strategy Sharpe             >= 1.0         (minimum for continued allocation)
Strategy Sortino            >= 1.5         (minimum for continued allocation)
Win Rate (swing strategies) >= 0.55        (below = re-evaluate entry/exit logic)
Profit Factor               >= 1.5         (total_profit / total_loss)
R-Multiple Average          >= 1.5R        (realized gain per unit of initial risk)
```

## Monthly Report Structure

```
Section 1 — Portfolio Summary:
  NAV, total return MTD/YTD, benchmark comparison, Sharpe/Sortino/Calmar MTD/YTD

Section 2 — Strategy Attribution:
  Ranked table: strategy_name, weight, contribution_bps, Sharpe, max_drawdown
  Flag any strategy with Sharpe < 1.0 or 63-day IC < 0.03

Section 3 — Signal Quality:
  Per-signal IC table (63-day and 252-day rolling)
  Degradation alerts: signals where IC dropped > 50% from prior month

Section 4 — Kelly Efficiency:
  Per-strategy: theoretical_kelly, applied_size, efficiency_ratio
  Flag any strategy with efficiency < 70%

Section 5 — Trade Analysis:
  Distribution of R-multiples, holding periods, and exit reasons
  Behavioral bias flags: e.g., early exit pattern, stop-too-tight pattern

Section 6 — Improvement Actions (ranked by expected impact):
  Action, target metric, expected improvement, priority (High/Medium/Low)
```

## Output
- Attribution JSON: nested dict matching the four-level hierarchy with all computed metrics
- IC dashboard: per-signal table with 63-day IC, 252-day IC, and trend direction
- Kelly efficiency table: per-strategy efficiency ratio and sizing recommendations
- Bias flag list: detected behavioral patterns with supporting trade-level evidence
- Monthly PDF-ready report: all sections above, generated as structured markdown
- Improvement action list: prioritized list of changes for the self-improvement engine

## Constraints
- Do not expose individual trade P&L in commercial API outputs (personal use only)
- Attribution computations must use only realized data; no forward-looking adjustments
- IC calculations use Spearman rank correlation (robust to outliers), not Pearson
- A signal with 252-day IC < 0.03 for two consecutive months triggers an automatic retirement recommendation
- Kelly efficiency below 50% triggers an immediate sizing review request to risk-auditor-agent
- All monthly reports must be written to `docs/reports/YYYY-MM-performance.md`
- Reference: docs/trading-methodology-overview.md section 2.1 and 2.3, docs/verified-methodologies-and-risk-management.md section 6