---
phase: 02-analysis-core
plan: 03
subsystem: valuation
tags: [ensemble-valuation, margin-of-safety, confidence-weighting, sector-thresholds, duckdb, adapter-pattern, ddd]

# Dependency graph
requires:
  - phase: 02-analysis-core
    provides: DCF/EPV/Relative pure math, valuation domain VOs, IValuationRepository, DuckDB pattern
provides:
  - Ensemble valuation with confidence-weighted DCF(40%)+EPV(35%)+Relative(25%)
  - Margin of safety with GICS sector-adjusted thresholds
  - CoreValuationAdapter wrapping all core/valuation/ functions
  - DuckDBValuationStore for valuation result persistence
  - EnsembleValuationService orchestrating full pipeline
affects: [03-signals, 03-screening, valuation-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [confidence-weighted-ensemble, sector-mos-thresholds, cv-model-agreement, adapter-delegation]

key-files:
  created:
    - core/valuation/ensemble.py
    - src/valuation/infrastructure/core_valuation_adapter.py
    - src/valuation/infrastructure/duckdb_valuation_store.py
    - tests/unit/test_ensemble_valuation.py
    - tests/unit/test_margin_of_safety.py
  modified:
    - src/valuation/domain/services.py
    - src/valuation/domain/__init__.py
    - src/valuation/infrastructure/__init__.py
    - core/valuation/__init__.py

key-decisions:
  - "Ensemble confidence = 0.6 * model_agreement(CV) + 0.4 * data_completeness -- agreement weighted higher than completeness"
  - "Single-model agreement = 0.0 (cannot compute CV) -- penalizes single-source valuations"
  - "Relative value estimated as market_price * (1 + (50 - percentile)/100) -- below-median stocks are undervalued"
  - "DuckDBValuationStore accepts connection via DI (not creating own) -- consistent with DDD infrastructure pattern"

patterns-established:
  - "Ensemble pattern: raw_weight = base_weight * confidence, normalize to sum=1.0"
  - "Sector thresholds: GICS sector -> MoS minimum, default 20% for unknown sectors"
  - "CoreValuationAdapter: thin wrapper delegating all params to core functions, no math rewriting"

requirements-completed: [VALU-04, VALU-05]

# Metrics
duration: 4min
completed: 2026-03-12
---

# Phase 2 Plan 03: Ensemble Valuation & Margin of Safety Summary

**Confidence-weighted ensemble (DCF 40% + EPV 35% + Relative 25%) with CV-based model agreement scoring, GICS sector-adjusted margin of safety thresholds, CoreValuationAdapter wrapping all core/valuation/ functions, and DuckDB persistence**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-12T00:30:53Z
- **Completed:** 2026-03-12T00:35:14Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Ensemble valuation produces confidence-weighted intrinsic value with proper weight redistribution when model confidence is low
- Margin of safety uses 10 GICS sector-specific thresholds (Tech 25%, Staples 15%, default 20%)
- CoreValuationAdapter wraps all 6 core/valuation/ functions following adapter pattern
- DuckDBValuationStore implements IValuationRepository with point-in-time querying
- EnsembleValuationService orchestrates DCF+EPV+Relative into final valuation with MoS
- 20 new tests (12 ensemble + 8 MoS), 370 total tests passing, ruff clean, mypy clean

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for ensemble + MoS** - `78650fe` (test)
2. **Task 1 GREEN: Ensemble valuation + MoS implementation** - `0a13b3c` (feat)
3. **Task 2: CoreValuationAdapter + DuckDB store + domain service** - `ed9f448` (feat)

## Files Created/Modified
- `core/valuation/ensemble.py` - compute_ensemble() and compute_margin_of_safety() pure math
- `src/valuation/infrastructure/core_valuation_adapter.py` - Thin adapter wrapping all 6 core/valuation/ functions
- `src/valuation/infrastructure/duckdb_valuation_store.py` - DuckDB persistence with point-in-time query
- `src/valuation/domain/services.py` - EnsembleValuationService orchestrating full pipeline
- `src/valuation/domain/__init__.py` - Updated exports with EnsembleValuationService
- `src/valuation/infrastructure/__init__.py` - Updated exports with adapter and store
- `core/valuation/__init__.py` - Updated exports with ensemble functions
- `tests/unit/test_ensemble_valuation.py` - 12 tests for ensemble weighting and confidence
- `tests/unit/test_margin_of_safety.py` - 8 tests for MoS with sector thresholds

## Decisions Made
- Ensemble confidence formula: 0.6 * model_agreement + 0.4 * data_completeness (agreement weighted higher because disagreeing models reduce reliability more than incomplete data)
- Single-model valuations get agreement=0.0 (CV cannot be computed from one value) which naturally produces low confidence scores
- Relative value conversion: market_price * (1 + (50 - percentile)/100) -- stocks ranking below sector median are estimated as undervalued
- DuckDBValuationStore takes connection via constructor injection rather than creating its own connection, consistent with DDD infrastructure patterns

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness
- Phase 2 (Analysis Core) fully complete: G-Score, composite scoring, DCF, EPV, Relative, ensemble, MoS all implemented
- All core/valuation/ and core/scoring/ pure math functions wrapped by adapters
- DuckDB stores ready for both scoring and valuation results
- ValuationCompletedEvent ready for Phase 3 cross-context communication with signals
- Ready for Phase 3: signals generation, risk management, backtesting

## Self-Check: PASSED

- 9/9 files found
- 3/3 commits found
- 20/20 new tests collected
- 370/370 total tests passing

---
*Phase: 02-analysis-core*
*Completed: 2026-03-12*
