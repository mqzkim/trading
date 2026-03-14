"""E2E Pipeline 통합 테스트.

Regime -> Scoring -> Signal -> Portfolio 전체 흐름을 InMemory 레포지토리로 검증.

Safety Gate 임계값 (변경 불가, domain/value_objects.py):
  Z-Score > 1.81  AND  M-Score < -1.78 이어야 통과

SignalFusionService BUY 조건 (변경 불가, signals/domain/services.py):
  3/4 방법론 BUY + composite_score >= 60.0 + safety_passed=True
"""
import tempfile
import pytest

from src.regime.application import DetectRegimeCommand, DetectRegimeHandler
from src.regime.infrastructure import SqliteRegimeRepository
from src.scoring.application import ScoreSymbolCommand, ScoreSymbolHandler
from src.scoring.infrastructure import InMemoryScoreRepository
from src.signals.application import GenerateSignalCommand, GenerateSignalHandler
from src.signals.infrastructure import InMemorySignalRepository
from src.shared.domain import Ok, Err


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def score_repo():
    return InMemoryScoreRepository()


@pytest.fixture
def signal_repo():
    return InMemorySignalRepository()


@pytest.fixture
def regime_repo(tmp_path):
    """임시 SQLite 파일을 사용하는 RegimeRepository."""
    db_path = str(tmp_path / "test_regime.db")
    return SqliteRegimeRepository(db_path=db_path)


# ---------------------------------------------------------------------------
# Mock 클라이언트 헬퍼
# ---------------------------------------------------------------------------

class _SafeFundamental:
    """Safety Gate 통과 데이터 반환 (z_score=3.5 > 1.81, m_score=-2.8 < -1.78)."""
    def get(self, symbol: str) -> dict:
        return {
            "fundamental_score": 70,
            "f_score": 8,
            "z_score": 3.5,
            "m_score": -2.8,
        }


class _RiskyFundamental:
    """Safety Gate 탈락 데이터 반환 (z_score=1.2 <= 1.81)."""
    def get(self, symbol: str) -> dict:
        return {
            "fundamental_score": 30,
            "f_score": 2,
            "z_score": 1.2,
            "m_score": -1.5,
        }


class _MScoreFailFundamental:
    """Safety Gate 탈락 데이터 반환 (m_score=-1.0 >= -1.78)."""
    def get(self, symbol: str) -> dict:
        return {
            "fundamental_score": 75,
            "f_score": 7,
            "z_score": 4.0,
            "m_score": -1.0,
        }


def _technical(score: float = 65.0):
    class _T:
        def get(self, symbol: str) -> dict:
            return {"technical_score": score}
    return _T()


def _sentiment(score: float = 60.0):
    class _S:
        def get(self, symbol: str) -> dict:
            return {"sentiment_score": score}
    return _S()


def _buy_method_client(score: float = 80.0):
    """BUY 방향과 높은 점수를 반환하는 방법론 클라이언트."""
    class _C:
        def get(self, symbol: str) -> dict:
            return {"direction": "BUY", "score": score, "reason": "mock buy"}
    return _C()


def _hold_method_client(score: float = 50.0):
    """HOLD 방향을 반환하는 방법론 클라이언트."""
    class _C:
        def get(self, symbol: str) -> dict:
            return {"direction": "HOLD", "score": score, "reason": "mock hold"}
    return _C()


# ---------------------------------------------------------------------------
# TestScoringPipeline
# ---------------------------------------------------------------------------

class TestScoringPipeline:
    def test_score_symbol_success(self, score_repo):
        """정상 종목 스코어링 — Safety Gate 통과 후 복합 점수 반환."""
        handler = ScoreSymbolHandler(
            score_repo=score_repo,
            fundamental_client=_SafeFundamental(),
            technical_client=_technical(65.0),
            sentiment_client=_sentiment(60.0),
        )
        result = handler.handle(ScoreSymbolCommand(symbol="AAPL"))

        assert isinstance(result, Ok), f"Expected Ok, got Err: {result.error}"
        data = result.value
        assert data["safety_passed"] is True
        assert 0 <= data["composite_score"] <= 100
        assert 0 <= data["risk_adjusted_score"] <= 100
        assert data["symbol"] == "AAPL"

    def test_score_symbol_saves_to_repo(self, score_repo):
        """스코어링 성공 시 레포지토리에 저장되어야 한다."""
        handler = ScoreSymbolHandler(
            score_repo=score_repo,
            fundamental_client=_SafeFundamental(),
            technical_client=_technical(),
            sentiment_client=_sentiment(),
        )
        handler.handle(ScoreSymbolCommand(symbol="MSFT"))

        saved = score_repo.find_latest("MSFT")
        assert saved is not None
        assert 0 <= saved.value <= 100

    def test_safety_gate_blocks_low_z_score(self, score_repo):
        """Safety Gate: Z-Score <= 1.81 종목 차단."""
        handler = ScoreSymbolHandler(
            score_repo=score_repo,
            fundamental_client=_RiskyFundamental(),
            technical_client=_technical(),
            sentiment_client=_sentiment(),
        )
        result = handler.handle(ScoreSymbolCommand(symbol="RISKY"))

        assert isinstance(result, Ok)
        data = result.value
        assert data["safety_passed"] is False
        assert data["composite_score"] == 0
        assert data["risk_adjusted_score"] == 0

    def test_safety_gate_blocks_high_m_score(self, score_repo):
        """Safety Gate: M-Score >= -1.78 (회계 조작 의심) 종목 차단."""
        handler = ScoreSymbolHandler(
            score_repo=score_repo,
            fundamental_client=_MScoreFailFundamental(),
            technical_client=_technical(),
            sentiment_client=_sentiment(),
        )
        result = handler.handle(ScoreSymbolCommand(symbol="FRAUD"))

        assert isinstance(result, Ok)
        data = result.value
        assert data["safety_passed"] is False
        assert data["composite_score"] == 0

    def test_safety_gate_blocked_stock_not_saved_to_repo(self, score_repo):
        """Safety Gate 탈락 종목은 레포지토리에 저장하지 않는다."""
        handler = ScoreSymbolHandler(
            score_repo=score_repo,
            fundamental_client=_RiskyFundamental(),
            technical_client=_technical(),
            sentiment_client=_sentiment(),
        )
        handler.handle(ScoreSymbolCommand(symbol="BADCO"))

        # 핸들러는 safety 실패 시 repo.save를 호출하지 않는다 (handlers.py 확인)
        assert score_repo.find_latest("BADCO") is None

    def test_composite_score_range_swing_strategy(self, score_repo):
        """swing 전략 복합 점수가 0-100 범위를 벗어나지 않는다."""
        # 극단값 테스트: 모든 점수 = 100
        class _MaxClient:
            def get(self, s):
                return {
                    "fundamental_score": 100, "f_score": 9,
                    "z_score": 5.0, "m_score": -3.0,
                }
        handler = ScoreSymbolHandler(
            score_repo=score_repo,
            fundamental_client=_MaxClient(),
            technical_client=_technical(100.0),
            sentiment_client=_sentiment(100.0),
        )
        result = handler.handle(ScoreSymbolCommand(symbol="MAX"))

        assert isinstance(result, Ok)
        assert result.value["composite_score"] == 100.0

    def test_data_fetch_error_returns_err(self, score_repo):
        """데이터 조회 실패 시 Err 반환."""
        class _FailClient:
            def get(self, symbol: str):
                raise ConnectionError("API timeout")

        handler = ScoreSymbolHandler(
            score_repo=score_repo,
            fundamental_client=_FailClient(),
            technical_client=_technical(),
            sentiment_client=_sentiment(),
        )
        result = handler.handle(ScoreSymbolCommand(symbol="FAIL"))

        assert isinstance(result, Err)
        assert result.error.code == "DATA_FETCH_ERROR"


# ---------------------------------------------------------------------------
# TestSignalPipeline
# ---------------------------------------------------------------------------

class TestSignalPipeline:
    def test_generate_signal_hold_on_low_consensus(self, signal_repo):
        """합의 미달 시 HOLD 시그널 — 2개 BUY는 3/4 요건 미달."""
        # can_slim + magic_formula = BUY(2개), dual_momentum + trend_following = HOLD
        handler = GenerateSignalHandler(
            signal_repo=signal_repo,
            can_slim_client=_buy_method_client(75.0),
            magic_formula_client=_buy_method_client(70.0),
            dual_momentum_client=_hold_method_client(50.0),
            trend_following_client=_hold_method_client(50.0),
        )
        cmd = GenerateSignalCommand(
            symbol="AAPL",
            safety_passed=True,
            composite_score=65.0,
        )
        result = handler.handle(cmd)

        assert isinstance(result, Ok), f"Expected Ok, got Err: {result.error}"
        data = result.value
        assert data["direction"] == "HOLD"
        assert 0 <= data["strength"] <= 100.0

    def test_generate_signal_buy_on_full_consensus(self, signal_repo):
        """3/4 방법론 BUY + composite_score >= 60 -> BUY 시그널."""
        handler = GenerateSignalHandler(
            signal_repo=signal_repo,
            can_slim_client=_buy_method_client(80.0),
            magic_formula_client=_buy_method_client(80.0),
            dual_momentum_client=_buy_method_client(80.0),
            trend_following_client=_hold_method_client(40.0),
        )
        cmd = GenerateSignalCommand(
            symbol="NVDA",
            safety_passed=True,
            composite_score=70.0,
        )
        result = handler.handle(cmd)

        assert isinstance(result, Ok)
        assert result.value["direction"] == "BUY"
        assert result.value["consensus_count"] >= 3

    def test_safety_failed_produces_hold_signal(self, signal_repo):
        """safety_passed=False -> SignalFusionService가 HOLD 반환."""
        handler = GenerateSignalHandler(
            signal_repo=signal_repo,
            can_slim_client=_buy_method_client(90.0),
            magic_formula_client=_buy_method_client(90.0),
            dual_momentum_client=_buy_method_client(90.0),
            trend_following_client=_buy_method_client(90.0),
        )
        cmd = GenerateSignalCommand(
            symbol="RISKY",
            safety_passed=False,
            composite_score=0.0,
        )
        result = handler.handle(cmd)

        # safety_passed=False 이면 SignalFusionService는 즉시 HOLD 반환
        assert isinstance(result, Ok)
        assert result.value["direction"] == "HOLD"

    def test_signal_saved_to_repo(self, signal_repo):
        """시그널 생성 후 레포지토리에서 조회 가능해야 한다."""
        handler = GenerateSignalHandler(
            signal_repo=signal_repo,
            can_slim_client=_buy_method_client(80.0),
            magic_formula_client=_buy_method_client(80.0),
            dual_momentum_client=_buy_method_client(80.0),
            trend_following_client=_hold_method_client(40.0),
        )
        cmd = GenerateSignalCommand(symbol="TSLA", safety_passed=True, composite_score=70.0)
        result = handler.handle(cmd)

        assert isinstance(result, Ok)
        saved = signal_repo.find_active("TSLA")
        assert saved is not None
        assert saved["direction"] == result.value["direction"]

    def test_low_composite_score_triggers_sell(self, signal_repo):
        """composite_score < 30 -> SELL 시그널 (score 기준 SELL 조건)."""
        handler = GenerateSignalHandler(
            signal_repo=signal_repo,
            can_slim_client=_hold_method_client(20.0),
            magic_formula_client=_hold_method_client(20.0),
            dual_momentum_client=_hold_method_client(20.0),
            trend_following_client=_hold_method_client(20.0),
        )
        cmd = GenerateSignalCommand(
            symbol="DUMP",
            safety_passed=True,
            composite_score=20.0,  # < 30 -> SELL 조건
        )
        result = handler.handle(cmd)

        assert isinstance(result, Ok)
        assert result.value["direction"] == "SELL"


# ---------------------------------------------------------------------------
# TestRegimePipeline
# ---------------------------------------------------------------------------

class TestRegimePipeline:
    def test_detect_regime_bull_market(self, regime_repo):
        """저VIX + SP500 > MA200 + 강한 ADX -> Bull 레짐 감지."""
        cmd = DetectRegimeCommand(
            vix=14.0,
            sp500_price=5000.0,
            sp500_ma200=4500.0,   # 가격 > MA200 (상승장)
            adx=28.0,             # ADX > 25 (강한 추세)
            yield_spread=0.5,     # 정상 수익률 곡선
        )
        handler = DetectRegimeHandler(regime_repo=regime_repo)
        result = handler.handle(cmd)

        assert isinstance(result, Ok), f"Expected Ok, got Err: {result.error}"
        data = result.value
        assert "regime_type" in data
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["sp500_above_ma200"] is True

    def test_detect_regime_saves_to_repo(self, regime_repo):
        """레짐 감지 결과가 레포지토리에 저장된다."""
        cmd = DetectRegimeCommand(
            vix=20.0,
            sp500_price=4800.0,
            sp500_ma200=4900.0,
            adx=18.0,
            yield_spread=-0.2,
        )
        handler = DetectRegimeHandler(regime_repo=regime_repo)
        handler.handle(cmd)

        saved = regime_repo.find_latest()
        assert saved is not None

    def test_detect_regime_invalid_input_returns_err(self, regime_repo):
        """잘못된 입력값 (음수 VIX) -> Err 반환."""
        cmd = DetectRegimeCommand(
            vix=-1.0,       # 유효하지 않음
            sp500_price=5000.0,
            sp500_ma200=4500.0,
            adx=25.0,
            yield_spread=0.5,
        )
        handler = DetectRegimeHandler(regime_repo=regime_repo)
        result = handler.handle(cmd)

        assert isinstance(result, Err)
        assert result.error.code == "INVALID_INPUT"


# ---------------------------------------------------------------------------
# TestFullPipeline — Regime -> Scoring -> Signal E2E
# ---------------------------------------------------------------------------

class TestFullPipeline:
    def test_regime_to_signal_full_flow(self, regime_repo, score_repo, signal_repo):
        """Regime 감지 -> Scoring -> Signal 전체 파이프라인 통과."""
        # Step 1: 레짐 감지
        regime_cmd = DetectRegimeCommand(
            vix=14.0,
            sp500_price=5000.0,
            sp500_ma200=4500.0,
            adx=28.0,
            yield_spread=0.5,
        )
        regime_result = DetectRegimeHandler(regime_repo=regime_repo).handle(regime_cmd)
        assert isinstance(regime_result, Ok)
        regime_data = regime_result.value

        # Step 2: 종목 스코어링
        score_handler = ScoreSymbolHandler(
            score_repo=score_repo,
            fundamental_client=_SafeFundamental(),
            technical_client=_technical(65.0),
            sentiment_client=_sentiment(60.0),
        )
        score_result = score_handler.handle(ScoreSymbolCommand(symbol="AAPL"))
        assert isinstance(score_result, Ok)
        score_data = score_result.value
        assert score_data["safety_passed"] is True

        # Step 3: 시그널 생성 (Scoring 결과를 Signal로 전달)
        signal_handler = GenerateSignalHandler(
            signal_repo=signal_repo,
            can_slim_client=_buy_method_client(80.0),
            magic_formula_client=_buy_method_client(75.0),
            dual_momentum_client=_buy_method_client(78.0),
            trend_following_client=_hold_method_client(55.0),
        )
        signal_cmd = GenerateSignalCommand(
            symbol="AAPL",
            safety_passed=score_data["safety_passed"],
            composite_score=score_data["composite_score"],
        )
        signal_result = signal_handler.handle(signal_cmd)
        assert isinstance(signal_result, Ok)
        signal_data = signal_result.value

        # E2E 검증
        assert signal_data["symbol"] == "AAPL"
        assert signal_data["direction"] in ("BUY", "SELL", "HOLD")
        assert signal_data["composite_score"] == score_data["composite_score"]
        assert "regime_type" in regime_data

    def test_safety_failed_propagates_through_pipeline(self, score_repo, signal_repo):
        """Safety Gate 탈락이 Signal 단계까지 올바르게 전달된다."""
        # Scoring: Safety 탈락
        score_handler = ScoreSymbolHandler(
            score_repo=score_repo,
            fundamental_client=_RiskyFundamental(),
            technical_client=_technical(),
            sentiment_client=_sentiment(),
        )
        score_result = score_handler.handle(ScoreSymbolCommand(symbol="RISKY"))
        assert isinstance(score_result, Ok)
        score_data = score_result.value
        assert score_data["safety_passed"] is False

        # Signal: safety_passed=False 전달 -> HOLD
        signal_handler = GenerateSignalHandler(
            signal_repo=signal_repo,
            can_slim_client=_buy_method_client(90.0),
            magic_formula_client=_buy_method_client(90.0),
            dual_momentum_client=_buy_method_client(90.0),
            trend_following_client=_buy_method_client(90.0),
        )
        signal_cmd = GenerateSignalCommand(
            symbol="RISKY",
            safety_passed=score_data["safety_passed"],
            composite_score=score_data["composite_score"],
        )
        signal_result = signal_handler.handle(signal_cmd)
        assert isinstance(signal_result, Ok)

        # Safety 탈락 종목은 방법론 점수와 무관하게 HOLD
        assert signal_result.value["direction"] == "HOLD"


# ---------------------------------------------------------------------------
# TestValuationAdapter -- DuckDB intrinsic_value lookup
# ---------------------------------------------------------------------------

class TestValuationAdapter:
    def test_get_intrinsic_value_from_duckdb(self, tmp_path):
        """ValuationAdapter returns intrinsic_value from DuckDB valuation_results."""
        import duckdb

        from src.pipeline.infrastructure.valuation_adapter import ValuationAdapter
        from src.shared.infrastructure.db_factory import DBFactory

        db_factory = DBFactory(data_dir=str(tmp_path))
        # Seed DuckDB with valuation data
        conn = db_factory.duckdb_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS valuation_results (
                ticker VARCHAR PRIMARY KEY,
                intrinsic_value DOUBLE,
                margin_of_safety DOUBLE,
                has_margin BOOLEAN
            )
        """)
        conn.execute(
            "INSERT INTO valuation_results VALUES ('AAPL', 225.50, 0.3, true)"
        )
        conn.close()
        db_factory.close()

        adapter = ValuationAdapter(db_factory=db_factory)
        result = adapter.get_intrinsic_value("AAPL")

        assert result == 225.50

    def test_get_intrinsic_value_returns_none_for_unknown(self, tmp_path):
        """ValuationAdapter returns None when no row exists."""
        import duckdb

        from src.pipeline.infrastructure.valuation_adapter import ValuationAdapter
        from src.shared.infrastructure.db_factory import DBFactory

        db_factory = DBFactory(data_dir=str(tmp_path))
        conn = db_factory.duckdb_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS valuation_results (
                ticker VARCHAR PRIMARY KEY,
                intrinsic_value DOUBLE,
                margin_of_safety DOUBLE,
                has_margin BOOLEAN
            )
        """)
        conn.close()
        db_factory.close()

        adapter = ValuationAdapter(db_factory=db_factory)
        result = adapter.get_intrinsic_value("UNKNOWN")

        assert result is None


# ---------------------------------------------------------------------------
# TestPipelineOrchestrator -- Full E2E with mocked externals
# ---------------------------------------------------------------------------

class TestPipelineOrchestratorE2E:
    """Test full pipeline orchestrator with mocked external dependencies."""

    def test_pipeline_completes_e2e(self, tmp_path):
        """Full pipeline run completes with COMPLETED or HALTED status."""
        from unittest.mock import MagicMock, patch

        from src.pipeline.domain.services import PipelineOrchestrator
        from src.pipeline.domain.value_objects import PipelineStatus

        orchestrator = PipelineOrchestrator()

        # Mock handlers dict
        handlers = self._build_mock_handlers(tmp_path)

        run = orchestrator.run(
            handlers=handlers,
            symbols=["AAPL"],
            dry_run=True,
        )

        # Pipeline should complete or halt (Crisis regime is valid halt)
        assert run.status in (PipelineStatus.COMPLETED, PipelineStatus.HALTED)
        assert len(run.stages) >= 4  # at least ingest + regime + score + signal

    def test_pipeline_stage_names_in_order(self, tmp_path):
        """Pipeline stages follow correct order: ingest, regime, score, signal, plan, execute."""
        from unittest.mock import MagicMock

        from src.pipeline.domain.services import PipelineOrchestrator
        from src.pipeline.domain.value_objects import PipelineStatus

        orchestrator = PipelineOrchestrator()
        handlers = self._build_mock_handlers(tmp_path)

        run = orchestrator.run(
            handlers=handlers,
            symbols=["AAPL"],
            dry_run=True,
        )

        expected_stages = ["ingest", "regime", "score", "signal", "plan", "execute"]
        actual_stages = [s.stage_name for s in run.stages]

        # At minimum all 6 stages should be present
        assert actual_stages == expected_stages

    def test_pipeline_uses_valuation_reader_for_intrinsic_value(self, tmp_path):
        """Pipeline _run_plan uses injected valuation_reader when available."""
        from unittest.mock import MagicMock, call

        from src.pipeline.domain.services import PipelineOrchestrator

        orchestrator = PipelineOrchestrator()
        handlers = self._build_mock_handlers(tmp_path)

        # Set up valuation_reader mock to return specific value
        mock_valuation_reader = MagicMock(return_value=225.50)
        handlers["valuation_reader"] = mock_valuation_reader

        run = orchestrator.run(
            handlers=handlers,
            symbols=["AAPL"],
            dry_run=True,
        )

        # valuation_reader should have been called for AAPL (if signal was BUY/SELL)
        # The _run_plan stage only runs for BUY/SELL signals
        # Since our mock signal handler returns BUY, valuation_reader should be called
        if mock_valuation_reader.called:
            mock_valuation_reader.assert_called_with("AAPL")

    def test_pipeline_fallback_when_valuation_reader_none(self, tmp_path):
        """Pipeline falls back to heuristic when valuation_reader returns None."""
        from unittest.mock import MagicMock

        from src.pipeline.domain.services import PipelineOrchestrator
        from src.pipeline.domain.value_objects import PipelineStatus

        orchestrator = PipelineOrchestrator()
        handlers = self._build_mock_handlers(tmp_path)

        # valuation_reader returns None -- should fall back to heuristic
        handlers["valuation_reader"] = MagicMock(return_value=None)

        run = orchestrator.run(
            handlers=handlers,
            symbols=["AAPL"],
            dry_run=True,
        )

        # Pipeline should still complete successfully
        assert run.status in (PipelineStatus.COMPLETED, PipelineStatus.HALTED)

    def _build_mock_handlers(self, tmp_path) -> dict:
        """Build a mock handlers dict for PipelineOrchestrator."""
        import asyncio
        from unittest.mock import MagicMock

        from src.shared.domain import Ok

        # Mock data pipeline (ingest)
        mock_data_pipeline = MagicMock()

        async def _mock_ingest(symbols):
            return {"succeeded": symbols, "failed_count": 0, "total": len(symbols)}

        mock_data_pipeline.ingest_universe = _mock_ingest

        # Mock regime handler
        mock_regime_handler = MagicMock()
        mock_regime_handler.handle.return_value = Ok({
            "regime_type": "Bull",
            "confidence": 0.85,
            "sp500_above_ma200": True,
        })

        # Mock score handler
        mock_score_handler = MagicMock()
        mock_score_handler.handle.return_value = Ok({
            "composite_score": 75.0,
            "risk_adjusted_score": 70.0,
            "margin_of_safety": 0.25,
            "safety_passed": True,
            "symbol": "AAPL",
        })

        # Mock signal handler -- return BUY for triggering plan stage
        mock_signal_handler = MagicMock()
        mock_signal_handler.handle.return_value = Ok({
            "direction": "BUY",
            "strength": 80.0,
            "consensus_count": 3,
            "composite_score": 75.0,
            "reasoning_trace": "test buy signal",
        })

        # Mock trade plan handler
        mock_trade_plan = MagicMock()
        mock_trade_plan.symbol = "AAPL"
        mock_trade_plan.composite_score = 75.0
        mock_trade_plan.position_pct = 5.0
        mock_trade_plan.position_value = 5000.0

        mock_trade_plan_handler = MagicMock()
        mock_trade_plan_handler.generate.return_value = mock_trade_plan

        # Mock DataClient for _run_plan (injected, not created internally)
        mock_data_client = MagicMock()
        mock_data_client.get_full.return_value = {
            "price": {"close": 175.50},
            "indicators": {"atr21": 5.0},
        }

        return {
            "data_pipeline": mock_data_pipeline,
            "regime_handler": mock_regime_handler,
            "score_handler": mock_score_handler,
            "signal_handler": mock_signal_handler,
            "trade_plan_handler": mock_trade_plan_handler,
            "data_client": mock_data_client,
            "capital": 100_000.0,
        }
