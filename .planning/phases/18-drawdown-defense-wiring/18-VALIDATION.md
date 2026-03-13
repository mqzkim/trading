---
phase: 18
slug: drawdown-defense-wiring
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `python3 -m pytest tests/integration/test_drawdown_defense.py -x -v` |
| **Full suite command** | `python3 -m pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/integration/test_drawdown_defense.py tests/unit/test_pipeline_orchestrator.py tests/unit/test_approval_integration.py -x -v`
- **After every plan wave:** Run `python3 -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | APPR-05 | integration | `python3 -m pytest tests/integration/test_drawdown_defense.py::test_drawdown_event_suspends_approval -x` | ❌ W0 | ⬜ pending |
| 18-01-02 | 01 | 1 | APPR-05 | integration | `python3 -m pytest tests/integration/test_drawdown_defense.py::test_caution_level_does_not_suspend -x` | ❌ W0 | ⬜ pending |
| 18-01-03 | 01 | 1 | PIPE-06 | integration | `python3 -m pytest tests/integration/test_drawdown_defense.py::test_pipeline_halts_on_drawdown_warning -x` | ❌ W0 | ⬜ pending |
| 18-01-04 | 01 | 1 | PIPE-06 | unit | `python3 -m pytest tests/unit/test_pipeline_orchestrator.py::test_halt_on_warning_drawdown -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/integration/test_drawdown_defense.py` — cross-phase integration tests for APPR-05, PIPE-06
- Existing `pytest` infrastructure and fixtures sufficient — no new config needed

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
