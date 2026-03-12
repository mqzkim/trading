# Requirements: Intrinsic Alpha Trader

**Defined:** 2026-03-13
**Core Value:** Every recommendation must be explainable and risk-controlled — capital preservation and positive expectancy over maximizing returns.

## v1.2 Requirements

Requirements for Production Trading & Dashboard milestone. Each maps to roadmap phases.

### Safety Infrastructure

- [ ] **SAFE-01**: System requires explicit EXECUTION_MODE setting (paper/live enum, defaults to paper) — live mode cannot be triggered by credentials alone
- [ ] **SAFE-02**: Live mode uses separate adapter class with no mock fallback — order failures raise errors, never return phantom fills
- [ ] **SAFE-03**: Paper and live Alpaca accounts use separate API key pairs configured independently
- [ ] **SAFE-04**: Pipeline startup reconciles SQLite position records with Alpaca broker positions and flags divergences
- [ ] **SAFE-05**: Drawdown cooldown state persists in SQLite and survives process restarts (30-day cooling period)
- [ ] **SAFE-06**: Kill switch cancels all open orders and halts pipeline immediately via CLI and dashboard
- [ ] **SAFE-07**: System polls order status until terminal state (filled, rejected, cancelled) before proceeding
- [ ] **SAFE-08**: After bracket order fill, system verifies stop-loss and take-profit legs are confirmed active

### Automated Pipeline

- [ ] **PIPE-01**: Daily automated pipeline runs ingest → regime → score → signal → plan → budget check → execute after market close
- [ ] **PIPE-02**: Pipeline checks NYSE market calendar and skips weekends, holidays, and early-close days
- [ ] **PIPE-03**: Each pipeline run logs stages completed, symbol counts, errors, and next scheduled run to SQLite
- [ ] **PIPE-04**: Dry-run mode executes full pipeline without submitting orders (for validation)
- [ ] **PIPE-05**: Individual pipeline stages retry with exponential backoff on transient failures (e.g., yfinance timeouts)
- [ ] **PIPE-06**: Pipeline auto-halts execution when regime is Crisis or drawdown tier >= 2
- [ ] **PIPE-07**: APScheduler with SQLite job persistence manages schedule across process restarts

### Strategy & Budget Approval

- [ ] **APPR-01**: User can create strategy approval with score threshold, regime allow-list, max per-trade %, and mandatory expiration date
- [ ] **APPR-02**: User can set daily budget cap with real-time spent/remaining tracking per pipeline run
- [ ] **APPR-03**: Trades exceeding approved budget or strategy parameters queue for manual review instead of auto-executing
- [ ] **APPR-04**: Regime change event automatically suspends active strategy approval until user re-approves
- [ ] **APPR-05**: Drawdown tier 2+ automatically suspends strategy approval and halts automated execution

### Live Trading

- [ ] **LIVE-01**: System connects to Alpaca live account when EXECUTION_MODE=live with valid live API credentials
- [ ] **LIVE-02**: SafeExecutionService wraps broker adapter with circuit breaker and budget enforcement pre-checks
- [ ] **LIVE-03**: AlpacaOrderMonitor runs as background task tracking all open orders until terminal state
- [ ] **LIVE-04**: TradingStream WebSocket receives real-time fill events and publishes to event bus
- [ ] **LIVE-05**: Initial live deployment uses max 25% capital allocation, increasing as reliability is demonstrated
- [ ] **LIVE-06**: Circuit breaker halts live trading after 3 consecutive order failures

### Web Dashboard

- [ ] **DASH-01**: Dashboard shows portfolio overview with holdings, per-position P&L, and allocation chart
- [ ] **DASH-02**: Dashboard displays scoring and signal results for latest pipeline run
- [ ] **DASH-03**: Dashboard shows trade history with execution details (entry, stop, target, fill price, P&L)
- [ ] **DASH-04**: Dashboard displays risk metrics (drawdown gauge, sector exposure, position limit utilization)
- [ ] **DASH-05**: Dashboard shows pipeline status (last run time, next scheduled, stage results, symbol counts)
- [ ] **DASH-06**: User can view and manage strategy approval and daily budget from dashboard
- [ ] **DASH-07**: Dashboard receives real-time updates via SSE for order fills, pipeline events, and alerts
- [ ] **DASH-08**: Dashboard displays equity curve chart with regime overlay
- [ ] **DASH-09**: Dashboard shows prominent paper/live mode banner (red for live, green for paper)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Dashboard Enhancements

- **DASH-10**: Mobile-responsive dashboard layout
- **DASH-11**: Multi-user dashboard with authentication (beyond single-user)
- **DASH-12**: React/Next.js frontend (if HTMX proves insufficient)

### Extended Trading

- **LIVE-07**: KIS live trading for Korean market
- **LIVE-08**: Multi-broker simultaneous execution
- **LIVE-09**: Options/derivatives integration

### Advanced Automation

- **PIPE-08**: Per-symbol scoring history with 90-day evolution chart
- **PIPE-09**: ML-based signal weight optimization

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full auto-execution without any human oversight | Strategy/budget approval still required — no unsupervised trading |
| Mobile app | Web dashboard first; mobile-responsive in v2 |
| Real-time intraday trading | Daily granularity for mid-term holding period |
| Social/sentiment scoring | Focus on fundamentals + technicals first |
| Multi-user SaaS dashboard | Personal tool; commercial API serves external users separately |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SAFE-01 | — | Pending |
| SAFE-02 | — | Pending |
| SAFE-03 | — | Pending |
| SAFE-04 | — | Pending |
| SAFE-05 | — | Pending |
| SAFE-06 | — | Pending |
| SAFE-07 | — | Pending |
| SAFE-08 | — | Pending |
| PIPE-01 | — | Pending |
| PIPE-02 | — | Pending |
| PIPE-03 | — | Pending |
| PIPE-04 | — | Pending |
| PIPE-05 | — | Pending |
| PIPE-06 | — | Pending |
| PIPE-07 | — | Pending |
| APPR-01 | — | Pending |
| APPR-02 | — | Pending |
| APPR-03 | — | Pending |
| APPR-04 | — | Pending |
| APPR-05 | — | Pending |
| LIVE-01 | — | Pending |
| LIVE-02 | — | Pending |
| LIVE-03 | — | Pending |
| LIVE-04 | — | Pending |
| LIVE-05 | — | Pending |
| LIVE-06 | — | Pending |
| DASH-01 | — | Pending |
| DASH-02 | — | Pending |
| DASH-03 | — | Pending |
| DASH-04 | — | Pending |
| DASH-05 | — | Pending |
| DASH-06 | — | Pending |
| DASH-07 | — | Pending |
| DASH-08 | — | Pending |
| DASH-09 | — | Pending |

**Coverage:**
- v1.2 requirements: 35 total
- Mapped to phases: 0
- Unmapped: 35 ⚠️

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after initial definition*
