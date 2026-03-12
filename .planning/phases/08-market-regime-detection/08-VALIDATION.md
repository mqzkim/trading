---
phase: 8
slug: market-regime-detection
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4+ with pytest-asyncio |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `cd /home/mqz/workspace/trading && python -m pytest tests/unit/test_regime_handler_wiring.py tests/unit/test_regime_confirmation.py tests/unit/test_regime_event_publish.py -x` |
| **Full suite command** | `cd /home/mqz/workspace/trading && python -m pytest tests/ -x` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/unit/test_regime_handler_wiring.py tests/unit/test_regime_confirmation.py tests/unit/test_regime_event_publish.py -x`
- **After every plan wave:** Run `python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 0 | REGIME-01 | unit | `pytest tests/unit/test_regime_handler_wiring.py -x` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 0 | REGIME-02 | unit | `pytest tests/unit/test_regime_confirmation.py -x` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 0 | REGIME-03 | unit | `pytest tests/unit/test_regime_event_publish.py -x` | ❌ W0 | ⬜ pending |
| 08-01-04 | 01 | 0 | REGIME-04 | unit | `pytest tests/unit/test_regime_weight_adjustment.py -x` | ❌ W0 | ⬜ pending |
| 08-01-05 | 01 | 0 | REGIME-05 | unit | `pytest tests/unit/test_cli_regime_ddd.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_regime_handler_wiring.py` — stubs for REGIME-01 (handler data fetch + detect)
- [ ] `tests/unit/test_regime_confirmation.py` — stubs for REGIME-02 (3-day confirmation state machine)
- [ ] `tests/unit/test_regime_event_publish.py` — stubs for REGIME-03 (EventBus publish on confirmed transition)
- [ ] `tests/unit/test_regime_weight_adjustment.py` — stubs for REGIME-04 (concrete RegimeWeightAdjuster)
- [ ] `tests/unit/test_cli_regime_ddd.py` — stubs for REGIME-05 (CLI rewiring + history flag)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CLI regime output formatting | REGIME-05 | Visual formatting check | Run `python -m cli.main regime` and verify Rich table output |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
