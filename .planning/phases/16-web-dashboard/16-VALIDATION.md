---
phase: 16
slug: web-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4+ |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/unit/test_dashboard_web.py tests/unit/test_dashboard_sse.py tests/unit/test_dashboard_charts.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_dashboard_web.py tests/unit/test_dashboard_sse.py tests/unit/test_dashboard_charts.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 16-01-01 | 01 | 0 | DASH-01..09 | unit | `pytest tests/unit/test_dashboard_web.py tests/unit/test_dashboard_sse.py tests/unit/test_dashboard_charts.py -x` | ❌ W0 | ⬜ pending |
| 16-02-01 | 02 | 1 | DASH-01 | unit | `pytest tests/unit/test_dashboard_web.py::test_overview_page -x` | ❌ W0 | ⬜ pending |
| 16-02-02 | 02 | 1 | DASH-02 | unit | `pytest tests/unit/test_dashboard_web.py::test_signals_page -x` | ❌ W0 | ⬜ pending |
| 16-02-03 | 02 | 1 | DASH-03 | unit | `pytest tests/unit/test_dashboard_web.py::test_trade_history -x` | ❌ W0 | ⬜ pending |
| 16-02-04 | 02 | 1 | DASH-04 | unit | `pytest tests/unit/test_dashboard_web.py::test_risk_page -x` | ❌ W0 | ⬜ pending |
| 16-02-05 | 02 | 1 | DASH-05 | unit | `pytest tests/unit/test_dashboard_web.py::test_pipeline_page -x` | ❌ W0 | ⬜ pending |
| 16-02-06 | 02 | 1 | DASH-06 | unit | `pytest tests/unit/test_dashboard_web.py::test_approval_actions -x` | ❌ W0 | ⬜ pending |
| 16-03-01 | 03 | 2 | DASH-07 | unit | `pytest tests/unit/test_dashboard_sse.py -x` | ❌ W0 | ⬜ pending |
| 16-03-02 | 03 | 2 | DASH-08 | unit | `pytest tests/unit/test_dashboard_charts.py -x` | ❌ W0 | ⬜ pending |
| 16-03-03 | 03 | 2 | DASH-09 | unit | `pytest tests/unit/test_dashboard_web.py::test_mode_banner -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_dashboard_web.py` — stubs for DASH-01 through DASH-06, DASH-09
- [ ] `tests/unit/test_dashboard_sse.py` — stubs for DASH-07
- [ ] `tests/unit/test_dashboard_charts.py` — stubs for DASH-08
- [ ] `plotly>=6.0` pip install needed
- [ ] FastAPI TestClient for route testing (already available via `httpx` in dev deps)

*Wave 0 creates test infrastructure before implementation begins.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual chart rendering | DASH-04, DASH-08 | Plotly charts require browser render | Open dashboard in browser, verify gauge/pie/line charts display correctly |
| SSE real-time updates | DASH-07 | End-to-end SSE requires live connection | Trigger pipeline run, verify dashboard updates without page refresh |
| Paper/Live mode banner | DASH-09 | Visual color verification | Check green banner for paper mode, red for live mode |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
