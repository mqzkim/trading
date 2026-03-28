## Limit Enforcement

```
Hard Limits (block trade if violated):
  single_stock_weight  <= 0.08  (8% of portfolio NAV)
  sector_weight        <= 0.25  (25% of portfolio NAV)
  per_trade_risk       <= 0.01  (1% of capital = position_size * stop_distance / NAV)
  kelly_fraction       <= 0.25  (Fractional Kelly cap, Full Kelly forbidden)
  atr_stop_multiplier  in [2.5, 3.5]  (ATR(21) based)

Soft Limits (warn, do not block):
  corr_cluster_weight  <= 0.20  (20% per correlation cluster)
  strategy_max_drawdown <= 0.15 (15% per strategy)
  daily_loss_circuit   >= -0.03 (halt new trades if daily P&L < -3%)
```

## Drawdown Defense Protocol

```
Tier 1 — Warning (portfolio drawdown > 10%):
  - Block all new position entries
  - Increase monitoring frequency to intraday
  - Notify orchestrator with tier-1 alert

Tier 2 — Defensive (portfolio drawdown > 15%):
  - Reduce all existing positions by 50%
  - Tighten stops to 2.5x ATR(21) minimum
  - Shift strategy weights toward Cash/Bonds (coordinate with regime-analyst-agent)
  - Notify orchestrator with tier-2 alert

Tier 3 — Emergency (portfolio drawdown > 20%):
  - Full liquidation of all positions (cash out)
  - Enforce minimum 1-month cooling period before re-entry
  - Recovery protocol: re-enter at 25% of normal size, increase by 25% every 2 weeks
  - Notify orchestrator with tier-3 alert and system review request
```

## Output
- Audit report: JSON with check_name, status (PASS/FAIL/WARN), current_value, limit_value for each constraint
- Corrective action list: ordered list of required trades or parameter changes
- Drawdown tier: current active tier (0-3) with NAV, HWM, and drawdown_pct
- Kelly validation: per-position table of full_kelly, fractional_kelly (1/4), applied_size
- VaR summary: daily 95% VaR, CVaR, and whether within target bounds

## Constraints
- Never suppress a limit breach — fail loudly with descriptive error including position ID, current value, and limit
- Do not catch audit exceptions just to re-throw them; let them propagate with full context
- Fractional Kelly multiplier is always exactly 0.25; do not allow runtime configuration above 0.25
- Drawdown tiers are cumulative: Tier 2 conditions also apply all Tier 1 actions
- Recovery re-entry requires explicit orchestrator approval after Tier 3 liquidation
- Reference: docs/verified-methodologies-and-risk-management.md sections 4.1-4.4, trading/.claude/CLAUDE.md risk limits