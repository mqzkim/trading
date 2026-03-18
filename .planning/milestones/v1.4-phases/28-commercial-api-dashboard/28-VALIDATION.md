---
phase: 28
slug: commercial-api-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Python API + dashboard backend tests) |
| **Config file** | pyproject.toml (pytest section) |
| **Quick run command** | `pytest tests/unit/test_api_v1_quantscore.py tests/unit/test_api_v1_regime.py tests/unit/test_api_v1_signals.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_api_v1_quantscore.py tests/unit/test_api_v1_regime.py tests/unit/test_api_v1_signals.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 28-01-01 | 01 | 0 | API-01 | unit | `pytest tests/unit/test_api_v1_quantscore.py -x` | ✅ Extend | ⬜ pending |
| 28-01-02 | 01 | 0 | API-02 | unit | `pytest tests/unit/test_api_v1_regime.py -x` | ✅ Extend | ⬜ pending |
| 28-01-03 | 01 | 0 | API-03 | unit | `pytest tests/unit/test_api_v1_signals.py -x` | ✅ Extend | ⬜ pending |
| 28-01-04 | 01 | 0 | DASH-01 | unit | `pytest tests/unit/test_dashboard_json_api.py -x` | ✅ Extend | ⬜ pending |
| 28-01-05 | 01 | 0 | DASH-04 | unit | `pytest tests/unit/test_dashboard_json_api.py -x` | ✅ Extend | ⬜ pending |
| 28-02-01 | 02 | 1 | API-01 | unit | `pytest tests/unit/test_api_v1_quantscore.py -x` | ✅ W0 | ⬜ pending |
| 28-02-02 | 02 | 1 | API-02 | unit | `pytest tests/unit/test_api_v1_regime.py -x` | ✅ W0 | ⬜ pending |
| 28-02-03 | 02 | 1 | API-03 | unit | `pytest tests/unit/test_api_v1_signals.py -x` | ✅ W0 | ⬜ pending |
| 28-02-04 | 02 | 1 | DASH-04 | unit | `pytest tests/unit/test_dashboard_json_api.py -x` | ✅ W0 | ⬜ pending |
| 28-03-01 | 03 | 2 | DASH-01 | unit | `pytest tests/unit/test_dashboard_json_api.py -x` | ✅ W0 | ⬜ pending |
| 28-03-02 | 03 | 2 | DASH-02 | manual-only | Dashboard UI inspection (Performance page) | N/A | ⬜ pending |
| 28-03-03 | 03 | 2 | DASH-03 | manual | Start servers, verify real data displayed | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_api_v1_quantscore.py` — extend with `sentiment_sub_scores`, `sentiment_confidence`, typed `technical_sub_scores` assertions
- [ ] `tests/unit/test_api_v1_regime.py` — extend with `regime_probabilities` dict (all 4 regimes, values sum to ~1.0)
- [ ] `tests/unit/test_api_v1_signals.py` — extend with `methodology_votes` as reasoning trace verification
- [ ] `tests/unit/test_dashboard_json_api.py` — extend for `regime_probabilities` in risk handler response, and sub-score breakdown in signals handler response

*Existing test infrastructure covers all phase requirements. No new test files needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Performance Attribution page renders correctly | DASH-02 | React page, no unit test coverage | Navigate to /performance in dashboard; verify KPI cards, empty-state message, equity curve placeholder visible |
| Real data displayed across all pages | DASH-03 | E2E depends on pipeline run producing stored scores | Run pipeline, then verify signals/risk pages show F/T/S breakdowns from real data |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
