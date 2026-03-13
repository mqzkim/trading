---
phase: 19-dashboard-cli-and-data-accuracy
verified: 2026-03-14T00:00:00Z
status: passed
score: 5/5 must-haves verified
gaps: []
human_verification:
  - test: "Run `trade serve` and confirm browser opens the dashboard"
    expected: "Browser window opens at http://0.0.0.0:8000/dashboard/ approximately 1.5 seconds after server start"
    why_human: "uvicorn.run blocks; threading.Timer browser-open behavior requires a running uvicorn instance and a display environment — not testable headlessly"
  - test: "With a portfolio in SQLite that has drawdown > 0, load /dashboard/risk in the browser"
    expected: "Risk gauge shows the actual drawdown percentage (e.g., 12.0) instead of 0.0"
    why_human: "The SQLite bootstrap path is only exercised at runtime; unit tests mock the portfolio_handler"
---

# Phase 19: Dashboard CLI & Data Accuracy — Verification Report

**Phase Goal:** Dashboard is fully operational from CLI with accurate initial data — `trade serve` launches uvicorn, risk gauge shows real drawdown on load, equity curve accumulates P&L
**Verified:** 2026-03-14
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User runs `trade serve` and uvicorn starts the dashboard at localhost | VERIFIED | `serve()` registered in Typer app at `cli/main.py:1783`; calls `uvicorn.run(dashboard_app, host=_host, port=_port, log_level="info")` at line 1811 |
| 2 | Browser auto-opens the dashboard URL (unless --no-browser) | VERIFIED | `threading.Timer(1.5, _open_browser)` branch at lines 1801-1809; `test_serve_opens_browser_by_default` passes; `test_serve_no_browser_flag` passes |
| 3 | `trade serve --host 127.0.0.1 --port 9000` overrides settings defaults | VERIFIED | Lines 1792-1793 apply CLI args first, fallback to `settings.DASHBOARD_HOST/PORT`; `test_serve_custom_host_port` passes |
| 4 | Risk page drawdown gauge shows actual portfolio drawdown on initial load, not hardcoded 0.0 | VERIFIED | `RiskQueryHandler.handle()` lines 472-483 query `portfolio_handler._portfolio_repo.find_by_id("default")` and compute `portfolio.drawdown * 100`; `test_risk_drawdown_from_portfolio` asserts "12.0" in HTML response |
| 5 | Equity curve chart shows accumulated P&L over time for executed trades | VERIFIED | `_build_equity_curve()` lines 289-304 compute `(target - entry) * qty` per trade and accumulate into `cumulative`; `test_equity_curve_accumulates_pnl` asserts final value != 0.0 |

**Score: 5/5 truths verified**

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `cli/main.py` | `serve()` command | VERIFIED | Function exists at line 1783, 18 commands registered including "serve" |
| `tests/unit/test_cli_serve.py` | Unit tests for serve command | VERIFIED | 91 lines, 4 test cases in `TestServeCommand` class; all 4 pass |
| `src/dashboard/application/queries.py` | `RiskQueryHandler` with real drawdown, `OverviewQueryHandler` with P&L accumulation | VERIFIED | `RiskQueryHandler.__init__` stores `self._ctx` (line 437); drawdown block lines 471-483; `_build_equity_curve` P&L loop lines 289-304 |
| `tests/unit/test_dashboard_web.py` | Tests for drawdown and equity curve accuracy | VERIFIED | Contains `test_risk_drawdown_from_portfolio` at line 413; 484 total lines |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cli/main.py::serve` | `src.dashboard.presentation.app::create_dashboard_app` | import and call with `_get_ctx()` context | WIRED | Line 1790: `from src.dashboard.presentation.app import create_dashboard_app`; line 1796: `dashboard_app = create_dashboard_app(ctx)` |
| `cli/main.py::serve` | `uvicorn.run` | programmatic launch (not subprocess) | WIRED | Line 7: `import uvicorn` (module-level); line 1811: `uvicorn.run(dashboard_app, host=_host, port=_port, log_level="info")` |
| `src/dashboard/application/queries.py::RiskQueryHandler` | `portfolio_handler._portfolio_repo.find_by_id` | ctx dict access | WIRED | Lines 474-481: `handler = self._ctx.get("portfolio_handler")` -> `repo.find_by_id("default")` -> `portfolio.drawdown * 100` |
| `src/dashboard/application/queries.py::_build_equity_curve` | trade_history dicts | entry_price/take_profit_price subtraction for P&L | WIRED | Lines 291-301: `entry = trade.get("entry_price")`, `target = trade.get("take_profit_price")`, `trade_pnl = (target - entry) * qty` |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DASH-01 | 19-01-PLAN.md | Dashboard accessible without manual uvicorn command | SATISFIED | `trade serve` command closes INT-01 gap; the dashboard was already built in Phase 16 — Phase 19 adds the CLI entrypoint |
| DASH-04 | 19-02-PLAN.md | Dashboard displays risk metrics including drawdown gauge | SATISFIED | INT-02 closed: `RiskQueryHandler` now reads real `portfolio.drawdown` instead of hardcoded 0.0 |
| DASH-08 | 19-02-PLAN.md | Dashboard displays equity curve chart | SATISFIED | INT-03 closed: `_build_equity_curve` accumulates P&L from entry/target price spread instead of returning flat zero line |

**Note on traceability table:** `REQUIREMENTS.md` traceability table maps DASH-01, DASH-04, and DASH-08 to Phase 16 (where the dashboard was originally built). Phase 19 closes integration gaps (INT-01, INT-02, INT-03) that existed after Phase 16 — the traceability table reflects original completion, not gap-closure. Both Phase 16 and Phase 19 contribute to these requirements. No orphaned requirements.

---

## Anti-Patterns Found

No anti-patterns detected in phase 19 files.

Checked: `cli/main.py`, `src/dashboard/application/queries.py`, `tests/unit/test_cli_serve.py`, `tests/unit/test_dashboard_web.py`

- No TODO/FIXME/PLACEHOLDER comments
- No hardcoded stubs (`return null`, `return {}`, `return []`)
- No empty handlers (no `console.log`-only implementations)
- `webbrowser.open` wrapped in try/except for WSL2/headless environments — intentional defensive pattern, not a stub

---

## Test Results

| Test Suite | Tests | Result |
|------------|-------|--------|
| `tests/unit/test_cli_serve.py` | 4/4 | PASS |
| `tests/unit/test_dashboard_web.py` (full suite) | 29/29 | PASS |
| New accuracy tests only | 4/4 | PASS |

Commits verified in git log:
- `ed7fb09` — test(19-01): add failing tests for trade serve command
- `0b3f4aa` — feat(19-01): implement trade serve command with browser auto-open
- `b5c5b9c` — test(19-02): add failing tests for drawdown and equity curve accuracy
- `a9049f5` — fix(19-02): real drawdown in risk gauge and P&L accumulation in equity curve

---

## Human Verification Required

### 1. Browser auto-open in live environment

**Test:** Run `trade serve` (without `--no-browser`) on a machine with a display
**Expected:** Browser opens at `http://0.0.0.0:8000/dashboard/` approximately 1.5 seconds after server starts
**Why human:** `uvicorn.run()` blocks the process; `threading.Timer` behavior is mocked in unit tests and cannot be verified headlessly

### 2. Risk gauge with real portfolio data

**Test:** With a portfolio record in SQLite that has a non-zero drawdown, load `/dashboard/risk` in the browser
**Expected:** Drawdown gauge shows the actual percentage (not 0.0)
**Why human:** Unit tests mock the portfolio handler; the SQLite bootstrap path only runs during real execution

---

## Gaps Summary

No gaps. All 5 observable truths verified, all 4 artifacts confirmed substantive and wired, all 4 key links confirmed connected, all 3 requirements satisfied.

Phase goal achieved: `trade serve` CLI command exists and is wired to uvicorn + dashboard app; risk gauge reads real drawdown from Portfolio aggregate; equity curve accumulates P&L from trade entry/target price spread.

---

_Verified: 2026-03-14_
_Verifier: Claude (gsd-verifier)_
