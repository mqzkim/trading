"""Tests for the Composition Root (bootstrap)."""
from __future__ import annotations

from src.bootstrap import bootstrap
from src.shared.infrastructure.db_factory import DBFactory
from src.shared.infrastructure.sync_event_bus import SyncEventBus
from src.scoring.application.handlers import ScoreSymbolHandler


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
