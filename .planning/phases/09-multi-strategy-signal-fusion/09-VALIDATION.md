---
phase: 9
slug: multi-strategy-signal-fusion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (installed) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/unit/test_signal_engine.py tests/unit/test_signal_consensus.py tests/unit/test_signal_canslim.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_signal_engine.py tests/unit/test_signal_consensus.py tests/unit/test_signal_canslim.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | SIGNAL-06 | unit | `pytest tests/unit/test_signal_regime_weights.py -x` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | SIGNAL-05 | unit | `pytest tests/unit/test_signal_consensus.py -x` | ✅ | ⬜ pending |
| 09-02-01 | 02 | 1 | SIGNAL-01 | unit | `pytest tests/unit/test_signal_canslim.py -x` | ✅ | ⬜ pending |
| 09-02-02 | 02 | 1 | SIGNAL-02 | unit | `pytest tests/unit/test_signal_engine.py -x` | ✅ | ⬜ pending |
| 09-02-03 | 02 | 1 | SIGNAL-03 | unit | `pytest tests/unit/test_signal_engine.py -x` | ✅ | ⬜ pending |
| 09-02-04 | 02 | 1 | SIGNAL-04 | unit | `pytest tests/unit/test_signal_engine.py -x` | ✅ | ⬜ pending |
| 09-03-01 | 03 | 2 | SIGNAL-07 | unit | `pytest tests/unit/test_signal_reasoning.py -x` | ❌ W0 | ⬜ pending |
| 09-03-02 | 03 | 2 | SIGNAL-05, SIGNAL-06 | integration | `pytest tests/unit/test_signal_engine.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_signal_regime_weights.py` — stubs for SIGNAL-06 (regime-weighted fusion)
- [ ] `tests/unit/test_signal_reasoning.py` — stubs for SIGNAL-07 (enhanced reasoning trace with regime context)
- [ ] Update `tests/unit/test_signal_engine.py` — add tests for regime-aware GenerateSignalHandler flow (SIGNAL-05 DDD path)
- [ ] Update `tests/unit/test_signal_consensus.py` — add tests for DDD SignalFusionService with regime weights (SIGNAL-05 + SIGNAL-06)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CLI `signal` output formatting | SIGNAL-07 | Rich Panel rendering requires visual inspection | Run `python -m cli.main signal AAPL` and verify regime, weights, and per-strategy breakdown display correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
