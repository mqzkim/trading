---
phase: 29
slug: performance-self-improvement
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-03-18
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/unit/test_performance_trade_repo.py tests/unit/test_brinson_fachler.py tests/unit/test_ic_calculation.py tests/unit/test_kelly_efficiency.py tests/unit/test_position_score_snapshot.py tests/unit/test_self_improver_proposal.py tests/unit/test_proposal_approval.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command above
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 29-01-01 | 01 | 0 | PERF-01 | unit | `pytest tests/unit/test_performance_trade_repo.py -x` | ✅ | ✅ green |
| 29-01-02 | 01 | 0 | PERF-02 | unit | `pytest tests/unit/test_brinson_fachler.py -x` | ✅ | ✅ green |
| 29-01-03 | 01 | 0 | PERF-03 | unit | `pytest tests/unit/test_ic_calculation.py -x` | ✅ | ✅ green |
| 29-01-04 | 01 | 0 | PERF-04 | unit | `pytest tests/unit/test_kelly_efficiency.py -x` | ✅ | ✅ green |
| 29-01-05 | 01 | 0 | PERF-05 | unit | `pytest tests/unit/test_position_score_snapshot.py -x` | ✅ | ✅ green |
| 29-02-01 | 02 | 0 | SELF-01 | unit | `pytest tests/unit/test_self_improver_proposal.py -x` | ❌ W0 | ⬜ pending |
| 29-02-02 | 02 | 0 | SELF-02 | unit | `pytest tests/unit/test_proposal_approval.py -x` | ❌ W0 | ⬜ pending |
| 29-02-03 | 02 | 0 | SELF-03 | unit | `pytest tests/unit/test_self_improver_proposal.py::test_walk_forward_required -x` | ❌ W0 | ⬜ pending |
| 29-02-04 | 02 | 0 | SELF-04 | unit | `pytest tests/unit/test_self_improver_proposal.py::test_threshold_50 -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/test_performance_trade_repo.py` — stubs for PERF-01
- [x] `tests/unit/test_brinson_fachler.py` — stubs for PERF-02
- [x] `tests/unit/test_ic_calculation.py` — stubs for PERF-03
- [x] `tests/unit/test_kelly_efficiency.py` — stubs for PERF-04
- [x] `tests/unit/test_position_score_snapshot.py` — stubs for PERF-05
- [ ] `tests/unit/test_self_improver_proposal.py` — stubs for SELF-01, SELF-03, SELF-04
- [ ] `tests/unit/test_proposal_approval.py` — stubs for SELF-02

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard Parameter Proposals section shows/hides based on trade count | SELF-02 | Browser UI interaction | Open Performance page, verify section hidden when < 50 trades |
| Approve button updates proposal status and reflects in history | SELF-02 | Browser UI interaction | Click Approve, verify approval history row appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
