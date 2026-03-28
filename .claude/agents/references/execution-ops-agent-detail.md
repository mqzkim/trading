## Order Type Decision Matrix

```
Signal Type       -> Order Type
----------------------------------
Swing entry       -> Limit (at mid or slight passive)
Position entry    -> Limit (split over 2-3 days via TWAP if size > 2% NAV)
ATR stop trigger  -> Stop-Limit
Tier-1/2 defense  -> Limit (allow 5 min for fill before converting to market)
Tier-3 emergency  -> Market (immediate, no wait)
Rebalance trim    -> Limit (end-of-day session, passive)
```

## Execution Log Schema

```json
{
  "order_id": "string",
  "symbol": "string",
  "side": "buy | sell",
  "order_type": "limit | stop_limit | market",
  "requested_qty": 0,
  "filled_qty": 0,
  "limit_price": 0.0,
  "stop_price": 0.0,
  "fill_avg_price": 0.0,
  "slippage_bps": 0.0,
  "submitted_at": "ISO8601",
  "filled_at": "ISO8601",
  "status": "filled | partial | canceled | rejected",
  "signal_reason": "string",
  "mode": "paper | live"
}
```

## Output
- Order confirmation: order_id, status, and submitted parameters immediately after submission
- Fill notification: fill_avg_price, filled_qty, slippage_bps vs mid at submission time
- Partial fill decision: action taken (re-submit or cancel-remainder) with rationale
- Execution summary: per-trade JSON log entry written to `logs/execution/YYYY-MM-DD.jsonl`
- Daily execution report: total trades, avg slippage (bps), fill rate (%), rejected orders

## Constraints
- Paper Trading is the default; never switch to Live mode without `ALPACA_LIVE=true` in environment
- Never hardcode API keys; read `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` from environment only
- Minimum holding period enforcement: do not submit a closing order for a position opened less than 2 weeks ago unless risk-auditor-agent has issued a Tier-2 or Tier-3 action
- Market orders require an explicit `force_market=true` flag in the signal payload; reject otherwise
- Log every order event synchronously before returning; silent execution failure is not acceptable
- Do not implement retry loops with sleep; surface errors immediately for the orchestrator to handle
- Reference: docs/trading-methodology-overview.md section 3.1 Phase 5, trading/.claude/CLAUDE.md broker section