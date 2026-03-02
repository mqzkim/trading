"""Unit tests for core/orchestrator.py"""
import pytest
from unittest.mock import patch, MagicMock
from core.orchestrator import run_full_pipeline, run_quick_scan, PipelineResult


# -- Fixtures / Helpers --

def _mock_data(symbol="AAPL", close=150.0, atr=3.5, adx=28.0):
    """Return a mock DataClient.get_full() result."""
    return {
        "symbol": symbol,
        "price": {"open": 149.0, "high": 152.0, "low": 148.0, "close": close, "volume": 50_000_000},
        "indicators": {
            "ma50": close * 0.98,
            "ma200": close * 0.95,
            "rsi14": 55.0,
            "atr21": atr,
            "adx14": adx,
            "obv": 1_000_000,
            "macd": 1.2,
            "macd_signal": 0.8,
            "macd_histogram": 0.4,
        },
        "fundamentals": {
            "highlights": {
                "roe": 0.20,
                "pe_ratio": 18.0,
                "current_ratio": 2.0,
            },
            "valuation": {},
        },
        "history_days": 756,
    }


def _mock_regime(regime="Low-Vol Bull", confidence=0.80):
    return {
        "regime": regime,
        "confidence": confidence,
        "probabilities": {regime: confidence},
        "indicators": {"vix": 15, "sp500_vs_200ma": 1.05, "adx": 28, "yield_curve_bps": 50},
        "warning": None,
    }


def _mock_signal_result(consensus="BULLISH", agreement=3):
    return {
        "skill": "signal-generate",
        "status": "success",
        "symbol": "AAPL",
        "consensus": consensus,
        "agreement": agreement,
        "regime_context": "Low-Vol Bull",
        "methods": {
            "canslim": {"signal": "BUY", "score": 5, "score_max": 7},
            "magic_formula": {"signal": "BUY", "score": 72, "score_max": 100},
            "dual_momentum": {"signal": "BUY", "score": 2, "score_max": 2},
            "trend_following": {"signal": "HOLD", "score": 1, "score_max": 3},
        },
        "weighted_score": 0.72,
    }


def _mock_entry_plan(status="APPROVED"):
    return {
        "symbol": "AAPL",
        "status": status,
        "order_type": "LIMIT",
        "entry_price": 150.0,
        "limit_price": 149.25,
        "shares": 22,
        "stop_price": 139.5,
        "stop_distance": 10.5,
        "position_value": 3300.0,
        "position_pct": 3.3,
        "risk_pct": 0.231,
        "atr_multiplier": 3.0,
        "drawdown_level": 0,
    }


# Module paths for patching
_DATA_CLIENT = "core.orchestrator.DataClient"
_GET_VIX = "core.orchestrator.get_vix"
_GET_SP500 = "core.orchestrator.get_sp500_vs_200ma"
_GET_YIELD = "core.orchestrator.get_yield_curve_slope"
_CLASSIFY = "core.orchestrator.classify"
_GEN_SIGNALS = "core.orchestrator.generate_signals"
_SCORE_SYMBOL = "core.orchestrator.score_symbol"
_CHECK_ENTRY = "core.orchestrator.check_entry_allowed"
_ATR_SIZE = "core.orchestrator.atr_position_size"
_VALIDATE_POS = "core.orchestrator.validate_position"
_PLAN_ENTRY = "core.orchestrator.plan_entry"
_RISK_ADJ = "core.orchestrator.get_risk_adjustment"
_FULL_RISK = "core.orchestrator.full_risk_check"


class TestPipelineResult:
    def test_pipeline_result_structure(self):
        """PipelineResult has all required fields."""
        result = PipelineResult(
            symbol="AAPL", regime="Low-Vol Bull", regime_confidence=0.8,
            consensus="BULLISH", agreement=3, composite_score=72.5,
            safety_passed=True, position_shares=22, position_value=3300.0,
            risk_level=0, entry_plan={"status": "APPROVED"},
        )
        assert result.symbol == "AAPL"
        assert result.regime == "Low-Vol Bull"
        assert result.regime_confidence == 0.8
        assert result.consensus == "BULLISH"
        assert result.agreement == 3
        assert result.composite_score == 72.5
        assert result.safety_passed is True
        assert result.position_shares == 22
        assert result.position_value == 3300.0
        assert result.risk_level == 0
        assert result.entry_plan == {"status": "APPROVED"}
        assert result.warnings == []
        assert result.error is None

    def test_pipeline_result_defaults(self):
        """Default fields are correct."""
        result = PipelineResult(
            symbol="X", regime="T", regime_confidence=0.5,
            consensus="NEUTRAL", agreement=0, composite_score=0.0,
            safety_passed=False, position_shares=0, position_value=0.0,
            risk_level=0, entry_plan={},
        )
        assert result.warnings == []
        assert result.error is None


class TestRunFullPipeline:
    @patch(_PLAN_ENTRY, return_value=_mock_entry_plan())
    @patch(_VALIDATE_POS, return_value={"passed": True, "violations": []})
    @patch(_ATR_SIZE, return_value={"shares": 22, "position_value": 3300.0, "stop_price": 139.5})
    @patch(_RISK_ADJ, return_value=1.0)
    @patch(_CHECK_ENTRY, return_value={"allowed": True, "drawdown_level": 0, "drawdown_pct": 0.0, "reason": "normal"})
    @patch(_SCORE_SYMBOL, return_value={"composite_score": 72.5, "risk_adjusted_score": 72.5, "safety_passed": True, "symbol": "AAPL", "fundamental_score": 70, "technical_score": 75, "sentiment_score": 50})
    @patch(_GEN_SIGNALS, return_value=_mock_signal_result())
    @patch(_CLASSIFY, return_value=_mock_regime())
    @patch(_GET_YIELD, return_value=50.0)
    @patch(_GET_SP500, return_value=1.05)
    @patch(_GET_VIX, return_value=15.0)
    @patch(_DATA_CLIENT)
    def test_run_full_pipeline_returns_result(
        self, mock_dc, mock_vix, mock_sp, mock_yc, mock_cls, mock_sig,
        mock_score, mock_entry, mock_radj, mock_atr, mock_vp, mock_plan,
    ):
        """Full pipeline returns a complete PipelineResult."""
        mock_instance = MagicMock()
        mock_instance.get_full.return_value = _mock_data()
        mock_dc.return_value = mock_instance

        result = run_full_pipeline("AAPL", capital=100_000.0)

        assert isinstance(result, PipelineResult)
        assert result.symbol == "AAPL"
        assert result.regime == "Low-Vol Bull"
        assert result.consensus == "BULLISH"
        assert result.composite_score == 72.5
        assert result.position_shares == 22
        assert result.error is None

    @patch(_PLAN_ENTRY, return_value=_mock_entry_plan())
    @patch(_VALIDATE_POS, return_value={"passed": True, "violations": []})
    @patch(_ATR_SIZE, return_value={"shares": 22, "position_value": 3300.0, "stop_price": 139.5})
    @patch(_RISK_ADJ, return_value=1.0)
    @patch(_CHECK_ENTRY, return_value={"allowed": True, "drawdown_level": 0, "drawdown_pct": 0.0, "reason": "normal"})
    @patch(_SCORE_SYMBOL, return_value={"composite_score": 72.5, "risk_adjusted_score": 72.5, "safety_passed": True, "symbol": "AAPL", "fundamental_score": 70, "technical_score": 75, "sentiment_score": 50})
    @patch(_GEN_SIGNALS, return_value=_mock_signal_result("BULLISH", 3))
    @patch(_CLASSIFY, return_value=_mock_regime("Low-Vol Bull", 0.80))
    @patch(_GET_YIELD, return_value=50.0)
    @patch(_GET_SP500, return_value=1.05)
    @patch(_GET_VIX, return_value=15.0)
    @patch(_DATA_CLIENT)
    def test_pipeline_bullish_regime(
        self, mock_dc, mock_vix, mock_sp, mock_yc, mock_cls, mock_sig,
        mock_score, mock_entry, mock_radj, mock_atr, mock_vp, mock_plan,
    ):
        """Low-Vol Bull regime yields BULLISH signal when signals agree."""
        mock_instance = MagicMock()
        mock_instance.get_full.return_value = _mock_data()
        mock_dc.return_value = mock_instance

        result = run_full_pipeline("AAPL")
        assert result.regime == "Low-Vol Bull"
        assert result.consensus == "BULLISH"
        assert result.agreement == 3

    @patch(_PLAN_ENTRY, return_value=_mock_entry_plan())
    @patch(_VALIDATE_POS, return_value={"passed": True, "violations": []})
    @patch(_ATR_SIZE, return_value={"shares": 5, "position_value": 750.0, "stop_price": 120.0})
    @patch(_RISK_ADJ, return_value=0.3)
    @patch(_CHECK_ENTRY, return_value={"allowed": True, "drawdown_level": 0, "drawdown_pct": 0.0, "reason": "normal"})
    @patch(_SCORE_SYMBOL, return_value={"composite_score": 35.0, "risk_adjusted_score": 30.0, "safety_passed": True, "symbol": "AAPL", "fundamental_score": 40, "technical_score": 30, "sentiment_score": 50})
    @patch(_GEN_SIGNALS, return_value=_mock_signal_result("BEARISH", 3))
    @patch(_CLASSIFY, return_value=_mock_regime("High-Vol Bear", 0.70))
    @patch(_GET_YIELD, return_value=-50.0)
    @patch(_GET_SP500, return_value=0.92)
    @patch(_GET_VIX, return_value=32.0)
    @patch(_DATA_CLIENT)
    def test_pipeline_high_vol_bear(
        self, mock_dc, mock_vix, mock_sp, mock_yc, mock_cls, mock_sig,
        mock_score, mock_entry, mock_radj, mock_atr, mock_vp, mock_plan,
    ):
        """High-Vol Bear regime gets low risk_adjustment (0.3)."""
        mock_instance = MagicMock()
        mock_instance.get_full.return_value = _mock_data(close=150.0, adx=30.0)
        mock_dc.return_value = mock_instance

        result = run_full_pipeline("AAPL")
        assert result.regime == "High-Vol Bear"
        # Verify risk_adjustment was called (0.3 for High-Vol Bear)
        mock_radj.assert_called_with("High-Vol Bear")

    @patch(_CHECK_ENTRY, return_value={"allowed": True, "drawdown_level": 0, "drawdown_pct": 0.0, "reason": "normal"})
    @patch(_SCORE_SYMBOL, return_value={"composite_score": 0.0, "risk_adjusted_score": 0.0, "safety_passed": False, "symbol": "BAD"})
    @patch(_GEN_SIGNALS, return_value=_mock_signal_result("NEUTRAL", 0))
    @patch(_CLASSIFY, return_value=_mock_regime())
    @patch(_GET_YIELD, return_value=50.0)
    @patch(_GET_SP500, return_value=1.05)
    @patch(_GET_VIX, return_value=15.0)
    @patch(_DATA_CLIENT)
    def test_pipeline_safety_gate(
        self, mock_dc, mock_vix, mock_sp, mock_yc, mock_cls, mock_sig, mock_score, mock_entry,
    ):
        """Safety gate failure is reflected in result."""
        mock_instance = MagicMock()
        mock_instance.get_full.return_value = _mock_data(close=150.0)
        mock_dc.return_value = mock_instance

        result = run_full_pipeline("BAD")
        assert result.safety_passed is False

    @patch(_DATA_CLIENT)
    def test_pipeline_error_handling(self, mock_dc):
        """DataClient failure sets error field."""
        mock_instance = MagicMock()
        mock_instance.get_full.side_effect = ConnectionError("Network unreachable")
        mock_dc.return_value = mock_instance

        result = run_full_pipeline("FAIL")
        assert result.error is not None
        assert "Data fetch failed" in result.error
        assert result.regime == "Unknown"
        assert result.composite_score == 0.0

    @patch(_PLAN_ENTRY, return_value=_mock_entry_plan())
    @patch(_VALIDATE_POS, return_value={"passed": True, "violations": []})
    @patch(_ATR_SIZE, return_value={"shares": 22, "position_value": 3300.0, "stop_price": 139.5})
    @patch(_RISK_ADJ, return_value=1.0)
    @patch(_CHECK_ENTRY, return_value={"allowed": True, "drawdown_level": 0, "drawdown_pct": 0.0, "reason": "normal"})
    @patch(_SCORE_SYMBOL, return_value={"composite_score": 65.0, "risk_adjusted_score": 65.0, "safety_passed": True, "symbol": "AAPL"})
    @patch(_GEN_SIGNALS, return_value=_mock_signal_result())
    @patch(_CLASSIFY, return_value=_mock_regime())
    @patch(_GET_YIELD, return_value=50.0)
    @patch(_GET_SP500, return_value=1.05)
    @patch(_GET_VIX, return_value=15.0)
    @patch(_DATA_CLIENT)
    def test_pipeline_capital_allocation(
        self, mock_dc, mock_vix, mock_sp, mock_yc, mock_cls, mock_sig,
        mock_score, mock_entry, mock_radj, mock_atr, mock_vp, mock_plan,
    ):
        """Position sizing uses capital correctly."""
        mock_instance = MagicMock()
        mock_instance.get_full.return_value = _mock_data(close=150.0, atr=3.5)
        mock_dc.return_value = mock_instance

        result = run_full_pipeline("AAPL", capital=200_000.0)
        # atr_position_size should have been called with risk-adjusted capital
        mock_atr.assert_called_once()
        call_args = mock_atr.call_args
        # First arg is capital (risk_adj * capital = 1.0 * 200000)
        assert call_args[0][0] == 200_000.0  # adjusted_capital
        assert result.position_shares == 22


class TestRunQuickScan:
    @patch(_SCORE_SYMBOL)
    @patch(_CLASSIFY, return_value=_mock_regime())
    @patch(_GET_YIELD, return_value=50.0)
    @patch(_GET_SP500, return_value=1.05)
    @patch(_GET_VIX, return_value=15.0)
    @patch(_DATA_CLIENT)
    def test_run_quick_scan_multiple_symbols(
        self, mock_dc, mock_vix, mock_sp, mock_yc, mock_cls, mock_score,
    ):
        """Quick scan returns results for multiple symbols."""
        mock_instance = MagicMock()
        mock_instance.get_full.side_effect = [
            _mock_data("AAPL", close=150.0),
            _mock_data("MSFT", close=350.0),
        ]
        mock_dc.return_value = mock_instance

        mock_score.side_effect = [
            {"composite_score": 72.0, "risk_adjusted_score": 72.0, "safety_passed": True, "symbol": "AAPL"},
            {"composite_score": 68.0, "risk_adjusted_score": 68.0, "safety_passed": True, "symbol": "MSFT"},
        ]

        results = run_quick_scan(["AAPL", "MSFT"])

        assert "AAPL" in results
        assert "MSFT" in results
        assert results["AAPL"]["score"] == 72.0
        assert results["MSFT"]["score"] == 68.0
        assert results["AAPL"]["safety_passed"] is True
        assert results["AAPL"]["regime"] == "Low-Vol Bull"

    @patch(_CLASSIFY, return_value=_mock_regime())
    @patch(_GET_YIELD, return_value=50.0)
    @patch(_GET_SP500, return_value=1.05)
    @patch(_GET_VIX, return_value=15.0)
    @patch(_DATA_CLIENT)
    def test_quick_scan_handles_error(
        self, mock_dc, mock_vix, mock_sp, mock_yc, mock_cls,
    ):
        """Quick scan gracefully handles per-symbol errors."""
        mock_instance = MagicMock()
        mock_instance.get_full.side_effect = Exception("API limit reached")
        mock_dc.return_value = mock_instance

        results = run_quick_scan(["BAD"])

        assert "BAD" in results
        assert results["BAD"]["score"] == 0.0
        assert "error" in results["BAD"]
