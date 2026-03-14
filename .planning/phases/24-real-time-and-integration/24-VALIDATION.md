---
phase: 24
slug: real-time-and-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Python backend) + TypeScript type checking (frontend) |
| **Config file** | `pyproject.toml` (pytest), `tsconfig.json` (TS), `biome.json` (lint) |
| **Quick run command** | `cd dashboard && npx tsc --noEmit && npx biome check .` |
| **Full suite command** | `cd /home/mqz/workspace/trading && pytest tests/ -x && cd dashboard && npx tsc --noEmit` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd dashboard && npx tsc --noEmit && npx biome check .`
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 24-01-01 | 01 | 1 | RT-01 | typecheck | `cd dashboard && npx tsc --noEmit` | ✅ | ⬜ pending |
| 24-01-02 | 01 | 1 | RT-01 | lint | `cd dashboard && npx biome check .` | ✅ | ⬜ pending |
| 24-01-03 | 01 | 1 | RT-01 | manual | Browser DevTools SSE verification | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

- TypeScript type checking via `tsconfig.json` (already configured)
- Biome linting via `biome.json` (already configured)
- Backend SSE tests already exist (`test_dashboard_sse.py`, `test_sse_event_wiring.py`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| OrderFilledEvent triggers overview refresh | RT-01 | Browser-native EventSource API requires DOM | 1. Start FastAPI + Next.js dev servers 2. Open browser DevTools Network tab 3. Trigger OrderFilledEvent from backend 4. Verify overview query refetches |
| DrawdownAlertEvent triggers risk + overview refresh | RT-01 | Browser-native EventSource API requires DOM | Same as above with DrawdownAlertEvent |
| RegimeChangedEvent triggers multi-page refresh | RT-01 | Browser-native EventSource API requires DOM | Same as above with RegimeChangedEvent |
| PipelineCompletedEvent triggers pipeline + overview refresh | RT-01 | Browser-native EventSource API requires DOM | Same as above with PipelineCompletedEvent |
| SSE auto-reconnection after disconnect | RT-01 | Requires network interruption simulation | 1. Connect to SSE 2. Stop FastAPI server 3. Restart server 4. Verify reconnection in Network tab |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
