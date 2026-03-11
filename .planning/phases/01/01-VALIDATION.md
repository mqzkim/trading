---
phase: 1
slug: data-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 7.4 + pytest-asyncio >= 0.21 |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `python -m pytest tests/unit/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/unit/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DATA-01 | integration | `pytest tests/integration/test_data_ingest.py::test_ohlcv_fetch -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | DATA-02 | integration | `pytest tests/integration/test_data_ingest.py::test_sec_financials -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | DATA-03 | unit | `pytest tests/unit/test_duckdb_store.py -x` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | DATA-04 | unit | `pytest tests/unit/test_quality_checker.py -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | SCOR-01 | unit | `pytest tests/unit/test_scoring_safety.py -x` | ✅ | ⬜ pending |
| 01-02-02 | 02 | 2 | SCOR-02 | unit | `pytest tests/unit/test_scoring_fundamental.py -x` | ✅ | ⬜ pending |
| 01-02-03 | 02 | 2 | SCOR-03 | unit | `pytest tests/unit/test_scoring_safety.py::test_altman_healthy_company -x` | ✅ | ⬜ pending |
| 01-02-04 | 02 | 2 | SCOR-04 | unit | `pytest tests/unit/test_scoring_safety.py::test_beneish_clean_company -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_duckdb_store.py` — stubs for DATA-03
- [ ] `tests/unit/test_quality_checker.py` — stubs for DATA-04
- [ ] `tests/unit/test_edgartools_client.py` — stubs for DATA-02 (unit with mocks)
- [ ] `tests/unit/test_universe_provider.py` — universe management
- [ ] `tests/unit/test_event_bus.py` — async event bus
- [ ] `tests/unit/test_yfinance_adapter.py` — DATA-01 adapter wrapping
- [ ] `tests/unit/test_core_scoring_adapter.py` — SCOR-01~04 adapter wrapping
- [ ] `tests/integration/test_data_ingest.py` — DATA-01 + DATA-02 end-to-end
- [ ] `pip install duckdb>=1.5.0 edgartools>=5.23.0 aiohttp>=3.9` — new dependencies

*(Existing tests for SCOR-01~04 already pass via core/scoring/ — new adapter tests verify DDD wrapping)*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DuckDB 500+ ticker screening < 30s | DATA-03 | Performance benchmark requires real data volume | Ingest 500+ tickers, run screening query, measure wall time |
| edgartools XBRL mid-cap coverage | DATA-02 | Coverage varies by company, needs real API call | Test 20 random S&P 400 tickers for XBRL availability |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
