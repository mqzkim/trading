---
phase: 22
slug: design-system-overview-page
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 22 — Validation Strategy

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
| 22-01-01 | 01 | 1 | DSGN-01 | manual | `npm run build` (validates CSS processing) | -- Wave 0 | ⬜ pending |
| 22-01-02 | 01 | 1 | DSGN-02 | manual | `npx tsc --noEmit` (validates font variable usage) | -- Wave 0 | ⬜ pending |
| 22-01-03 | 01 | 1 | DSGN-03 | manual | `npm run build` (validates CSS variable references) | -- Wave 0 | ⬜ pending |
| 22-01-04 | 01 | 1 | DSGN-04 | manual | `npm run build` (validates component imports) | -- Wave 0 | ⬜ pending |
| 22-02-01 | 02 | 2 | OVER-01 | smoke | `npx tsc --noEmit` (type-checks component props) | -- Wave 0 | ⬜ pending |
| 22-02-02 | 02 | 2 | OVER-02 | smoke | `npx tsc --noEmit` | -- Wave 0 | ⬜ pending |
| 22-02-03 | 02 | 2 | OVER-03 | manual | `npm run build` (validates lightweight-charts import) | -- Wave 0 | ⬜ pending |
| 22-02-04 | 02 | 2 | OVER-04 | smoke | `npx tsc --noEmit` | -- Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `dashboard/src/types/api.ts` — TypeScript types matching FastAPI OverviewQueryHandler response shape
- [ ] `dashboard/src/lib/formatters.ts` — Currency/percentage/score formatting utilities
- [ ] shadcn/ui initialized (`components.json` exists)
- [ ] `npm run build` passing with all new components and dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Bloomberg dark theme renders correctly | DSGN-01 | Visual appearance cannot be tested programmatically | Open Overview page, verify black background, amber/cyan/red semantic colors |
| Monospace numbers align in tables | DSGN-02 | Font rendering is visual | Open Holdings table, verify numeric columns align vertically |
| Semantic colors (cyan=profit, red=loss) | DSGN-03 | Color correctness is visual | Check P&L values show cyan for positive, red for negative |
| Equity curve with regime coloring | OVER-03 | Chart rendering is visual | Open Overview page, verify equity curve + regime background bands |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
