---
phase: 07-technical-scoring-engine
verified: 2026-03-12T09:00:00Z
status: passed
score: 4/4 must-haves verified
re_verification: true
  previous_status: gaps_found
  previous_score: 2/4
  gaps_closed:
    - "CLI score command calls ScoreSymbolHandler.handle() (not legacy score_symbol())"
    - "Overall CompositeScore uses 40/40/20 weights at CLI surface (core/scoring/composite.py updated)"
  gaps_remaining: []
  regressions: []
human_verification: []
---

# Phase 7: Technical Scoring Engine Verification Report

**Phase Goal:** Users see a composite score that blends fundamental quality with technical momentum -- each sub-score is individually visible and explained
**Verified:** 2026-03-12T09:00:00Z
**Status:** passed
**Re-verification:** Yes -- after gap closure (Plan 07-03)

## Goal Achievement

### Observable Truths (Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | CLI `score` command shows 5 individual technical indicator scores (RSI, MACD, MA, ADX, OBV) with plain-text explanations in a sub-table | VERIFIED | `cli/main.py` score command calls `ctx["score_handler"].handle()`. Handler `_get_technical()` fallback calls `compute_all()` and merges raw indicator keys. `_compute_technical_with_subscores()` detects keys and routes through `TechnicalScoringService`, producing 5 sub-scores. Sub-table rendering at lines 144-171 is now active (not dead code). Confirmed by `TestHandlerTechnicalSubScores` (8 tests pass) and `TestHandlerEndToEndSubScoresAndWeights`. |
| 2 | Technical composite score (0-100) computed from 5 indicators with configurable weights | VERIFIED | `TechnicalScoringService.compute()` produces weighted RSI(0.20) + MACD(0.20) + MA(0.25) + ADX(0.15) + OBV(0.20). 33 unit tests pass. Now reached from CLI via handler. |
| 3 | Overall CompositeScore combines fundamental (40%), technical (40%), and sentiment (20% placeholder) | VERIFIED | `core/scoring/composite.py` `WEIGHTS["swing"] = {"fundamental": 0.40, "technical": 0.40, "sentiment": 0.20}` confirmed. CLI routes through `CompositeScoringService` in DDD handler which uses `STRATEGY_WEIGHTS["swing"] = 40/40/20`. Both paths now agree on 40/40/20. AST verification: CLI does not import `core.scoring.composite`. |
| 4 | Strong fundamentals + bearish technicals produces visibly lower composite than aligned signals | VERIFIED | Domain layer verified: `TechnicalScoringService` + `CompositeScoringService` path confirmed. Integration test `test_handler_end_to_end_sub_scores_and_weights` confirms composite uses 40/40/20 formula. Both domain and CLI surface now use same path. |

**Score:** 4/4 success criteria verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `cli/main.py` | CLI score command routed through ScoreSymbolHandler | VERIFIED | `score()` calls `ctx["score_handler"].handle(ScoreSymbolCommand(...))`. No import of `core.scoring.composite` (AST test passes). Sub-table rendering code at lines 144-171 is now active. |
| `core/scoring/composite.py` | WEIGHTS["swing"] updated to 40/40/20 | VERIFIED | Line 5: `"swing": {"fundamental": 0.40, "technical": 0.40, "sentiment": 0.20}`. Runtime confirmed via `from core.scoring.composite import WEIGHTS` assertion. |
| `src/scoring/application/handlers.py` | Handler `_get_technical()` fallback fetches OHLCV and returns raw indicator values | VERIFIED | Lines 192-229: calls `compute_all(df)`, merges `rsi`, `macd_histogram`, `close`, `ma50`, `ma200`, `adx`, `obv_change_pct` into result dict. Enables `_compute_technical_with_subscores()` detection. |
| `tests/unit/test_cli_score_technical.py` | 3 gap-closure tests added (integration, AST, error handling) | VERIFIED | `TestHandlerEndToEndSubScoresAndWeights`, `TestCLIDoesNotImportLegacyScoring`, `TestHandlerErrorProducesErrResult` all present and passing. File is 313 lines (above 80-line minimum). |
| `src/scoring/domain/value_objects.py` | TechnicalIndicatorScore VO, updated STRATEGY_WEIGHTS | VERIFIED | Unchanged from Plan 07-01. All correct. |
| `src/scoring/domain/services.py` | TechnicalScoringService with compute() | VERIFIED | Unchanged from Plan 07-01. All correct. |
| `src/scoring/infrastructure/core_scoring_adapter.py` | TechnicalIndicatorAdapter | VERIFIED | Unchanged from Plan 07-02. All correct. |
| `tests/unit/test_technical_scoring_service.py` | 33 unit tests for TechnicalScoringService | VERIFIED | 33 tests pass. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cli/main.py (score command)` | `src/scoring/application/handlers.py (ScoreSymbolHandler)` | `ctx["score_handler"].handle(ScoreSymbolCommand(...))` | WIRED | Confirmed at lines 100-102 of `cli/main.py`. AST test `TestCLIDoesNotImportLegacyScoring` passes. |
| `src/scoring/application/handlers.py (_get_technical fallback)` | `core/data/indicators.py (compute_all)` | Handler calls `compute_all(df)` and merges raw values | WIRED | Lines 198-229 in handlers.py. `compute_all` present. `obv_change_pct` computed with 60-day lookback. |
| `cli/main.py` | `result["technical_sub_scores"]` | `handler.handle()` returns sub-scores; CLI renders sub-table | WIRED | `result.get("technical_sub_scores", [])` at line 145. `if sub_scores:` guard at line 146. Sub-table rendered at lines 147-171. |
| `src/scoring/domain/services.py (TechnicalScoringService)` | `src/scoring/domain/value_objects.py (TechnicalIndicatorScore, TechnicalScore)` | `compute()` returns TechnicalScore with sub-scores | WIRED | Verified in initial verification. Unchanged. |
| `src/scoring/infrastructure/core_scoring_adapter.py` | `core/data/indicators.py (compute_all)` | Adapter calls `compute_all`, extracts floats | WIRED | Verified in initial verification. Unchanged. |
| `src/scoring/application/handlers.py` | `src/scoring/domain/services.py (TechnicalScoringService)` | Handler calls `_compute_technical_with_subscores()` | WIRED | Lines 155-180. `TechnicalScoringService` imported and used. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| TECH-01 | 07-01-PLAN.md | RSI/MACD/MA/ADX/OBV 5개 지표를 DDD 스코어링 컨텍스트에 통합 | SATISFIED | `TechnicalScoringService` domain service + `TechnicalIndicatorScore` VO with 5 indicators. Reachable from CLI via handler. 33 unit tests pass. REQUIREMENTS.md marked complete. |
| TECH-02 | 07-01-PLAN.md | 기술적 복합 점수 (0-100) 산출 (가중 합산) | SATISFIED | `TechnicalScoringService.compute()` produces weighted composite RSI(0.20)+MACD(0.20)+MA(0.25)+ADX(0.15)+OBV(0.20). Formula verified by `test_composite_is_weighted_sum`. REQUIREMENTS.md marked complete. |
| TECH-03 | 07-01-PLAN.md | 기존 CompositeScore에 기술 점수 통합 (기본40%/기술40%/센티먼트20%) | SATISFIED | `core/scoring/composite.py` swing=40/40/20 updated. DDD `STRATEGY_WEIGHTS["swing"]`=40/40/20. CLI uses DDD handler path. Integration test confirms 40/40/20 formula. REQUIREMENTS.md marked complete. |
| TECH-04 | 07-02-PLAN.md | 서브 스코어 분해 출력 (5개 지표별 개별 점수 + 설명) | SATISFIED | Handler produces `technical_sub_scores` list with 5 entries (name, value, explanation, raw_value). CLI renders "Technical Indicators" sub-table with color-coded scores. Previously dead code is now active. REQUIREMENTS.md marked complete. |

### Anti-Patterns Found

None. Previous blockers resolved:

| Previously Flagged | Resolution |
|--------------------|------------|
| `cli/main.py` lines 157-183: dead sub-table code | Now active -- CLI routes through handler which returns `technical_sub_scores` |
| `core/scoring/composite.py` swing = 35/40/25 | Updated to 40/40/20 at line 5 |

### Human Verification Required

None -- all gaps were verifiable programmatically. The gap closure is fully verified by:
- 669 tests passing (full regression, no new failures)
- 3 new gap-closure tests all passing
- 3 key link AST/runtime verifications passing
- Lint clean (ruff check passes)
- No new type errors in modified files (pre-existing errors in `core/scoring/technical.py` and `core/data/client.py` are out of scope and pre-date Phase 7)

### Gap Closure Summary

Both gaps from the initial verification (2026-03-12T08:30:00Z) were closed in Plan 07-03:

**Gap 1 (CLOSED): CLI score command bypassed domain layer**

Fix: `cli/main.py` `score()` function now calls `ctx["score_handler"].handle(ScoreSymbolCommand(symbol, strategy))` instead of `core.scoring.composite.score_symbol()`. The previously-dead sub-table rendering code (lines 144-171) is now reached because the handler's result dict includes `technical_sub_scores`.

**Gap 2 (CLOSED): Old composite weights in CLI path**

Fix: `core/scoring/composite.py` `WEIGHTS["swing"]` updated from `0.35/0.40/0.25` to `0.40/0.40/0.20`. Additionally, the CLI no longer calls this function directly -- it goes through the DDD `CompositeScoringService` which already had correct weights.

**Root cause addressed:** Both gaps shared the root cause that the CLI was not wired through the DDD handler. The handler `_get_technical()` fallback also had a bug (calling `compute_technical_score(symbol)` with wrong signature) that was fixed by fetching OHLCV inline and merging raw indicator keys.

---
_Verified: 2026-03-12T09:00:00Z_
_Verifier: Claude (gsd-verifier)_
_Re-verification: Yes (Plan 07-03 gap closure)_
