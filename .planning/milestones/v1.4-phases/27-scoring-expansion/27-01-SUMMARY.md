---
phase: 27-scoring-expansion
plan: "01"
subsystem: scoring
tags: [sentiment, technical, macd, atr, event-bus, value-objects]
dependency_graph:
  requires: [26-02]
  provides: [real-sentiment-scoring, macd-atr-normalization, sentiment-confidence, sentiment-event]
  affects: [scoring-domain, scoring-infrastructure, scoring-application, bootstrap]
tech_stack:
  added: [vaderSentiment>=3.3.2]
  patterns: [SentimentConfidence-enum, ATR-dynamic-normalization, weight-renormalization, sentinel-NONE-confidence]
key_files:
  created:
    - tests/unit/test_27_01_scoring_expansion.py
  modified:
    - src/scoring/domain/value_objects.py
    - src/scoring/domain/events.py
    - src/scoring/domain/services.py
    - src/scoring/domain/__init__.py
    - src/scoring/infrastructure/core_scoring_adapter.py
    - src/scoring/infrastructure/__init__.py
    - src/scoring/application/handlers.py
    - src/bootstrap.py
    - pyproject.toml
decisions:
  - "MACD normalization uses ATR-scaled dynamic range [-2*atr21, +2*atr21] instead of hardcoded [-5, +5]"
  - "SentimentConfidence.NONE triggers fundamental+technical weight renormalization (drops 20% sentiment axis)"
  - "RealSentimentAdapter uses Alpaca News+VADER for news; yfinance for insider/institutional/analyst"
  - "SentimentDataAdapter kept for backward compat; bootstrap switched to RealSentimentAdapter"
  - "confidence field in SentimentScore is SentimentConfidence enum (str enum for serialization)"
metrics:
  duration: 7 minutes
  completed_date: "2026-03-17"
  tasks_completed: 2
  files_modified: 9
---

# Phase 27 Plan 01: Scoring Expansion Summary

Expanded SentimentScore VO with real 4-source sentiment data, fixed MACD normalization bug with ATR-dynamic range, and added composite weight renormalization when sentiment data is unavailable.

## What Was Built

### Task 1: Domain layer expansion (TDD)
- **SentimentConfidence enum** (`NONE/LOW/MEDIUM/HIGH`) added to `value_objects.py`
- **SentimentScore VO** expanded with `news_score`, `insider_score`, `institutional_score`, `analyst_score`, `confidence` fields — all optional for backward compat
- **SentimentUpdatedEvent** added to `events.py` — published after scoring
- **MACD ATR fix**: `TechnicalScoringService.compute()` accepts `atr21: float | None = None`; uses `[-2*atr21, +2*atr21]` range when available (vs hardcoded `[-5, +5]`); NVR with ATR=198 gets moderate score ~56 instead of 100
- **Composite NONE confidence**: `CompositeScoringService.compute()` accepts `sentiment_confidence` param; when `NONE`, drops sentiment axis and renormalizes fundamental+technical (e.g., 40/40/20 → 50/50)
- `domain/__init__.py` exports: `SentimentConfidence`, `SentimentUpdatedEvent`

### Task 2: Infrastructure + wiring (TDD)
- **RealSentimentAdapter** with 4 live data sources:
  - News: Alpaca News API + VADER compound score → 0-100 (requires keys, graceful None if absent)
  - Insider: yfinance `insider_transactions` buy/(buy+sell) ratio
  - Institutional: yfinance `institutional_holders` QoQ pctHeld change
  - Analyst: yfinance `recommendations` bullish ratio + price target upside (60/40 blend)
  - All wrapped in `try/except` — returns `None` on failure
  - Confidence: `{0: NONE, 1: LOW, 2: LOW, 3: MEDIUM, 4: HIGH}[available_count]`
- **handlers.py** updated: builds full `SentimentScore` VO from adapter dict; passes `sentiment_confidence` to composite; publishes `SentimentUpdatedEvent`; passes `atr21` to technical service
- **bootstrap.py**: `RealSentimentAdapter` replaces `SentimentDataAdapter`; `SentimentUpdatedEvent` subscribed to logging handler
- **pyproject.toml**: `vaderSentiment>=3.3.2` added to dependencies

## Verification Results

```
검증 결과:
- typecheck: PASS (mypy 0 errors, 14 files)
- test: PASS (99/99 passed)
- lint: PASS (ruff 0 errors)
```

Manual verifications:
- `RealSentimentAdapter().get('AAPL')` → `{sentiment_score: 65.9, institutional_score: 68.6, analyst_score: 63.3, confidence: LOW}`
- NVR MACD score (histogram=50, atr21=198): 56.3 (was 100 with old hardcoded range)
- Composite with NONE confidence: 65.0 (0.50×60 + 0.50×70) — correct renormalization

## Deviations from Plan

None — plan executed exactly as written.

The only fix applied was a type annotation in `RealSentimentAdapter._fetch_news_sentiment()`: alpaca-py's `NewsRequest` expects `symbols` as `str` not `list[str]` (mypy caught this); fixed with `type: ignore[arg-type]` since the library docs say list is accepted at runtime.

## Self-Check: PASSED

All created/modified files verified to exist on disk.

Commits verified:
- e7cc88f: test(27-01): add failing tests for scoring expansion (RED phase)
- 01a90ca: feat(27-01): expand SentimentScore VO, fix MACD ATR normalization, add SentimentUpdatedEvent
- 26c4f11: feat(27-01): wire RealSentimentAdapter and SentimentUpdatedEvent into bootstrap and handlers

99/99 tests passing. mypy clean. ruff clean.
