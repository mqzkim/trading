"""Tests for the Composition Root (bootstrap)."""
from __future__ import annotations

from src.bootstrap import bootstrap
from src.shared.infrastructure.db_factory import DBFactory
from src.shared.infrastructure.sync_event_bus import SyncEventBus
from src.scoring.application.handlers import ScoreSymbolHandler
from src.execution.domain.value_objects import ExecutionMode
from src.execution.infrastructure.alpaca_adapter import AlpacaExecutionAdapter
from src.execution.infrastructure.kis_adapter import KisExecutionAdapter
from src.execution.infrastructure.safe_adapter import SafeExecutionAdapter


class TestBootstrap:
    def test_returns_dict_with_required_keys(self, tmp_path) -> None:
        factory = DBFactory(data_dir=str(tmp_path))
        ctx = bootstrap(db_factory=factory)
        assert "bus" in ctx
        assert "db_factory" in ctx
        assert "score_handler" in ctx
        factory.close()

    def test_uses_custom_db_factory(self, tmp_path) -> None:
        factory = DBFactory(data_dir=str(tmp_path))
        ctx = bootstrap(db_factory=factory)
        assert ctx["db_factory"] is factory
        factory.close()

    def test_bus_is_sync_event_bus(self, tmp_path) -> None:
        factory = DBFactory(data_dir=str(tmp_path))
        ctx = bootstrap(db_factory=factory)
        assert isinstance(ctx["bus"], SyncEventBus)
        factory.close()

    def test_score_handler_is_correct_type(self, tmp_path) -> None:
        factory = DBFactory(data_dir=str(tmp_path))
        ctx = bootstrap(db_factory=factory)
        assert isinstance(ctx["score_handler"], ScoreSymbolHandler)
        factory.close()

    def test_independent_contexts(self, tmp_path) -> None:
        factory1 = DBFactory(data_dir=str(tmp_path / "a"))
        factory2 = DBFactory(data_dir=str(tmp_path / "b"))
        ctx1 = bootstrap(db_factory=factory1)
        ctx2 = bootstrap(db_factory=factory2)
        assert ctx1["bus"] is not ctx2["bus"]
        assert ctx1["score_handler"] is not ctx2["score_handler"]
        factory1.close()
        factory2.close()

    def test_default_factory_when_none(self, tmp_path, monkeypatch) -> None:
        """When no db_factory is passed, bootstrap creates a default one."""
        # Monkeypatch to use tmp_path as default data dir
        monkeypatch.chdir(tmp_path)
        ctx = bootstrap()
        assert isinstance(ctx["db_factory"], DBFactory)
        ctx["db_factory"].close()

    def test_bootstrap_kr(self, tmp_path) -> None:
        """bootstrap(market='kr') injects KisExecutionAdapter and KR_CAPITAL."""
        factory = DBFactory(data_dir=str(tmp_path))
        ctx = bootstrap(db_factory=factory, market="kr")
        handler = ctx["trade_plan_handler"]
        assert isinstance(handler._adapter, KisExecutionAdapter)
        assert ctx["market"] == "kr"
        assert ctx["capital"] > 0  # KR_CAPITAL default is 10_000_000
        factory.close()

    def test_bootstrap_us(self, tmp_path) -> None:
        """bootstrap(market='us') wraps AlpacaExecutionAdapter with SafeExecutionAdapter."""
        factory = DBFactory(data_dir=str(tmp_path))
        ctx = bootstrap(db_factory=factory, market="us")
        handler = ctx["trade_plan_handler"]
        assert isinstance(handler._adapter, SafeExecutionAdapter)
        assert isinstance(handler._adapter._inner, AlpacaExecutionAdapter)
        assert ctx["market"] == "us"
        assert ctx["capital"] > 0  # US_CAPITAL default is 100_000
        assert ctx["execution_mode"] == ExecutionMode.PAPER
        assert ctx["cooldown_repo"] is not None
        factory.close()

    def test_bootstrap_default_is_us(self, tmp_path) -> None:
        """Default market parameter is 'us' for backward compatibility."""
        factory = DBFactory(data_dir=str(tmp_path))
        ctx = bootstrap(db_factory=factory)
        assert isinstance(ctx["trade_plan_handler"]._adapter, SafeExecutionAdapter)
        assert ctx["market"] == "us"
        factory.close()
