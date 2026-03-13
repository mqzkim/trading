# Pipeline

## Responsibility

Automated pipeline scheduling and execution tracking. Manages the full screening-to-execution pipeline lifecycle: scheduling runs after market close, tracking stage-level results, persisting run history, and sending notifications.

## Core Entities

- PipelineRun: A single pipeline execution with stage-level tracking, timing, and status

## Value Objects

- PipelineStatus: Run lifecycle (running/completed/halted/failed)
- RunMode: Execution mode (auto/manual/dry_run)
- StageResult: Immutable record of a single stage's execution result

## External Dependencies

- execution context (via domain events only): SafeExecutionAdapter for order submission
- regime context (via domain events only): RegimeType for halt decisions
- portfolio context (via domain events only): DrawdownLevel for halt decisions

## Key Use Cases

1. Schedule and execute daily pipeline after market close
2. Track and persist stage-level results for each run
3. Skip weekends and NYSE holidays
4. Halt pipeline on dangerous market conditions
5. Send notifications on completion/halt/failure

## Invariant Rules

- Pipeline runs only on NYSE trading days
- Crisis regime or drawdown tier >= 2 halts before execution stage
- Dry-run mode never submits real orders
- Run history persists across process restarts
