# Dashboard

## Responsibility
Read-only view bounded context providing browser-based operational visibility into portfolio, pipeline, risk, and approval status. No domain layer -- this context only queries data from other contexts and renders it.

## Core Entities
- None (read-only view context -- no own domain entities)

## External Dependencies
- portfolio context (holdings, P&L, drawdown via events)
- scoring context (score results via queries)
- signals context (signal recommendations via queries)
- regime context (regime state via events)
- pipeline context (run history via queries)
- approval context (strategy approval, budget via queries)
- execution context (order fills via events)

## Key Use Cases
1. Display portfolio overview with KPI cards and holdings table
2. Show scoring/signal results in sortable heatmap table
3. Render risk dashboard with drawdown gauge and sector exposure
4. Show pipeline run history and approval management
5. Stream real-time updates via SSE (order fills, regime changes, pipeline status)

## Invariant Rules
- Dashboard is read-only -- never modifies state in other contexts
- All data access goes through application queries, never direct infrastructure imports
- SSE bridge subscribes to SyncEventBus events, does not publish
