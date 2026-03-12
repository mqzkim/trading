---
phase: 10
slug: korean-broker-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python3 -m pytest tests/unit/test_kis_adapter.py tests/unit/test_broker_abstraction.py -x -v` |
| **Full suite command** | `python3 -m pytest tests/ -x --ignore=tests/unit/test_api_routes.py` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | KR-01 | unit | `pytest tests/unit/test_broker_abstraction.py -x -v` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | KR-01 | unit | `pytest tests/unit/test_kis_adapter.py -x -v` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 2 | KR-02, KR-03 | unit | `pytest tests/unit/test_krw_sizing.py -x -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_broker_abstraction.py` — stubs for KR-01 (IBrokerAdapter interface)
- [ ] `tests/unit/test_kis_adapter.py` — stubs for KR-01, KR-02 (KIS mock adapter)
- [ ] `tests/unit/test_krw_sizing.py` — stubs for KR-03 (KRW position sizing, tick size)

*Existing pytest infrastructure covers all framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| KIS real API connection | KR-01 | No KIS credentials yet | After developer registration: set .env, run `python3 -m pytest tests/integration/test_kis_live.py` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
