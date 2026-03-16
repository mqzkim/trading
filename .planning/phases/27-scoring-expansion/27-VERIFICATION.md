---
phase: 27-scoring-expansion
verified: 2026-03-16T19:25:44Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 27: Scoring Expansion Verification Report

**Phase Goal:** Composite score reflects three real axes -- fundamental (existing), technical (5 indicators), and sentiment (4 data sources) -- with proper normalization and confidence tracking
**Verified:** 2026-03-16T19:25:44Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | TechnicalScore returned by ScoreSymbolHandler contains non-None rsi_score, macd_score, ma_score, adx_score, obv_score sub-scores | VERIFIED | All 5 sub-scores confirmed non-None in programmatic check; TechnicalScoringService.compute() always returns TechnicalScore with all 5 TechnicalIndicatorScore fields set |
| 2 | MACD normalization uses ATR-scaled dynamic range (not hardcoded [-5, +5]) | VERIFIED | `_score_macd()` in services.py line 303: uses `[-2*atr21, +2*atr21]` when atr21 provided. NVR case (histogram=50, atr21=198) yields score 56.3, not 100 |
| 3 | SentimentScore VO contains news_score, insider_score, institutional_score, analyst_score sub-fields plus a confidence field | VERIFIED | value_objects.py lines 114-131: all 5 new fields present as optional with defaults. SentimentScore(value=50) still works |
| 4 | SentimentScore confidence is HIGH/MEDIUM/LOW/NONE based on data coverage | VERIFIED | SentimentConfidence enum (str, Enum) with 4 variants at value_objects.py lines 14-25. RealSentimentAdapter.get() maps `available_count` to confidence via lookup dict |
| 5 | CompositeScore.compute() re-normalizes weights to fundamental+technical when confidence is NONE | VERIFIED | CompositeScoringService.compute() services.py lines 160-172: `if sentiment_confidence == SentimentConfidence.NONE` drops sentiment axis, renormalizes. Confirmed: fund=60, tech=70, NONE => 65.0 |
| 6 | SentimentUpdatedEvent is published on the EventBus after scoring completes | VERIFIED | handlers.py lines 158-168: `sentiment_event = SentimentUpdatedEvent(...)` + `bus.publish(sentiment_event)`. bootstrap.py subscribes via `bus.subscribe(SentimentUpdatedEvent, _log_sentiment_event)` |
| 7 | Real news sentiment (Alpaca + VADER), insider buy/sell ratio (yfinance), institutional holdings change (yfinance), analyst revision (yfinance) are fetched | VERIFIED | RealSentimentAdapter in core_scoring_adapter.py: `_fetch_news_sentiment()` (Alpaca NewsClient + VADER), `_fetch_insider_score()` (yf.insider_transactions), `_fetch_institutional_score()` (yf.institutional_holders), `_fetch_analyst_score()` (yf.recommendations + analyst_price_targets). All wrapped in try/except with None fallback |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|---------|--------|---------|
| `src/scoring/domain/value_objects.py` | Expanded SentimentScore VO with sub-scores + SentimentConfidence enum | VERIFIED | `SentimentConfidence` enum (lines 14-25), `SentimentScore` with 5 new optional fields (lines 114-131) |
| `src/scoring/domain/events.py` | SentimentUpdatedEvent domain event | VERIFIED | `SentimentUpdatedEvent` at lines 22-35 with all required fields |
| `src/scoring/domain/services.py` | MACD ATR-based normalization fix; CompositeScoringService handles NONE confidence | VERIFIED | `_score_macd(self, histogram, atr21)` (line 303), `_score_macd_atr` pattern via dynamic `half_range = 2.0 * float(atr21)`; `if sentiment_confidence == SentimentConfidence.NONE` (line 160) |
| `src/scoring/infrastructure/core_scoring_adapter.py` | RealSentimentAdapter with 4 real data sources | VERIFIED | `RealSentimentAdapter` class (line 247) with all 4 `_fetch_*` methods |
| `tests/unit/test_sentiment_score_vo.py` | SentimentScore VO + SentimentConfidence enum unit tests | VERIFIED | File exists; 22 tests, all pass |
| `tests/unit/test_macd_normalization.py` | MACD ATR-based normalization unit tests | VERIFIED | File exists; 14 tests, all pass |
| `tests/unit/test_composite_weight_renorm.py` | CompositeScore confidence-aware weight renormalization tests | VERIFIED | File exists; 11 tests, all pass |
| `tests/unit/test_real_sentiment_adapter.py` | RealSentimentAdapter unit tests (mocked external calls) | VERIFIED | File exists; 17 tests, all pass |
| `tests/integration/test_scoring_expansion_e2e.py` | Full ScoreSymbolHandler E2E test | VERIFIED | File exists; 13 tests, all pass |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/scoring/application/handlers.py` | `SentimentUpdatedEvent` | `bus.publish` after scoring | WIRED | Lines 158-168: `sentiment_event = SentimentUpdatedEvent(...)` then `bus.publish(sentiment_event)` |
| `src/scoring/infrastructure/core_scoring_adapter.py` | `RealSentimentAdapter.get(symbol)` | Replaces SentimentDataAdapter in bootstrap | WIRED | bootstrap.py lines 97-113: `from src.scoring.infrastructure.core_scoring_adapter import RealSentimentAdapter`; `sentiment_adapter = RealSentimentAdapter(...)` |
| `src/scoring/domain/services.py` | `TechnicalScoringService._score_macd` | ATR parameter added to compute() | WIRED | `compute()` signature includes `atr21: float | None = None`; passed to `_score_macd(macd_histogram, atr21)` |
| `src/scoring/domain/services.py` | `CompositeScoringService.compute()` | confidence=NONE weight renormalization | WIRED | `sentiment_confidence: SentimentConfidence = SentimentConfidence.MEDIUM` in signature; NONE branch renormalizes |
| `src/scoring/application/handlers.py` | `TechnicalScoringService` | atr21 from technical_data | WIRED | `_compute_technical_with_subscores()` passes `atr21=technical_data.get("atr21")` to `self._technical_scoring.compute()` |
| `src/scoring/infrastructure/core_scoring_adapter.py` | `TechnicalScoringService.compute()` | atr21 extracted from indicators | WIRED | `compute_technical_subscores()` extracts `atr21 = _safe_float(_safe_last(ind["atr21"]))` and passes `atr21=atr21` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| TECH-01 | 27-01 | RSI(14) scoring integrated into TechnicalScore VO with 0-100 mapping | SATISFIED | `_score_rsi()` in services.py; `rsi_score: TechnicalIndicatorScore` in TechnicalScore VO |
| TECH-02 | 27-01 | MACD scoring with histogram direction and crossover detection | SATISFIED | `_score_macd()` in services.py uses ATR-scaled normalization |
| TECH-03 | 27-01 | Moving average trend scoring (50/200-day MA, golden/death cross) | SATISFIED | `_score_ma()` in services.py covers close vs MA50/MA200, golden/death cross |
| TECH-04 | 27-01 | ADX trend strength scoring | SATISFIED | `_score_adx()` in services.py |
| TECH-05 | 27-01 | OBV volume confirmation scoring | SATISFIED | `_score_obv()` in services.py |
| TECH-06 | 27-01 | MACD normalization bug fixed (hardcoded [-5,+5] range) | SATISFIED | Dynamic `[-2*atr21, +2*atr21]` range; NVR score 56.3 not 100 |
| TECH-07 | 27-01 | Composite score reflects 3-axis weights | SATISFIED | CompositeScoringService.compute() with NONE confidence renormalization |
| SENT-01 | 27-01 | News sentiment via Alpaca News API + VADER | SATISFIED | `_fetch_news_sentiment()` in RealSentimentAdapter |
| SENT-02 | 27-01 | Insider trade scoring from Form 4 data (buy/sell ratio) | SATISFIED | `_fetch_insider_score()` via yfinance insider_transactions |
| SENT-03 | 27-01 | Institutional holdings change rate from 13F filings | SATISFIED | `_fetch_institutional_score()` via yfinance institutional_holders |
| SENT-04 | 27-01 | Analyst estimate revision direction integrated | SATISFIED | `_fetch_analyst_score()` via yfinance recommendations + analyst_price_targets |
| SENT-05 | 27-01 | SentimentScore VO populated with real sub-component data | SATISFIED | SentimentScore has news_score, insider_score, institutional_score, analyst_score fields; handler builds full VO from adapter dict |
| SENT-06 | 27-01 | Sentiment confidence field added (data freshness/coverage indicator) | SATISFIED | SentimentConfidence enum + SentimentScore.confidence field + SentimentUpdatedEvent.confidence field |

All 13 phase requirements (TECH-01 through TECH-07, SENT-01 through SENT-06) are satisfied. No orphaned requirements detected.

---

### Anti-Patterns Found

No blockers found. The following items were noted:

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/scoring/domain/value_objects.py` | 181-203 | `CompositeScore.compute()` classmethod does NOT apply NONE confidence renormalization (only CompositeScoringService.compute() does) | Info | The classmethod is a simpler static path not used by the production handler; the handler always calls CompositeScoringService.compute(). No impact. |
| `src/pipeline/application/handlers.py` | 126 | Pre-existing mypy error: `Item "None" of "DuckDBPyConnection | None" has no attribute "execute"` | Info | Pre-existing error unrelated to Phase 27; out of scope |

---

### Human Verification Required

None. All behavioral contracts were verified programmatically:
- Sub-score values confirmed with live invocations
- MACD saturation fix confirmed numerically (56.3 vs old 100)
- Weight renormalization confirmed numerically (65.0 for fund=60, tech=70)
- RealSentimentAdapter graceful degradation confirmed (news_score=None without Alpaca keys)
- Event bus wiring confirmed via source inspection and test coverage

---

### Test Results Summary

| Test Suite | Tests | Result |
|-----------|-------|--------|
| `test_sentiment_score_vo.py` | 22 | PASS |
| `test_macd_normalization.py` | 14 | PASS |
| `test_composite_weight_renorm.py` | 11 | PASS |
| `test_real_sentiment_adapter.py` | 17 | PASS |
| `test_scoring_expansion_e2e.py` | 13 | PASS |
| **Phase 27 total** | **77** | **PASS** |
| Regression: `test_technical_scoring_service.py` + `test_scoring_composite.py` + `test_scoring_composite_v2.py` + `test_core_scoring_adapter.py` + `test_sync_event_bus.py` | 71 | PASS |
| **Combined total** | **148** | **PASS** |

mypy: 0 errors in scoring module (1 pre-existing error in pipeline, unrelated to Phase 27)
ruff: 0 errors in `src/scoring/`

---

### Goal Achievement Summary

The phase goal is **fully achieved**. The composite score now reflects three real axes:

1. **Fundamental (existing):** Unchanged — Piotroski F-Score, Altman Z-Score, Beneish M-Score, Mohanram G-Score
2. **Technical (5 indicators):** RSI, MACD (with ATR-scaled normalization), MA trend (golden/death cross), ADX strength, OBV volume — all returning real sub-scores with values and explanations
3. **Sentiment (4 data sources):** Alpaca News+VADER, yfinance insider transactions, yfinance institutional holdings, yfinance analyst recommendations — all fetched live, gracefully degrading to None on failure

Proper normalization: MACD uses `[-2*ATR21, +2*ATR21]` dynamic range (not hardcoded `[-5,+5]`).
Confidence tracking: `SentimentConfidence.NONE/LOW/MEDIUM/HIGH` based on data coverage, with automatic weight renormalization to 50/50 fundamental/technical when sentiment is unavailable.

---

_Verified: 2026-03-16T19:25:44Z_
_Verifier: Claude (gsd-verifier)_
