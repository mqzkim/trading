# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-12
**Phases:** 4 | **Plans:** 12 | **Commits:** 106

### What Was Built
- Data ingestion pipeline with DuckDB/SQLite dual-DB and SEC filing point-in-time awareness
- Fundamental scoring (F/Z/M/G-Score) with safety gates and composite 0-100 scoring
- Valuation ensemble (DCF + EPV + Relative) with margin of safety
- Signal generation with BUY/HOLD/SELL reasoning traces
- Risk management with Fractional Kelly sizing and 3-tier drawdown defense
- Trade execution with Alpaca paper trading, human approval CLI, dashboard, and monitoring

### What Worked
- Coarse 4-phase roadmap with strict dependency chain kept execution focused
- Adapter pattern wrapping existing core/ math prevented rewrites and saved significant time
- Frozen dataclass VO pattern with _validate() was consistent and easy to replicate across all domains
- DI for all infrastructure made testing fast and reliable (352+ tests passing)
- YOLO mode with quality profile balanced speed and verification

### What Was Inefficient
- DuckDB vs SQLite store decisions not aligned upfront -- scoring writes to SQLite but screener queries DuckDB, causing integration gaps
- CLI commands added late (Phase 4) without verifying they wire all the way back to Phase 1 entry points
- Domain events defined in all contexts but never wired to EventBus -- async event architecture is scaffolding only
- G-Score and regime adjustment implemented in domain but handler wiring incomplete

### Patterns Established
- Frozen dataclass VOs with `_validate()` and `__post_init__` for domain value objects
- `kw_only=True` for domain event dataclass inheritance
- Local imports inside CLI function bodies (lazy loading pattern)
- alpaca-py imports inside methods only (avoid SDK init on import)
- CoreXxxAdapter pattern: thin adapter wrapping core/ functions, no math rewriting
- DuckDB INSERT OR REPLACE for upsert semantics

### Key Lessons
1. **Wire stores end-to-end before building consumers** — The DuckDB/SQLite mismatch was avoidable if we'd verified the screener's data source matched the scoring store in Phase 2
2. **Add CLI surface incrementally per phase** — Waiting until Phase 4 to add CLI commands left integration gaps. Each phase should expose its capabilities through CLI immediately
3. **Test cross-context integration, not just unit** — 352 passing tests didn't catch that the screener queries a non-existent table. Integration tests spanning bounded contexts would have caught this
4. **Define event contracts early, publish immediately** — Defining events without publishing them creates dead code. Events should be published as soon as they're defined
5. **Adapter pattern is excellent for incremental DDD migration** — Wrapping core/ math with thin adapters preserved correctness while adding DDD structure

### Cost Observations
- Model mix: ~80% sonnet (plan execution), ~15% opus (orchestration/review), ~5% haiku (research/analysis)
- Execution velocity: ~5.5 min/plan average
- Total execution time: ~1.1 hours for 12 plans
- Notable: YOLO mode + coarse granularity + parallelization = very efficient

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Commits | Phases | Key Change |
|-----------|---------|--------|------------|
| v1.0 | 106 | 4 | Initial DDD architecture with adapter pattern for core/ reuse |

### Cumulative Quality

| Milestone | Tests | LOC | Tech Debt Items |
|-----------|-------|-----|-----------------|
| v1.0 | 352+ | 20,357 | 16 |

### Top Lessons (Verified Across Milestones)

1. Wire data stores end-to-end before building consumers
2. Adapter pattern is excellent for incremental DDD migration
