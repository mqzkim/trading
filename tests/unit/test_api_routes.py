"""Smoke tests for API route registration and health endpoint.

These tests verify the current v1.1 API surface:
- /health returns correct status and version
- v1 API routes are registered (non-404 responses)
- DISCLAIMER constant is importable and non-empty

Comprehensive endpoint behavior tests live in test_api_v1_*.py files.
"""
from fastapi.testclient import TestClient

from commercial.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_status_ok(self):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_version_1_1_0(self):
        resp = client.get("/health")
        data = resp.json()
        assert data["version"] == "1.1.0"


class TestRouteRegistration:
    """Verify v1 API routes are registered (return non-404 status codes).

    These routes require JWT auth, so without auth they return 401/403.
    The key assertion is that they do NOT return 404 (route not found).
    """

    def test_quantscore_route_exists(self):
        resp = client.get("/api/v1/quantscore/AAPL")
        assert resp.status_code != 404

    def test_regime_route_exists(self):
        resp = client.get("/api/v1/regime/current")
        assert resp.status_code != 404

    def test_signals_route_exists(self):
        resp = client.get("/api/v1/signals/AAPL")
        assert resp.status_code != 404

    def test_auth_token_route_exists(self):
        resp = client.post("/api/v1/auth/token")
        assert resp.status_code != 404


class TestDisclaimerConstant:
    def test_disclaimer_importable_from_models(self):
        from commercial.api.models import DISCLAIMER

        assert isinstance(DISCLAIMER, str)
        assert len(DISCLAIMER) > 0

    def test_disclaimer_importable_from_schemas_common(self):
        from commercial.api.schemas.common import DISCLAIMER

        assert isinstance(DISCLAIMER, str)
        assert len(DISCLAIMER) > 0
