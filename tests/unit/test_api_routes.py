"""Unit tests for Commercial API routes."""
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from commercial.api.main import app
from commercial.api.models import DISCLAIMER

client = TestClient(app)


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _mock_score_modules():
    """Return a dict of patches for the score endpoint's internal imports."""
    mock_data_client_cls = MagicMock()
    mock_client_instance = MagicMock()
    mock_data_client_cls.return_value = mock_client_instance
    mock_client_instance.get_full.return_value = {
        "symbol": "AAPL",
        "price": {"close": 150.0},
        "indicators": {"adx14": 22.0},
        "fundamentals": {"highlights": {"z_score": 3.0, "m_score": -2.5}},
    }

    mock_score_symbol = MagicMock(return_value={
        "symbol": "AAPL",
        "composite_score": 72.5,
        "safety_passed": True,
        "fundamental_score": 60.0,
        "technical_score": 70.0,
        "sentiment_score": 55.0,
    })

    mock_check_safety = MagicMock(return_value={
        "safety_passed": True,
        "z_score": 3.0,
        "z_pass": True,
        "m_score": -2.5,
        "m_pass": True,
    })

    mock_classify = MagicMock(return_value={
        "regime": "Low-Vol Bull",
        "confidence": 0.80,
    })

    mock_get_vix = MagicMock(return_value=15.0)
    mock_get_sp500 = MagicMock(return_value=1.05)
    mock_get_slope = MagicMock(return_value=50.0)

    return {
        "core.data.client.DataClient": mock_data_client_cls,
        "core.scoring.composite.score_symbol": mock_score_symbol,
        "core.scoring.safety.check_safety": mock_check_safety,
        "core.regime.classifier.classify": mock_classify,
        "core.data.market.get_vix": mock_get_vix,
        "core.data.market.get_sp500_vs_200ma": mock_get_sp500,
        "core.data.market.get_yield_curve_slope": mock_get_slope,
    }


def _mock_regime_modules():
    """Return a dict of patches for the regime endpoint's internal imports."""
    mock_classify = MagicMock(return_value={
        "regime": "Low-Vol Bull",
        "confidence": 0.80,
    })
    mock_get_weights = MagicMock(return_value={
        "canslim": 0.30, "magic": 0.20, "momentum": 0.25, "trend": 0.25,
    })
    mock_get_risk_adj = MagicMock(return_value=1.0)
    mock_get_vix = MagicMock(return_value=15.0)
    mock_get_sp500 = MagicMock(return_value=1.05)
    mock_get_slope = MagicMock(return_value=50.0)

    return {
        "core.regime.classifier.classify": mock_classify,
        "core.regime.weights.get_weights": mock_get_weights,
        "core.regime.weights.get_risk_adjustment": mock_get_risk_adj,
        "core.data.market.get_vix": mock_get_vix,
        "core.data.market.get_sp500_vs_200ma": mock_get_sp500,
        "core.data.market.get_yield_curve_slope": mock_get_slope,
    }


def _mock_signal_modules():
    """Return a dict of patches for the signal endpoint's internal imports."""
    mock_data_client_cls = MagicMock()
    mock_client_instance = MagicMock()
    mock_data_client_cls.return_value = mock_client_instance
    mock_client_instance.get_full.return_value = {
        "symbol": "AAPL",
        "price": {"close": 150.0},
        "indicators": {"adx14": 22.0},
        "fundamentals": {"highlights": {}},
    }

    mock_generate_signals = MagicMock(return_value={
        "consensus": "BULLISH",
        "agreement": 3,
        "methods": {
            "canslim": {"signal": "BUY", "score": 5, "score_max": 7},
            "magic_formula": {"signal": "BUY", "score": 80, "score_max": 100},
            "dual_momentum": {"signal": "BUY", "score": 1, "score_max": 1},
            "trend_following": {"signal": "HOLD", "score": 2, "score_max": 4},
        },
    })

    mock_classify = MagicMock(return_value={
        "regime": "Low-Vol Bull",
        "confidence": 0.80,
    })

    mock_get_vix = MagicMock(return_value=15.0)
    mock_get_sp500 = MagicMock(return_value=1.05)
    mock_get_slope = MagicMock(return_value=50.0)

    return {
        "core.data.client.DataClient": mock_data_client_cls,
        "core.signals.consensus.generate_signals": mock_generate_signals,
        "core.regime.classifier.classify": mock_classify,
        "core.data.market.get_vix": mock_get_vix,
        "core.data.market.get_sp500_vs_200ma": mock_get_sp500,
        "core.data.market.get_yield_curve_slope": mock_get_slope,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_endpoint(self):
        """GET /health returns status ok and version 1.0.0."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"


class TestScoreEndpoint:
    def test_score_endpoint_returns_disclaimer(self):
        """GET /score/AAPL includes the mandatory disclaimer."""
        mocks = _mock_score_modules()
        with patch.dict(sys.modules, {}, clear=False):
            for target, mock_obj in mocks.items():
                parts = target.rsplit(".", 1)
                mod_path, attr = parts[0], parts[1]
                # Ensure module exists in sys.modules with the mock attribute
                if mod_path not in sys.modules:
                    sys.modules[mod_path] = MagicMock()
                setattr(sys.modules[mod_path], attr, mock_obj)

            resp = client.get("/score/AAPL")

        assert resp.status_code == 200
        data = resp.json()
        assert data["disclaimer"] == DISCLAIMER

    def test_score_endpoint_symbol_uppercase(self):
        """GET /score/aapl returns symbol as AAPL."""
        mocks = _mock_score_modules()
        for target, mock_obj in mocks.items():
            parts = target.rsplit(".", 1)
            mod_path, attr = parts[0], parts[1]
            if mod_path not in sys.modules:
                sys.modules[mod_path] = MagicMock()
            setattr(sys.modules[mod_path], attr, mock_obj)

        resp = client.get("/score/aapl")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "AAPL"

    def test_score_range_valid(self):
        """composite_score is within 0-100 range."""
        mocks = _mock_score_modules()
        for target, mock_obj in mocks.items():
            parts = target.rsplit(".", 1)
            mod_path, attr = parts[0], parts[1]
            if mod_path not in sys.modules:
                sys.modules[mod_path] = MagicMock()
            setattr(sys.modules[mod_path], attr, mock_obj)

        resp = client.get("/score/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert 0 <= data["composite_score"] <= 100

    def test_score_endpoint_503_on_error(self):
        """GET /score/AAPL returns 503 when core raises an exception."""
        # Inject a DataClient that raises on instantiation
        bad_client = MagicMock(side_effect=RuntimeError("API down"))
        mod = MagicMock()
        mod.DataClient = bad_client
        sys.modules["core.data.client"] = mod

        resp = client.get("/score/FAIL")
        assert resp.status_code == 503

        # Clean up
        del sys.modules["core.data.client"]


class TestRegimeEndpoint:
    def test_regime_endpoint_returns_disclaimer(self):
        """GET /regime includes the mandatory disclaimer."""
        mocks = _mock_regime_modules()
        for target, mock_obj in mocks.items():
            parts = target.rsplit(".", 1)
            mod_path, attr = parts[0], parts[1]
            if mod_path not in sys.modules:
                sys.modules[mod_path] = MagicMock()
            setattr(sys.modules[mod_path], attr, mock_obj)

        resp = client.get("/regime")
        assert resp.status_code == 200
        data = resp.json()
        assert data["disclaimer"] == DISCLAIMER

    def test_regime_has_strategy_weights(self):
        """GET /regime response contains strategy_weights dict."""
        mocks = _mock_regime_modules()
        for target, mock_obj in mocks.items():
            parts = target.rsplit(".", 1)
            mod_path, attr = parts[0], parts[1]
            if mod_path not in sys.modules:
                sys.modules[mod_path] = MagicMock()
            setattr(sys.modules[mod_path], attr, mock_obj)

        resp = client.get("/regime")
        assert resp.status_code == 200
        data = resp.json()
        assert "strategy_weights" in data
        assert isinstance(data["strategy_weights"], dict)
        assert len(data["strategy_weights"]) > 0


class TestSignalEndpoint:
    def test_signal_endpoint_returns_disclaimer(self):
        """GET /signal/AAPL includes the mandatory disclaimer."""
        mocks = _mock_signal_modules()
        for target, mock_obj in mocks.items():
            parts = target.rsplit(".", 1)
            mod_path, attr = parts[0], parts[1]
            if mod_path not in sys.modules:
                sys.modules[mod_path] = MagicMock()
            setattr(sys.modules[mod_path], attr, mock_obj)

        resp = client.get("/signal/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["disclaimer"] == DISCLAIMER

    def test_signal_consensus_valid(self):
        """consensus must be one of BULLISH, BEARISH, NEUTRAL."""
        mocks = _mock_signal_modules()
        for target, mock_obj in mocks.items():
            parts = target.rsplit(".", 1)
            mod_path, attr = parts[0], parts[1]
            if mod_path not in sys.modules:
                sys.modules[mod_path] = MagicMock()
            setattr(sys.modules[mod_path], attr, mock_obj)

        resp = client.get("/signal/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["consensus"] in ["BULLISH", "BEARISH", "NEUTRAL"]


class TestAllEndpointsDisclaimer:
    def test_all_endpoints_have_disclaimer(self):
        """All three data endpoints include the disclaimer field."""
        # Setup all mocks
        score_mocks = _mock_score_modules()
        regime_mocks = _mock_regime_modules()
        signal_mocks = _mock_signal_modules()

        all_mocks = {}
        all_mocks.update(score_mocks)
        all_mocks.update(regime_mocks)
        all_mocks.update(signal_mocks)

        for target, mock_obj in all_mocks.items():
            parts = target.rsplit(".", 1)
            mod_path, attr = parts[0], parts[1]
            if mod_path not in sys.modules:
                sys.modules[mod_path] = MagicMock()
            setattr(sys.modules[mod_path], attr, mock_obj)

        endpoints = ["/score/AAPL", "/regime", "/signal/AAPL"]
        for endpoint in endpoints:
            resp = client.get(endpoint)
            assert resp.status_code == 200, f"{endpoint} returned {resp.status_code}"
            data = resp.json()
            assert "disclaimer" in data, f"{endpoint} missing disclaimer"
            assert data["disclaimer"] == DISCLAIMER, f"{endpoint} wrong disclaimer"
