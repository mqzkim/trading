---
phase: 20
slug: ci-test-debt-cleanup
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + mypy 1.x + ruff |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `mypy src/ --explicit-package-bases && pytest tests/unit/test_api_routes.py -x` |
| **Full suite command** | `mypy src/ --explicit-package-bases && ruff check src/ && pytest tests/ -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `mypy src/ --explicit-package-bases && pytest tests/unit/test_api_routes.py -x`
- **After every plan wave:** Run `mypy src/ --explicit-package-bases && ruff check src/ && pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | mypy zero errors | typecheck | `mypy src/ --explicit-package-bases` | N/A | ⬜ pending |
| 20-02-01 | 02 | 1 | api_routes tests pass | unit | `pytest tests/unit/test_api_routes.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

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
