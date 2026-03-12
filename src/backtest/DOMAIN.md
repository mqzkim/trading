# Backtest

## Responsibility

Walk-forward backtesting and strategy validation. Runs in-sample/out-of-sample splits, computes performance metrics (including profit factor), and persists results for historical comparison.

## Core Entities

- BacktestConfig: Configuration for a single backtest (symbol, capital)
- WalkForwardConfig: Configuration for walk-forward validation (splits, train ratio)
- PerformanceReport: 8-field metrics VO (cagr, sharpe, drawdown, win rate, total return, trades, avg return, profit factor)

## External Dependencies

- signals context (via events) -- receives signal series for backtesting
- scoring context (via events) -- receives composite scores for strategy evaluation

## Key Use Cases

1. Run single backtest on symbol with OHLCV data and signal series
2. Run walk-forward validation with N folds producing IS/OOS metrics and overfitting score
3. Generate performance report with profit factor enrichment
4. Persist results to DuckDB for historical comparison

## Invariant Rules

- Profit factor is computed in domain service (never modify core/backtest/metrics.py)
- Walk-forward validation requires minimum 2 splits
- CoreBacktestAdapter is a thin wrapper -- no math rewriting
- All core math delegated to core/backtest/ through adapter pattern
