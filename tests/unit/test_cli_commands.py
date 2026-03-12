"""Unit tests for CLI commands using Typer's test runner."""
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from cli.main import app


runner = CliRunner()


# -- Shared mock data --

def _mock_regime_result():
    return {
        "regime": "Low-Vol Bull",
        "confidence": 0.80,
        "probabilities": {"Low-Vol Bull": 0.80},
        "indicators": {"vix": 15, "sp500_vs_200ma": 1.05, "adx": 28, "yield_curve_bps": 50},
        "warning": None,
    }


def _mock_data():
    return {
        "symbol": "AAPL",
        "price": {"open": 149.0, "high": 152.0, "low": 148.0, "close": 150.0, "volume": 50_000_000},
        "indicators": {
            "ma50": 147.0, "ma200": 142.5, "rsi14": 55.0,
            "atr21": 3.5, "adx14": 28.0, "obv": 1_000_000,
            "macd": 1.2, "macd_signal": 0.8, "macd_histogram": 0.4,
        },
        "fundamentals": {"highlights": {"roe": 0.20, "pe_ratio": 18.0, "current_ratio": 2.0}, "valuation": {}},
        "history_days": 756,
    }


def _mock_signal_result():
    return {
        "skill": "signal-generate",
        "status": "success",
        "symbol": "AAPL",
        "consensus": "BULLISH",
        "agreement": 3,
        "regime_context": "Low-Vol Bull",
        "methods": {
            "canslim": {"signal": "BUY", "score": 5, "score_max": 7},
            "magic_formula": {"signal": "BUY", "score": 72, "score_max": 100},
            "dual_momentum": {"signal": "BUY", "score": 2, "score_max": 2},
            "trend_following": {"signal": "HOLD", "score": 1, "score_max": 3},
        },
        "weighted_score": 0.720,
    }


def _mock_pipeline_result():
    from core.orchestrator import PipelineResult
    return PipelineResult(
        symbol="AAPL", regime="Low-Vol Bull", regime_confidence=0.80,
        consensus="BULLISH", agreement=3, composite_score=72.5,
        safety_passed=True, position_shares=22, position_value=3300.0,
        risk_level=0,
        entry_plan={
            "symbol": "AAPL", "status": "APPROVED", "order_type": "LIMIT",
            "entry_price": 150.0, "limit_price": 149.25, "shares": 22,
            "stop_price": 139.5, "stop_distance": 10.5, "position_value": 3300.0,
            "position_pct": 3.3, "risk_pct": 0.231, "atr_multiplier": 3.0,
            "drawdown_level": 0,
        },
    )


# Patch paths — must match where the import happens (source modules, since CLI uses local imports)
_MARKET = "core.data.market"
_CLASSIFIER = "core.regime.classifier"
_WEIGHTS_MOD = "core.regime.weights"
_DATA_CLIENT = "core.data.client.DataClient"
_CONSENSUS = "core.signals.consensus"
_COMPOSITE = "core.scoring.composite"
_ORCHESTRATOR = "core.orchestrator"


# -- Tests --

class TestVersionCommand:
    def test_version_command(self):
        """'trading version' prints version string."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "v0.1.0" in result.output


class TestRegimeCommand:
    def test_regime_command_table(self):
        """'trading regime' prints regime table via DDD handler."""
        from src.shared.domain import Ok

        mock_handler = MagicMock()
        mock_handler.handle.return_value = Ok({
            "regime_type": "Bull",
            "confidence": 0.85,
            "vix": 15.0,
            "adx": 28.0,
            "yield_spread": 0.5,
            "sp500_above_ma200": True,
            "sp500_deviation_pct": 5.2,
            "detected_at": "2026-03-12T10:00:00+00:00",
            "confirmed_days": 5,
            "is_confirmed": True,
        })

        with patch("cli.main._get_ctx", return_value={"regime_handler": mock_handler}):
            result = runner.invoke(app, ["regime"])
        assert result.exit_code == 0
        assert "Bull" in result.output
        assert "VIX" in result.output

    def test_regime_command_json(self):
        """'trading regime --output json' prints valid JSON."""
        from src.shared.domain import Ok

        mock_handler = MagicMock()
        mock_handler.handle.return_value = Ok({
            "regime_type": "Bull",
            "confidence": 0.85,
            "vix": 15.0,
            "adx": 28.0,
            "yield_spread": 0.5,
            "sp500_above_ma200": True,
            "sp500_deviation_pct": 5.2,
            "detected_at": "2026-03-12T10:00:00+00:00",
            "confirmed_days": 5,
            "is_confirmed": True,
        })

        with patch("cli.main._get_ctx", return_value={"regime_handler": mock_handler}):
            result = runner.invoke(app, ["regime", "--output", "json"])
        assert result.exit_code == 0
        assert "Bull" in result.output


class TestScoreCommand:
    @patch(f"{_CLASSIFIER}.classify", return_value=_mock_regime_result())
    @patch(f"{_MARKET}.get_yield_curve_slope", return_value=50.0)
    @patch(f"{_MARKET}.get_sp500_vs_200ma", return_value=1.05)
    @patch(f"{_MARKET}.get_vix", return_value=15.0)
    def test_score_command(self, mock_vix, mock_sp, mock_yc, mock_cls):
        """'trading score AAPL' prints score table via DDD handler."""
        from src.shared.domain import Ok

        mock_handler = MagicMock()
        mock_handler.handle.return_value = Ok({
            "symbol": "AAPL", "composite_score": 72.5,
            "risk_adjusted_score": 72.5, "safety_passed": True,
            "fundamental_score": 70, "technical_score": 75,
            "sentiment_score": 50,
        })

        with patch("cli.main._get_ctx", return_value={"score_handler": mock_handler}):
            result = runner.invoke(app, ["score", "AAPL"])
        assert result.exit_code == 0
        assert "AAPL" in result.output
        assert "72.5" in result.output


class TestSignalCommand:
    def test_signal_command(self):
        """'trading signal AAPL' prints consensus signal via DDD handler."""
        from src.shared.domain import Ok

        mock_regime_handler = MagicMock()
        mock_regime_handler.handle.return_value = Ok({
            "regime_type": "Bull",
            "confidence": 0.55,
            "vix": 15.0, "adx": 28.0, "yield_spread": 0.5,
            "sp500_above_ma200": True, "sp500_deviation_pct": 5.2,
            "detected_at": "2026-03-12T10:00:00+00:00",
            "confirmed_days": 5, "is_confirmed": True,
        })

        mock_score_handler = MagicMock()
        mock_score_handler.handle.return_value = Ok({
            "symbol": "AAPL", "composite_score": 72.5,
            "risk_adjusted_score": 72.5, "safety_passed": True,
            "fundamental_score": 70, "technical_score": 75,
        })

        mock_signal_handler = MagicMock()
        mock_signal_handler.handle.return_value = Ok({
            "symbol": "AAPL", "direction": "BUY", "strength": 73.0,
            "consensus_count": 3, "methodology_count": 4,
            "composite_score": 72.5, "margin_of_safety": 0.0,
            "methodology_scores": {
                "CAN_SLIM": 75.0, "MAGIC_FORMULA": 80.0,
                "DUAL_MOMENTUM": 55.0, "TREND_FOLLOWING": 70.0,
            },
            "methodology_directions": {
                "CAN_SLIM": "BUY", "MAGIC_FORMULA": "BUY",
                "DUAL_MOMENTUM": "HOLD", "TREND_FOLLOWING": "BUY",
            },
            "strategy_weights": {
                "CAN_SLIM": 0.20, "MAGIC_FORMULA": 0.20,
                "DUAL_MOMENTUM": 0.30, "TREND_FOLLOWING": 0.30,
            },
            "reasoning_trace": "AAPL: BUY\n  Composite Score: 72.5/100",
            "regime_type": "Bull",
            "safety_passed": True,
        })

        ctx = {
            "regime_handler": mock_regime_handler,
            "score_handler": mock_score_handler,
            "signal_handler": mock_signal_handler,
        }

        with patch("cli.main._get_ctx", return_value=ctx), \
             patch("cli.main._build_signal_symbol_data", return_value={}):
            result = runner.invoke(app, ["signal", "AAPL"])
        assert result.exit_code == 0
        assert "BUY" in result.output
        assert "CAN SLIM" in result.output
        assert "Signal Consensus: AAPL" in result.output


class TestAnalyzeCommand:
    @patch(f"{_ORCHESTRATOR}.run_full_pipeline")
    def test_analyze_command(self, mock_pipeline):
        """'trading analyze AAPL' prints full analysis."""
        mock_pipeline.return_value = _mock_pipeline_result()

        result = runner.invoke(app, ["analyze", "AAPL"])
        assert result.exit_code == 0
        assert "AAPL" in result.output
        assert "Low-Vol Bull" in result.output
        assert "BULLISH" in result.output
        assert "72.5" in result.output

    @patch(f"{_ORCHESTRATOR}.run_full_pipeline")
    def test_analyze_json_output(self, mock_pipeline):
        """'trading analyze AAPL --output json' prints valid JSON."""
        mock_pipeline.return_value = _mock_pipeline_result()

        result = runner.invoke(app, ["analyze", "AAPL", "--output", "json"])
        assert result.exit_code == 0
        output = result.output
        assert "AAPL" in output
        assert "Low-Vol Bull" in output
        assert "72.5" in output
        assert "BULLISH" in output

    @patch(f"{_ORCHESTRATOR}.run_full_pipeline")
    def test_analyze_with_capital(self, mock_pipeline):
        """'trading analyze AAPL --capital 50000' passes capital correctly."""
        mock_pipeline.return_value = _mock_pipeline_result()

        result = runner.invoke(app, ["analyze", "AAPL", "--capital", "50000"])
        assert result.exit_code == 0
        mock_pipeline.assert_called_once_with("AAPL", 50000.0, "swing")
