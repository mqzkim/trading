---
phase: 15
slug: live-trading-activation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | pyproject.toml |
| **Quick run command** | `python3 -m pytest tests/unit/ -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/unit/ -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | LIVE-01 | unit | `python3 -m pytest tests/unit/test_live_activation.py::test_live_mode_bootstrap -x` | ❌ W0 | ⬜ pending |
| 15-01-02 | 01 | 1 | LIVE-02 | unit | `python3 -m pytest tests/unit/test_circuit_breaker.py -x` | ❌ W0 | ⬜ pending |
| 15-01-03 | 01 | 1 | LIVE-06 | unit | `python3 -m pytest tests/unit/test_circuit_breaker.py::test_trip_after_3_failures -x` | ❌ W0 | ⬜ pending |
| 15-02-01 | 02 | 1 | LIVE-03 | unit | `python3 -m pytest tests/unit/test_order_monitor.py -x` | ❌ W0 | ⬜ pending |
| 15-02-02 | 02 | 1 | LIVE-04 | unit | `python3 -m pytest tests/unit/test_trading_stream.py -x` | ❌ W0 | ⬜ pending |
| 15-02-03 | 02 | 1 | LIVE-05 | unit | `python3 -m pytest tests/unit/test_capital_ratio.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_circuit_breaker.py` — covers LIVE-02, LIVE-06
- [ ] `tests/unit/test_order_monitor.py` — covers LIVE-03
- [ ] `tests/unit/test_trading_stream.py` — covers LIVE-04
- [ ] `tests/unit/test_capital_ratio.py` — covers LIVE-05
- [ ] `tests/unit/test_live_activation.py` — covers LIVE-01

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Alpaca connection with real credentials | LIVE-01 | Requires real API keys and live account | Set EXECUTION_MODE=live with valid ALPACA_LIVE_KEY/SECRET, verify connection log |
| WebSocket reconnection under network failure | LIVE-04 | Network conditions hard to simulate | Kill network during pipeline run, verify stream reconnects |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
