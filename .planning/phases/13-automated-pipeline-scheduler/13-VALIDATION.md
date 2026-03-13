---
phase: 13
slug: automated-pipeline-scheduler
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4+ with pytest-asyncio |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/unit/test_pipeline_orchestrator.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_pipeline_orchestrator.py tests/unit/test_market_calendar.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | PIPE-01 | unit | `pytest tests/unit/test_pipeline_orchestrator.py::test_full_pipeline_run -x` | ❌ W0 | ⬜ pending |
| 13-01-02 | 01 | 1 | PIPE-02 | unit | `pytest tests/unit/test_market_calendar.py -x` | ❌ W0 | ⬜ pending |
| 13-01-03 | 01 | 1 | PIPE-03 | unit | `pytest tests/unit/test_pipeline_repo.py -x` | ❌ W0 | ⬜ pending |
| 13-01-04 | 01 | 1 | PIPE-04 | unit | `pytest tests/unit/test_pipeline_orchestrator.py::test_dry_run_skips_execution -x` | ❌ W0 | ⬜ pending |
| 13-01-05 | 01 | 1 | PIPE-05 | unit | `pytest tests/unit/test_pipeline_orchestrator.py::test_retry_exponential_backoff -x` | ❌ W0 | ⬜ pending |
| 13-01-06 | 01 | 1 | PIPE-06 | unit | `pytest tests/unit/test_pipeline_orchestrator.py::test_halt_on_crisis -x` | ❌ W0 | ⬜ pending |
| 13-01-07 | 01 | 1 | PIPE-07 | unit | `pytest tests/unit/test_scheduler_service.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_pipeline_orchestrator.py` — stubs for PIPE-01, PIPE-04, PIPE-05, PIPE-06
- [ ] `tests/unit/test_market_calendar.py` — stubs for PIPE-02
- [ ] `tests/unit/test_pipeline_repo.py` — stubs for PIPE-03
- [ ] `tests/unit/test_scheduler_service.py` — stubs for PIPE-07
- [ ] Framework install: `pip install "APScheduler>=3.11,<4" "exchange-calendars>=4.13"` — if not detected

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Slack notification delivery | PIPE-01 | Requires real Slack webhook endpoint | Configure SLACK_WEBHOOK_URL in .env, run pipeline, verify message in Slack channel |
| APScheduler persistence across restart | PIPE-07 | Requires process restart cycle | Start scheduler, stop process, restart, verify schedule resumes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
