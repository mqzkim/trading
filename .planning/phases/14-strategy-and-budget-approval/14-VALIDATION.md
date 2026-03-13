---
phase: 14
slug: strategy-and-budget-approval
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/unit/test_approval*.py tests/unit/test_budget*.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_approval*.py tests/unit/test_budget*.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 0 | APPR-01 | unit | `pytest tests/unit/test_approval_domain.py -x` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 0 | APPR-03 | unit | `pytest tests/unit/test_approval_gate.py -x` | ❌ W0 | ⬜ pending |
| 14-01-03 | 01 | 0 | APPR-02 | unit | `pytest tests/unit/test_budget_tracking.py -x` | ❌ W0 | ⬜ pending |
| 14-01-04 | 01 | 0 | APPR-04,05 | unit | `pytest tests/unit/test_approval_suspension.py -x` | ❌ W0 | ⬜ pending |
| 14-01-05 | 01 | 0 | Integration | integration | `pytest tests/integration/test_pipeline_approval.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_approval_domain.py` — stubs for APPR-01 (entity creation, validation, expiry)
- [ ] `tests/unit/test_approval_gate.py` — stubs for APPR-03 (gate check logic)
- [ ] `tests/unit/test_budget_tracking.py` — stubs for APPR-02 (daily budget)
- [ ] `tests/unit/test_approval_suspension.py` — stubs for APPR-04, APPR-05 (suspension logic)
- [ ] `tests/integration/test_pipeline_approval.py` — stubs for approval gate in pipeline flow

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CLI approval UX flow | APPR-01 | User experience validation | Run `trading approve create ...` and verify output formatting |
| CLI budget status display | APPR-02 | Visual output check | Run `trading budget status` and verify spent/remaining display |
| CLI review queue UX | APPR-03 | User experience validation | Run `trading review list` and verify queued trades display |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
