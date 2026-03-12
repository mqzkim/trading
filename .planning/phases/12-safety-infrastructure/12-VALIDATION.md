---
phase: 12
slug: safety-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4+ |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/unit/test_safe_execution.py tests/unit/test_cooldown_persistence.py tests/unit/test_reconciliation.py tests/unit/test_kill_switch.py tests/unit/test_order_polling.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_safe_execution.py tests/unit/test_cooldown_persistence.py tests/unit/test_reconciliation.py tests/unit/test_kill_switch.py tests/unit/test_order_polling.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | SAFE-01 | unit | `pytest tests/unit/test_safe_execution.py::test_default_paper_mode -x` | ❌ W0 | ⬜ pending |
| 12-01-02 | 01 | 1 | SAFE-01 | unit | `pytest tests/unit/test_safe_execution.py::test_credentials_alone_not_live -x` | ❌ W0 | ⬜ pending |
| 12-01-03 | 01 | 1 | SAFE-02 | unit | `pytest tests/unit/test_safe_execution.py::test_live_no_mock_fallback -x` | ❌ W0 | ⬜ pending |
| 12-01-04 | 01 | 1 | SAFE-02 | unit | `pytest tests/unit/test_alpaca_adapter.py::test_real_bracket_order_error -x` | ❌ W0 | ⬜ pending |
| 12-01-05 | 01 | 1 | SAFE-03 | unit | `pytest tests/unit/test_safe_execution.py::test_separate_key_pairs -x` | ❌ W0 | ⬜ pending |
| 12-02-01 | 02 | 1 | SAFE-04 | unit | `pytest tests/unit/test_reconciliation.py -x` | ❌ W0 | ⬜ pending |
| 12-02-02 | 02 | 1 | SAFE-04 | unit | `pytest tests/unit/test_reconciliation.py::test_halt_on_mismatch -x` | ❌ W0 | ⬜ pending |
| 12-03-01 | 03 | 1 | SAFE-05 | unit | `pytest tests/unit/test_cooldown_persistence.py -x` | ❌ W0 | ⬜ pending |
| 12-03-02 | 03 | 1 | SAFE-05 | unit | `pytest tests/unit/test_cooldown_persistence.py::test_survives_restart -x` | ❌ W0 | ⬜ pending |
| 12-03-03 | 03 | 1 | SAFE-05 | unit | `pytest tests/unit/test_cooldown_persistence.py::test_expiry_30_days -x` | ❌ W0 | ⬜ pending |
| 12-03-04 | 03 | 1 | SAFE-05 | unit | `pytest tests/unit/test_cooldown_persistence.py::test_force_override -x` | ❌ W0 | ⬜ pending |
| 12-04-01 | 04 | 2 | SAFE-06 | unit | `pytest tests/unit/test_kill_switch.py::test_cancel_all_orders -x` | ❌ W0 | ⬜ pending |
| 12-04-02 | 04 | 2 | SAFE-06 | unit | `pytest tests/unit/test_kill_switch.py::test_liquidate -x` | ❌ W0 | ⬜ pending |
| 12-04-03 | 04 | 2 | SAFE-06 | unit | `pytest tests/unit/test_kill_switch.py::test_kill_triggers_cooldown -x` | ❌ W0 | ⬜ pending |
| 12-05-01 | 05 | 2 | SAFE-07 | unit | `pytest tests/unit/test_order_polling.py -x` | ❌ W0 | ⬜ pending |
| 12-05-02 | 05 | 2 | SAFE-07 | unit | `pytest tests/unit/test_order_polling.py::test_timeout -x` | ❌ W0 | ⬜ pending |
| 12-05-03 | 05 | 2 | SAFE-08 | unit | `pytest tests/unit/test_order_polling.py::test_bracket_legs_verified -x` | ❌ W0 | ⬜ pending |
| 12-05-04 | 05 | 2 | SAFE-08 | unit | `pytest tests/unit/test_order_polling.py::test_bracket_legs_missing -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_safe_execution.py` — stubs for SAFE-01, SAFE-02, SAFE-03
- [ ] `tests/unit/test_reconciliation.py` — stubs for SAFE-04
- [ ] `tests/unit/test_cooldown_persistence.py` — stubs for SAFE-05
- [ ] `tests/unit/test_kill_switch.py` — stubs for SAFE-06
- [ ] `tests/unit/test_order_polling.py` — stubs for SAFE-07, SAFE-08

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live mode startup confirmation prompt | SAFE-01 | Interactive terminal input | 1. Set EXECUTION_MODE=live 2. Run pipeline 3. Verify "Are you sure?" prompt appears |
| Kill switch --liquidate confirmation | SAFE-06 | Interactive terminal input | 1. Run `trade kill --liquidate` 2. Verify confirmation prompt 3. Type "no" to abort |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
