"""Tests for CLI regime command DDD rewiring and history flag (REGIME-05)."""
from __future__ import annotations

import ast
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.main import app
from src.shared.domain import Ok, Err

runner = CliRunner()


def _mock_regime_handler(result_value: dict | None = None, error: str | None = None):
    """Create a mock regime handler that returns Ok or Err."""
    handler = MagicMock()
    if error:
        handler.handle.return_value = Err(Exception(error))
    else:
        default = {
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
        }
        handler.handle.return_value = Ok(result_value or default)
    return handler


def _mock_regime_entity(
    regime_type_value: str = "Bull",
    confidence: float = 0.85,
    confirmed_days: int = 5,
    detected_at: datetime | None = None,
):
    """Create a mock MarketRegime entity for history tests."""
    entity = MagicMock()
    entity.regime_type = MagicMock()
    entity.regime_type.value = regime_type_value
    entity.confidence = confidence
    entity.confirmed_days = confirmed_days
    entity.is_confirmed = confirmed_days >= 3
    entity.detected_at = detected_at or datetime.now(timezone.utc)
    return entity


class TestRegimeCommandNoLegacyImports:
    """Test 1: CLI regime command does not import from legacy core.regime path."""

    def test_regime_function_has_no_legacy_imports(self):
        """Parse cli/main.py AST and verify regime function has no core.regime imports."""
        with open("cli/main.py") as f:
            tree = ast.parse(f.read())

        # Find the regime function
        regime_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "regime":
                regime_func = node
                break

        assert regime_func is not None, "regime function not found in cli/main.py"

        # Check for legacy imports inside the function body
        for node in ast.walk(regime_func):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert not module.startswith("core.regime"), (
                    f"Found legacy import 'from {module}' in regime function"
                )
                assert not module.startswith("core.data.market"), (
                    f"Found legacy import 'from {module}' in regime function"
                )


class TestRegimeCommandDDDHandler:
    """Test 2: CLI regime command calls ctx['regime_handler'].handle()."""

    def test_regime_calls_ddd_handler(self):
        """Regime command uses DDD handler via _get_ctx()."""
        handler = _mock_regime_handler()
        ctx = {"regime_handler": handler}

        with patch("cli.main._get_ctx", return_value=ctx):
            result = runner.invoke(app, ["regime"])

        assert result.exit_code == 0
        assert "Bull" in result.output
        handler.handle.assert_called_once()


class TestRegimeHistoryFlag:
    """Test 3: CLI regime --history N shows past N days of regime transitions."""

    def test_regime_history_displays_table(self):
        """regime --history 90 shows regime history table with dates and types."""
        entities = [
            _mock_regime_entity("Bull", 0.85, 5, datetime(2026, 3, 10, tzinfo=timezone.utc)),
            _mock_regime_entity("Bear", 0.75, 3, datetime(2026, 3, 5, tzinfo=timezone.utc)),
            _mock_regime_entity("Sideways", 0.60, 2, datetime(2026, 3, 1, tzinfo=timezone.utc)),
        ]

        handler = MagicMock()
        handler._regime_repo.find_by_date_range.return_value = entities
        ctx = {"regime_handler": handler}

        with patch("cli.main._get_ctx", return_value=ctx):
            result = runner.invoke(app, ["regime", "--history", "90"])

        assert result.exit_code == 0
        assert "Bull" in result.output
        assert "Bear" in result.output
        assert "Sideways" in result.output
        assert "2026-03-10" in result.output
        assert "2026-03-05" in result.output


class TestRegimeErrorHandling:
    """Test 4: CLI regime handles Err result gracefully."""

    def test_regime_err_exits_with_code_1(self):
        """Err result shows error message and exits 1."""
        handler = _mock_regime_handler(error="Data fetch failed")
        ctx = {"regime_handler": handler}

        with patch("cli.main._get_ctx", return_value=ctx):
            result = runner.invoke(app, ["regime"])

        assert result.exit_code == 1
        assert "failed" in result.output.lower() or "error" in result.output.lower()


class TestRegimeJsonOutput:
    """Test 5: CLI regime --output json outputs structured JSON."""

    def test_regime_json_output(self):
        """regime --output json outputs JSON with expected fields."""
        handler = _mock_regime_handler()
        ctx = {"regime_handler": handler}

        with patch("cli.main._get_ctx", return_value=ctx):
            result = runner.invoke(app, ["regime", "--output", "json"])

        assert result.exit_code == 0
        # The output should contain JSON with regime data
        assert "regime_type" in result.output
        assert "confidence" in result.output
        assert "confirmed_days" in result.output
        assert "is_confirmed" in result.output
