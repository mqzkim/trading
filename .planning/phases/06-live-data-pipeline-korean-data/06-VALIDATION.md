---
phase: 6
slug: live-data-pipeline-korean-data
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4+ with pytest-asyncio |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/unit/test_quality_checker.py tests/unit/test_yfinance_adapter.py tests/unit/test_edgartools_client.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_quality_checker.py tests/unit/test_yfinance_adapter.py tests/unit/test_edgartools_client.py tests/unit/test_duckdb_store.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | DATA-01 | unit | `pytest tests/unit/test_yfinance_adapter.py -x` | ✅ | ⬜ pending |
| 06-01-02 | 01 | 1 | DATA-01 | integration | `pytest tests/integration/test_data_ingest.py -x` | ✅ | ⬜ pending |
| 06-01-03 | 01 | 1 | DATA-02 | unit | `pytest tests/unit/test_edgartools_client.py -x` | ✅ | ⬜ pending |
| 06-02-01 | 02 | 1 | DATA-03 | unit | `pytest tests/unit/test_quality_checker.py -x` | ✅ | ⬜ pending |
| 06-02-02 | 02 | 1 | DATA-03 | integration | `pytest tests/integration/test_data_ingest.py::test_pipeline_quality_failure -x` | ✅ | ⬜ pending |
| 06-03-01 | 03 | 2 | DATA-04 | unit | `pytest tests/unit/test_pykrx_client.py -x` | ❌ W0 | ⬜ pending |
| 06-03-02 | 03 | 2 | DATA-05 | unit | `pytest tests/unit/test_pykrx_client.py -x` | ❌ W0 | ⬜ pending |
| 06-03-03 | 03 | 2 | DATA-04/05 | unit | `pytest tests/unit/test_cli_ingest.py -x` | ✅ | ⬜ pending |
| 06-04-01 | 04 | 2 | DATA-06 | unit | `pytest tests/unit/test_regime_data_store.py -x` | ❌ W0 | ⬜ pending |
| 06-04-02 | 04 | 2 | DATA-06 | unit | `pytest tests/unit/test_duckdb_store.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_pykrx_client.py` — stubs for DATA-04, DATA-05 (pykrx OHLCV + fundamentals)
- [ ] `tests/unit/test_regime_data_store.py` — stubs for DATA-06 (regime data DuckDB storage)
- [ ] `pip install pykrx` — pykrx not yet in dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| yfinance adjusted close matches source | DATA-01 | Requires live API call to verify | Run `ingest AAPL` and compare closing price with Yahoo Finance website |
| pykrx KOSPI data accuracy | DATA-04 | Requires live Korean market API | Run `ingest --market kr 005930` and compare with KRX website |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
