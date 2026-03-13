---
phase: 13
slug: automated-pipeline-scheduler
status: draft
nyquist_compliant: true
wave_0_complete: true
wave_0_strategy: tdd-inline
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

## Wave 0 Strategy: TDD-Inline

All 4 test files are created by `tdd="true"` tasks as part of their RED phase (write failing tests first, then implement). This satisfies the Nyquist requirement because:

1. Each TDD task's first action is creating the test file with failing tests
2. The test file exists BEFORE the production code is written
3. The verify command runs against the test file the task itself creates
4. No task's verify command references a test file created by a different, later task

This is equivalent to a Wave 0 pre-creation -- the test stubs are the first artifact of each TDD task, not an afterthought.

| Test File | Created By | TDD Phase |
|-----------|-----------|-----------|
| `tests/unit/test_pipeline_domain.py` | 13-01 Task 1 (tdd=true) | RED: first action |
| `tests/unit/test_pipeline_repo.py` | 13-01 Task 2 (tdd=true) | RED: first action |
| `tests/unit/test_market_calendar.py` | 13-01 Task 2 (tdd=true) | RED: first action |
| `tests/unit/test_pipeline_orchestrator.py` | 13-02 Task 1 (tdd=true) | RED: first action |
| `tests/unit/test_scheduler_service.py` | 13-02 Task 2 (non-TDD, inline) | Written as step 5 of action |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_pipeline_orchestrator.py tests/unit/test_market_calendar.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | TDD Strategy | Status |
|---------|------|------|-------------|-----------|-------------------|--------------|--------|
| 13-01-01 | 01 | 1 | PIPE-02,03 | unit | `pytest tests/unit/test_pipeline_domain.py -x` | tdd=true (inline RED) | pending |
| 13-01-02 | 01 | 1 | PIPE-02,03,07 | unit | `pytest tests/unit/test_pipeline_repo.py tests/unit/test_market_calendar.py -x` | tdd=true (inline RED) | pending |
| 13-02-01 | 02 | 2 | PIPE-01,04,05,06 | unit | `pytest tests/unit/test_pipeline_orchestrator.py -x` | tdd=true (inline RED) | pending |
| 13-02-02 | 02 | 2 | PIPE-07 | unit | `pytest tests/unit/test_scheduler_service.py -x` | inline (step 5) | pending |

*Status: pending / green / red / flaky*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Slack notification delivery | PIPE-01 | Requires real Slack webhook endpoint | Configure SLACK_WEBHOOK_URL in .env, run pipeline, verify message in Slack channel |
| APScheduler persistence across restart | PIPE-07 | Requires process restart cycle | Start scheduler, stop process, restart, verify schedule resumes |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify with TDD-inline or inline test creation
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 strategy documented (TDD-inline satisfies Nyquist)
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready
