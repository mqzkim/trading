"""Performance infrastructure -- DuckDB repositories, event handlers."""
from .duckdb_trade_repository import DuckDBTradeHistoryRepository
from .duckdb_proposal_repository import DuckDBProposalRepository
from .trade_persistence_handler import TradePersistenceHandler

__all__ = [
    "DuckDBTradeHistoryRepository",
    "DuckDBProposalRepository",
    "TradePersistenceHandler",
]
