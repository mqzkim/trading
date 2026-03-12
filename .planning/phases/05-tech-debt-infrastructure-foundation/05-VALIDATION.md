---
phase: 5
slug: tech-debt-infrastructure-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/unit/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | INFRA-01 | unit | `pytest tests/unit/test_sync_event_bus.py -x` | Wave 0 | ⬜ pending |
| 05-01-02 | 01 | 1 | INFRA-01 | integration | `pytest tests/integration/test_event_wiring.py -x` | Wave 0 | ⬜ pending |
| 05-01-03 | 01 | 1 | INFRA-02 | unit | `pytest tests/unit/test_bootstrap.py -x` | Wave 0 | ⬜ pending |
| 05-02-01 | 02 | 1 | INFRA-03 | unit | `pytest tests/unit/test_db_factory.py -x` | Wave 0 | ⬜ pending |
| 05-02-02 | 02 | 1 | INFRA-04 | integration | `pytest tests/integration/test_screener_integration.py -x` | Wave 0 | ⬜ pending |
| 05-03-01 | 03 | 2 | INFRA-05 | unit (mocked) | `pytest tests/unit/test_cli_ingest.py -x` | Wave 0 | ⬜ pending |
| 05-03-02 | 03 | 2 | INFRA-05 | unit (mocked) | `pytest tests/unit/test_cli_generate_plan.py -x` | Wave 0 | ⬜ pending |
| 05-03-03 | 03 | 2 | INFRA-05 | unit (mocked) | `pytest tests/unit/test_cli_backtest.py -x` | Wave 0 | ⬜ pending |
| 05-01-04 | 01 | 1 | INFRA-06 | unit | `pytest tests/unit/test_scoring_composite_v2.py -x` | Partial | ⬜ pending |
| 05-01-05 | 01 | 1 | INFRA-07 | unit | `pytest tests/unit/test_score_handler_events.py -x` | Wave 0 | ⬜ pending |
| 05-01-06 | 01 | 1 | INFRA-08 | unit (import check) | `pytest tests/unit/test_ddd_boundaries.py -x` | Wave 0 | ⬜ pending |
| 05-01-07 | 01 | 1 | INFRA-09 | smoke | `mypy src/scoring src/signals src/execution src/shared --no-error-summary` | Existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_sync_event_bus.py` — stubs for INFRA-01 (SyncEventBus behavior)
- [ ] `tests/integration/test_event_wiring.py` — stubs for INFRA-01 (4 contexts wired)
- [ ] `tests/unit/test_bootstrap.py` — stubs for INFRA-02 (Composition Root returns handlers)
- [ ] `tests/unit/test_db_factory.py` — stubs for INFRA-03 (factory paths and connections)
- [ ] `tests/integration/test_screener_integration.py` — stubs for INFRA-04 (screener with real SQLite + DuckDB data)
- [ ] `tests/unit/test_cli_ingest.py` — stubs for INFRA-05 (ingest command)
- [ ] `tests/unit/test_cli_generate_plan.py` — stubs for INFRA-05 (generate-plan command)
- [ ] `tests/unit/test_cli_backtest.py` — stubs for INFRA-05 (backtest command)
- [ ] `tests/unit/test_score_handler_events.py` — stubs for INFRA-07 (event publishing in handler)
- [ ] `tests/unit/test_ddd_boundaries.py` — stubs for INFRA-08 (no cross-context domain imports)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CLI commands produce visible output | INFRA-05 | Output format subjective | Run `python -m cli.main ingest --help` and verify help text renders |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
