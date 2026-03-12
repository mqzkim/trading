---
phase: 2
slug: analysis-core
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=7.4 with pytest-asyncio |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/unit/test_<module>.py -x` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_<changed_module>.py -x`
- **After every plan wave:** Run `pytest tests/ -v && mypy src/ && ruff check src/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | SCOR-05 | unit | `pytest tests/unit/test_g_score.py -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 0 | SCOR-06 | unit | `pytest tests/unit/test_scoring_composite_v2.py -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 0 | VALU-01 | unit | `pytest tests/unit/test_dcf_model.py -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 0 | VALU-02 | unit | `pytest tests/unit/test_epv_model.py -x` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 0 | VALU-03 | unit | `pytest tests/unit/test_relative_multiples.py -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 0 | VALU-04 | unit | `pytest tests/unit/test_ensemble_valuation.py -x` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 0 | VALU-05 | unit | `pytest tests/unit/test_margin_of_safety.py -x` | ❌ W0 | ⬜ pending |
| 02-03-03 | 03 | 0 | ALL | unit | `pytest tests/unit/test_valuation_vos.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_g_score.py` — stubs for SCOR-05 (G-Score pure math + adapter)
- [ ] `tests/unit/test_scoring_composite_v2.py` — stubs for SCOR-06 (composite with G-Score)
- [ ] `tests/unit/test_dcf_model.py` — stubs for VALU-01 (DCF with known reference values)
- [ ] `tests/unit/test_epv_model.py` — stubs for VALU-02 (EPV with known reference values)
- [ ] `tests/unit/test_relative_multiples.py` — stubs for VALU-03 (percentile ranking)
- [ ] `tests/unit/test_ensemble_valuation.py` — stubs for VALU-04 (weighted ensemble + confidence)
- [ ] `tests/unit/test_margin_of_safety.py` — stubs for VALU-05 (MoS with sector thresholds)
- [ ] `tests/unit/test_valuation_vos.py` — stubs for all valuation domain VOs

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
