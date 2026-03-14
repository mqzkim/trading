---
phase: 25
slug: cleanup
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/unit/test_dashboard_json_api.py tests/unit/test_dashboard_sse.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_dashboard_json_api.py tests/unit/test_dashboard_sse.py -x`
- **After every plan wave:** Run `pytest tests/ -x && mypy src/ && ruff check src/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 25-01-01 | 01 | 1 | CLNP-01 | smoke | `python3 -c "from pathlib import Path; assert not Path('src/dashboard/presentation/templates').exists()"` | N/A | ⬜ pending |
| 25-01-02 | 01 | 1 | CLNP-01 | smoke | `python3 -c "import inspect; from src.dashboard.presentation.app import create_dashboard_app; assert 'routes' not in inspect.getsource(create_dashboard_app)"` | N/A | ⬜ pending |
| 25-01-03 | 01 | 1 | CLNP-02 | smoke | `python3 -c "t=open('pyproject.toml').read(); assert 'plotly' not in t"` | N/A | ⬜ pending |
| 25-01-04 | 01 | 1 | CLNP-02 | smoke | `! grep -r 'import plotly' src/` | N/A | ⬜ pending |
| 25-01-05 | 01 | 1 | CLNP-01+02 | unit | `pytest tests/unit/test_dashboard_json_api.py -x` | ✅ | ⬜ pending |
| 25-01-06 | 01 | 1 | CLNP-01+02 | unit | `pytest tests/unit/test_dashboard_sse.py -x` | ✅ | ⬜ pending |
| 25-01-07 | 01 | 1 | CLNP-01+02 | static | `mypy src/ && ruff check src/` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Tests being deleted (test_dashboard_web.py, test_dashboard_charts.py) test the code being removed. Remaining tests (test_dashboard_json_api.py, test_dashboard_sse.py) validate the surviving code paths.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
