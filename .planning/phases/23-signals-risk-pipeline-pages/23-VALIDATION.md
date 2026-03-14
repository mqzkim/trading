---
phase: 23
slug: signals-risk-pipeline-pages
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Biome 2.4.7 (lint + format) + TypeScript tsc (type check) |
| **Config file** | `dashboard/biome.json` + `dashboard/tsconfig.json` |
| **Quick run command** | `cd /home/mqz/workspace/trading/dashboard && npx tsc --noEmit && npx biome check .` |
| **Full suite command** | `cd /home/mqz/workspace/trading/dashboard && npm run build` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd /home/mqz/workspace/trading/dashboard && npx tsc --noEmit && npx biome check .`
- **After every plan wave:** Run `cd /home/mqz/workspace/trading/dashboard && npm run build`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 23-01-01 | 01 | 1 | SGNL-01 | smoke | `npx tsc --noEmit` | ❌ W0 | ⬜ pending |
| 23-01-02 | 01 | 1 | SGNL-02 | smoke | `npx tsc --noEmit` | ❌ W0 | ⬜ pending |
| 23-01-03 | 01 | 1 | SGNL-03 | manual | `npm run build` | ❌ W0 | ⬜ pending |
| 23-02-01 | 02 | 1 | RISK-01 | manual | `npx tsc --noEmit` | ❌ W0 | ⬜ pending |
| 23-02-02 | 02 | 1 | RISK-02 | manual | `npx tsc --noEmit` | ❌ W0 | ⬜ pending |
| 23-02-03 | 02 | 1 | RISK-03 | smoke | `npx tsc --noEmit` | ❌ W0 | ⬜ pending |
| 23-02-04 | 02 | 1 | RISK-04 | smoke | `npx tsc --noEmit` | ❌ W0 | ⬜ pending |
| 23-03-01 | 03 | 2 | PIPE-01 | manual | `npm run build` | ❌ W0 | ⬜ pending |
| 23-03-02 | 03 | 2 | PIPE-02 | smoke | `npx tsc --noEmit` | ❌ W0 | ⬜ pending |
| 23-03-03 | 03 | 2 | PIPE-03 | manual | `npm run build` | ❌ W0 | ⬜ pending |
| 23-03-04 | 03 | 2 | PIPE-04 | manual | `npm run build` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `@tanstack/react-table` — install: `npm install @tanstack/react-table`
- [ ] shadcn/ui form components — install: `npx shadcn@latest add progress input label checkbox select`
- [ ] `dashboard/src/types/api.ts` — extend with SignalsData, RiskData, PipelineData types
- [ ] `dashboard/src/hooks/use-signals.ts` — TanStack Query hook for signals
- [ ] `dashboard/src/hooks/use-risk.ts` — TanStack Query hook for risk
- [ ] `dashboard/src/hooks/use-pipeline.ts` — TanStack Query hook + mutations for pipeline
- [ ] `npm run build` passing with all new dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Drawdown gauge 3-tier coloring | RISK-01 | CSS visual rendering | Verify green (<=10%), yellow (<=15%), red (>15%) colors in browser |
| Sector donut chart proportions | RISK-02 | CSS conic-gradient visual | Verify sector proportions match data in browser |
| Column sort toggle UX | SGNL-03 | Interactive behavior | Click column headers, verify sort toggles asc/desc |
| Pipeline run form submission | PIPE-01 | POST mutation flow | Submit form, verify pipeline starts |
| Approval create/suspend/resume | PIPE-03 | Multi-step CRUD flow | Create approval, suspend, resume in sequence |
| Review approve/reject buttons | PIPE-04 | POST mutation + cache invalidation | Approve/reject review, verify queue updates |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
