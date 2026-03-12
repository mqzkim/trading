---
phase: 7
slug: technical-scoring-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=7.4 |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/unit/test_technical_scoring_service.py tests/unit/test_scoring_composite_v2.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_technical_scoring_service.py tests/unit/test_scoring_composite_v2.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | TECH-01 | unit | `pytest tests/unit/test_technical_scoring_service.py -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | TECH-02 | unit | `pytest tests/unit/test_technical_scoring_service.py::test_composite_range -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 2 | TECH-03 | unit | `pytest tests/unit/test_scoring_composite_v2.py -x` | ✅ (needs update) | ⬜ pending |
| 07-02-02 | 02 | 2 | TECH-04 | unit | `pytest tests/unit/test_cli_score_technical.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_technical_scoring_service.py` — stubs for TECH-01, TECH-02 (TechnicalScoringService)
- [ ] `tests/unit/test_cli_score_technical.py` — stubs for TECH-04 (CLI sub-score output)
- [ ] Update `tests/unit/test_scoring_composite_v2.py` — covers TECH-03 (weight change 40/40/20)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CLI output formatting readable | TECH-04 | Visual layout check | Run `python -m cli.main score AAPL` and verify sub-scores are human-readable |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
