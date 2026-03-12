---
phase: 11
slug: commercial-fastapi-rest-api
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4+ (already configured) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/unit/test_api_v1*.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_api_v1*.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | API-01 | unit | `pytest tests/unit/test_api_v1_quantscore.py -x` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | API-02 | unit | `pytest tests/unit/test_api_v1_regime.py -x` | ❌ W0 | ⬜ pending |
| 11-01-03 | 01 | 1 | API-03 | unit | `pytest tests/unit/test_api_v1_signals.py -x` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | API-04 | unit | `pytest tests/unit/test_api_v1_auth.py -x` | ❌ W0 | ⬜ pending |
| 11-02-02 | 02 | 1 | API-05 | unit | `pytest tests/unit/test_api_v1_rate_limit.py -x` | ❌ W0 | ⬜ pending |
| 11-02-03 | 02 | 1 | API-06 | unit | `pytest tests/unit/test_api_v1_apikeys.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_api_v1_quantscore.py` — stubs for API-01
- [ ] `tests/unit/test_api_v1_regime.py` — stubs for API-02
- [ ] `tests/unit/test_api_v1_signals.py` — stubs for API-03
- [ ] `tests/unit/test_api_v1_auth.py` — stubs for API-04
- [ ] `tests/unit/test_api_v1_rate_limit.py` — stubs for API-05
- [ ] `tests/unit/test_api_v1_apikeys.py` — stubs for API-06
- [ ] `tests/unit/conftest_api.py` — shared fixtures (TestClient, mock bootstrap, mock JWT)
- [ ] Install: `pip install PyJWT slowapi "passlib[bcrypt]"` — new dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rate limit headers visible in response | API-05 | Requires real HTTP timing | `curl -v` and check X-RateLimit headers |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
