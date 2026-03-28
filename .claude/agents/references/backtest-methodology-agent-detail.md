## Walk-Forward Schedule

```
Strategy Type    IS Window    OOS Window    Roll Step    Window Type
-----------------------------------------------------------------
Position         3-5 years    6-12 months   3-6 months   Anchored (expanding)
Swing            1-2 years    3-6 months    1-3 months   Rolling
```

## Validation Gates (all must pass for promotion)

```
Gate 1 — PBO      : CSCV probability of overfitting < 10%
Gate 2 — WFE      : OOS_Sharpe / IS_Sharpe >= 0.50
Gate 3 — Sharpe   : t-stat > 2.0  (formula: SR * sqrt(T) / sqrt(1 + 0.5*SR^2) adjusted for non-normality)
Gate 4 — DSR      : Deflated Sharpe Ratio > 0 (accounts for N trial runs)
Gate 5 — Stability: performance drop < 25% when any single parameter shifted +/-10%
Gate 6 — Bias     : All 12 checklist items passed
```

## 12-Item Bias-Prevention Checklist

```
Survivorship Bias:
  [ ] 1. Universe includes delisted and bankrupt securities for the full test period
  [ ] 2. Data source confirmed to provide point-in-time (as-reported) fundamentals

Look-Ahead Bias:
  [ ] 3. Financial data lagged by >= 45 days from fiscal period end (earnings release lag)
  [ ] 4. All normalization uses only historical data up to the decision date (rolling window)
  [ ] 5. Universe membership determined only from data available on that date
  [ ] 6. ML model trained exclusively on data prior to each OOS window start

Overfitting:
  [ ] 7. Parameter count per strategy <= 4
  [ ] 8. PBO (CSCV) < 10%
  [ ] 9. Strategy was not designed by inspecting OOS data

Transaction Costs:
  [ ] 10. Round-trip cost applied: large-cap 0.1-0.3%, small-cap 0.5-1.0%
  [ ] 11. Slippage model applied for positions > 1% of 30-day ADV

Regime Coverage:
  [ ] 12. Backtest covers at least one full market cycle (bull + bear + sideways) and includes 2008, 2020 drawdown events
```

## Output
- Validation report: JSON with gate_name, status (PASS/FAIL), value, threshold for each gate
- WFA summary table: IS Sharpe, OOS Sharpe, WFE, and date range per fold
- PBO result: overfitting probability (%) with CSCV fold count used
- Parameter stability matrix: heatmap-ready dict of {param: {delta: performance_ratio}}
- Promotion decision: PROMOTE / REJECT / CONDITIONAL (with specific conditions to meet)
- Bias checklist output: all 12 items with PASS/FAIL and evidence notes

## Constraints
- A strategy with any Gate failure is REJECTED; no exceptions without explicit user override
- Do not run optimization on OOS data under any circumstances
- Minimum backtest length: 10 years or 2 full market cycles, whichever is longer
- Maximum parameter count: 4 per strategy; refuse to validate strategies with more
- All random seeds used in CSCV must be logged for reproducibility
- Report must include the exact data source, version, and date range used
- Reference: docs/verified-methodologies-and-risk-management.md section 10, docs/trading-methodology-overview.md section 3 Stage 3