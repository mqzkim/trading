---
phase: 27-scoring-expansion
plan: "02"
subsystem: scoring
tags: [testing, sentiment, macd, atr, composite, sentiment-confidence, event-bus]
dependency_graph:
  requires: [27-01]
  provides: [phase-27-test-coverage, regression-lock]
  affects: [scoring-domain, scoring-infrastructure, scoring-application]
tech_stack:
  added: []
  patterns: [mock-external-calls, patch-local-imports, e2e-with-mocked-clients]
key_files:
  created:
    - tests/unit/test_sentiment_score_vo.py
    - tests/unit/test_macd_normalization.py
    - tests/unit/test_composite_weight_renorm.py
    - tests/unit/test_real_sentiment_adapter.py
    - tests/integration/test_scoring_expansion_e2e.py
  modified: []
decisions:
  - "Patch yfinance at yfinance.Ticker (module level) since it is imported locally inside methods"
  - "Use patch.object(RealSentimentAdapter, '_fetch_news_sentiment') for clean news source isolation in HIGH confidence test"
  - "E2E test uses is_ok() not .ok property — Result type uses method not attribute"
metrics:
  duration: 8 minutes
  completed_date: "2026-03-17"
  tasks_completed: 2
  files_modified: 5
---

# Phase 27 Plan 02: Scoring Expansion Tests Summary

77 focused tests across 5 files locking in Phase 27 correctness — SentimentScore VO expansion, MACD ATR normalization fix, composite weight renormalization, RealSentimentAdapter mocking, and E2E ScoreSymbolHandler integration.

## What Was Built

### Task 1: Unit tests for SentimentScore VO, MACD fix, and composite renormalization

**tests/unit/test_sentiment_score_vo.py** (22 tests):
- SentimentConfidence enum: 4 distinct variants, str enum for serialization, importable from domain package
- SentimentScore VO: backward compat (value=50), full construction with all sub-fields, partial sub-scores, immutability, validation (rejects -1 and 101)
- SentimentUpdatedEvent: importable, DomainEvent subclass, all required fields, frozen, None sub-scores allowed

**tests/unit/test_macd_normalization.py** (14 tests):
- ATR parameter accepted: compute() with/without atr21 works
- NVR high-priced stock: histogram=50, atr21=198 → range [-396,+396] → score ~56.3 (not saturated at 100)
- AAPL case: histogram=1.5, atr21=3.5 → range [-7,+7] → score ~60.7
- Fallback range: without ATR, large histogram saturates to 100 (documented, acceptable)
- Other indicators (RSI, ADX, OBV) unaffected when atr21 is passed
- All 5 sub-scores present regardless of atr21

**tests/unit/test_composite_weight_renorm.py** (11 tests):
- NONE confidence swing: 0.4/0.4/0.2 → 0.5/0.5 → expected 65.0 for fund=60, tech=70
- HIGH/MEDIUM/LOW confidence: full 3-axis weights (NONE is the only special case)
- Position strategy NONE: 0.5/0.3/0.2 → 0.625/0.375 → expected 72.5 for fund=80, tech=60
- G-Score blending works with both NONE and HIGH confidence

### Task 2: RealSentimentAdapter mocked tests + E2E integration test

**tests/unit/test_real_sentiment_adapter.py** (17 tests):
- Required keys always returned
- confidence=NONE when all sources fail (exception), neutral score=50.0
- confidence=HIGH when all 4 sources available (3 yfinance + mocked news)
- confidence=MEDIUM when 3 sources available (recs + institutional + insider, no news)
- Bullish analyst ratio (20/25=0.8 → score>70), bearish (2/25=0.08 → score<40)
- No Alpaca keys → news_score=None, no API call
- Empty DataFrames → None for insider/institutional/analyst scores
- VADER compound=0.5 → (0.5+1)/2*100 = 75.0; negative compound → score<50

**tests/integration/test_scoring_expansion_e2e.py** (13 tests):
- technical_sub_scores: 5 entries named RSI/MACD/MA/ADX/OBV with value and explanation
- MACD ATR: atr21=3.5, histogram=1.2 → score in [50,70] (not saturated)
- SentimentUpdatedEvent published with correct symbol and confidence
- ScoreUpdatedEvent still published (regression check)
- NONE confidence composite = 0.5*fundamental + 0.5*technical (within 2.0 tolerance)
- Safety gate: Z>1.81, M<-1.78 → safety_passed=True; Z<1.81 → safety_passed=False

## Verification Results

```
검증 결과:
- typecheck: 1 pre-existing error in src/pipeline/application/handlers.py (out of scope, unrelated)
- test: PASS (77 Phase 27 new + 71 regression = 148 total)
- lint: PASS (ruff 0 errors)
```

Breakdown of new tests:
- test_sentiment_score_vo.py: 22 tests
- test_macd_normalization.py: 14 tests
- test_composite_weight_renorm.py: 11 tests
- test_real_sentiment_adapter.py: 17 tests
- test_scoring_expansion_e2e.py: 13 tests
- **Total: 77 new tests**

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed `result.ok` attribute reference in E2E test**
- **Found during:** Task 2 E2E test execution
- **Issue:** Used `result.ok` but Result type uses `result.is_ok()` method (not an attribute)
- **Fix:** Changed to `result.is_ok()` in test assertion
- **Files modified:** tests/integration/test_scoring_expansion_e2e.py

**2. [Rule 1 - Bug] Fixed yfinance mock target — `@patch("src.scoring...yf")` fails**
- **Found during:** Task 2 — test_real_sentiment_adapter.py first run
- **Issue:** yfinance imported locally inside methods (`import yfinance as yf`), so module-level patch fails
- **Fix:** Changed all patches to `@patch("yfinance.Ticker")` and `patch.object(RealSentimentAdapter, "_fetch_news_sentiment")` for targeted isolation
- **Files modified:** tests/unit/test_real_sentiment_adapter.py

## Self-Check: PASSED
