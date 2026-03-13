---
phase: 17
slug: sse-realtime-event-wiring
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/unit/test_sse_event_wiring.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_sse_event_wiring.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | DASH-07a | unit | `pytest tests/unit/test_sse_event_wiring.py::test_event_names_match -x` | ❌ W0 | ⬜ pending |
| 17-01-02 | 01 | 1 | DASH-07b | unit | `pytest tests/unit/test_sse_event_wiring.py::test_pipeline_completed_event_published -x` | ❌ W0 | ⬜ pending |
| 17-01-03 | 01 | 1 | DASH-07c | unit | `pytest tests/unit/test_sse_event_wiring.py::test_drawdown_event_published -x` | ❌ W0 | ⬜ pending |
| 17-01-04 | 01 | 1 | DASH-07d | unit | `pytest tests/unit/test_sse_event_wiring.py::test_monitor_persistent_loop -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_sse_event_wiring.py` — stubs for DASH-07 (all 4 sub-behaviors)

*Existing test infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SSE updates visible in browser | DASH-07 | Requires running dashboard + browser | Start dashboard, trigger pipeline, observe live updates |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
