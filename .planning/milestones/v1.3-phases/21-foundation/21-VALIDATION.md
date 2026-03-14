---
phase: 21
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4+ (Python backend), Next.js build (frontend) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/unit/test_dashboard_json_api.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_dashboard_json_api.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green + manual `npm run dev` check
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | SETUP-01 | manual | `cd dashboard && npm run build` | -- Wave 0 | ⬜ pending |
| 21-01-02 | 01 | 1 | SETUP-02 | integration | `pytest tests/unit/test_dashboard_json_api.py -x -q` | -- Wave 0 | ⬜ pending |
| 21-02-01 | 02 | 1 | SETUP-03 | unit | `pytest tests/unit/test_dashboard_json_api.py -x -q` | -- Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_dashboard_json_api.py` — stubs for SETUP-03 (JSON API returns correct data for all 4 GET + 5 POST endpoints)
- [ ] Manual: `npm run dev` boots Next.js at localhost:3000 — covers SETUP-01
- [ ] Manual: fetch `/api/v1/dashboard/overview` from Next.js returns FastAPI JSON — covers SETUP-02
- [ ] `dashboard/` directory with valid `package.json` and `next.config.ts` — covers SETUP-01

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Next.js dev server starts at localhost:3000 | SETUP-01 | Requires running process | `cd dashboard && npm run dev`, verify http://localhost:3000 |
| Proxy round-trip returns FastAPI JSON | SETUP-02 | Requires both servers running | Start FastAPI + Next.js, fetch `/api/v1/dashboard/overview` from Next.js |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
