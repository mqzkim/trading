---
phase: 4
slug: execution-and-interface
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 7.4 + pytest-asyncio >= 0.21 |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/unit/test_FILE.py -x --tb=short` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** `pytest tests/unit/test_CHANGED_FILE.py -x`
- **After every plan wave:** `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| T4.1 | 04-01 | 1 | EXEC-01 | unit | `pytest tests/unit/test_trade_plan.py -x` | No | Pending |
| T4.2 | 04-01 | 1 | EXEC-02 | unit | `pytest tests/unit/test_trade_approval.py -x` | No | Pending |
| T4.3 | 04-01 | 1 | EXEC-03 | unit | `pytest tests/unit/test_alpaca_adapter.py -x` | No | Pending |
| T4.4 | 04-01 | 1 | EXEC-04 | unit | `pytest tests/unit/test_bracket_order.py -x` | No | Pending |
| T4.5 | 04-02 | 2 | INTF-01 | unit | `pytest tests/unit/test_cli_dashboard.py -x` | No | Pending |
| T4.6 | 04-02 | 2 | INTF-02 | unit | `pytest tests/unit/test_cli_screener.py -x` | No | Pending |
| T4.7 | 04-03 | 2 | INTF-03 | unit | `pytest tests/unit/test_watchlist.py -x` | No | Pending |
| T4.8 | 04-03 | 2 | INTF-04 | unit | `pytest tests/unit/test_alerts.py -x` | No | Pending |

---

## Wave 0 Test Gaps

- [ ] `tests/unit/test_trade_plan.py` -- EXEC-01: TradePlan VO creation with valid fields + reasoning trace
- [ ] `tests/unit/test_trade_approval.py` -- EXEC-02: Human approval flow (approve/reject/modify)
- [ ] `tests/unit/test_alpaca_adapter.py` -- EXEC-03: AlpacaExecutionAdapter mock mode + bracket order
- [ ] `tests/unit/test_bracket_order.py` -- EXEC-04: Bracket order spec creation + validation
- [ ] `tests/unit/test_cli_dashboard.py` -- INTF-01: Dashboard command renders portfolio table
- [ ] `tests/unit/test_cli_screener.py` -- INTF-02: Screener command renders top-N results
- [ ] `tests/unit/test_watchlist.py` -- INTF-03: Watchlist CRUD operations
- [ ] `tests/unit/test_alerts.py` -- INTF-04: Alert events fire on stop/target/drawdown

Note: `tests/unit/test_execution_planner.py`, `tests/unit/test_paper_trading.py`, and `tests/unit/test_cli_commands.py` already exist for the legacy `personal/` layer. New tests will test the DDD-compliant `src/execution/` and extended `cli/` layers.
