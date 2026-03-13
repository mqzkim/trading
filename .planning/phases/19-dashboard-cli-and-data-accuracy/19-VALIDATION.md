---
phase: 19
slug: dashboard-cli-and-data-accuracy
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4+ with pytest-asyncio |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/unit/test_dashboard_web.py tests/unit/test_cli_serve.py -x -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_dashboard_web.py tests/unit/test_cli_serve.py -x -v`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 01 | 0 | DASH-01 | unit | `pytest tests/unit/test_cli_serve.py -x` | ❌ W0 | ⬜ pending |
| 19-01-02 | 01 | 1 | DASH-01 | unit | `pytest tests/unit/test_cli_serve.py -x` | ❌ W0 | ⬜ pending |
| 19-02-01 | 02 | 1 | DASH-04 | unit | `pytest tests/unit/test_dashboard_web.py::test_risk_drawdown_from_portfolio -x` | ❌ W0 | ⬜ pending |
| 19-02-02 | 02 | 1 | DASH-08 | unit | `pytest tests/unit/test_dashboard_web.py::test_equity_curve_accumulates_pnl -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_cli_serve.py` — stubs for DASH-01 (serve command unit test with mock uvicorn)
- [ ] `tests/unit/test_dashboard_web.py::test_risk_drawdown_from_portfolio` — covers DASH-04/INT-02
- [ ] `tests/unit/test_dashboard_web.py::test_equity_curve_accumulates_pnl` — covers DASH-08/INT-03

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Browser auto-open on WSL2 | DASH-01 | WSL2 browser launch unreliable in CI | Run `trade serve`, verify browser opens at localhost |
| Visual risk gauge rendering | DASH-04 | Chart rendering requires browser | Open dashboard, check gauge shows non-zero drawdown |
| Equity curve visual accuracy | DASH-08 | Chart rendering requires browser | Open dashboard, check curve shows upward/downward P&L trend |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
