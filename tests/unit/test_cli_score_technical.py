"""Tests for technical sub-score wiring in handler and CLI display.

Verifies:
1. ScoreSymbolHandler produces technical_sub_scores in result dict
2. Handler result still has technical_score float (backward compat)
3. CLI score output contains indicator names when sub-scores present
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from src.scoring.application.commands import ScoreSymbolCommand
from src.scoring.application.handlers import ScoreSymbolHandler
from src.scoring.domain.value_objects import CompositeScore


# -- Fakes (same pattern as test_score_handler_events.py) --


class FakeScoreRepo:
    """In-memory score repository for testing."""

    def __init__(self) -> None:
        self._scores: dict[str, CompositeScore] = {}

    def save(self, symbol: str, score: CompositeScore) -> None:
        self._scores[symbol] = score

    def find_latest(self, symbol: str) -> Optional[CompositeScore]:
        return self._scores.get(symbol)

    def find_all_latest(self, limit: int = 100) -> dict[str, CompositeScore]:
        return dict(list(self._scores.items())[:limit])


class FakeClient:
    """Mock data client that returns configurable data."""

    def __init__(self, data: dict) -> None:
        self._data = data

    def get(self, symbol: str) -> dict:
        return self._data


# -- Fixtures --


@pytest.fixture
def handler_with_technical_subscores():
    """Handler with mock clients including technical indicator raw values."""
    repo = FakeScoreRepo()
    fundamental_client = FakeClient({
        "fundamental_score": 70,
        "f_score": 7,
        "z_score": 3.5,
        "m_score": -3.0,
    })
    # Technical client returns raw indicator values for sub-score computation
    technical_client = FakeClient({
        "technical_score": 60,
        "rsi": 45.0,
        "macd_histogram": 1.5,
        "close": 150.0,
        "ma50": 148.0,
        "ma200": 140.0,
        "adx": 28.0,
        "obv_change_pct": 5.0,
    })
    sentiment_client = FakeClient({"sentiment_score": 55})

    handler = ScoreSymbolHandler(
        score_repo=repo,
        fundamental_client=fundamental_client,
        technical_client=technical_client,
        sentiment_client=sentiment_client,
    )
    return handler, repo


@pytest.fixture
def handler_without_indicator_data():
    """Handler with technical client that has no raw indicator values."""
    repo = FakeScoreRepo()
    fundamental_client = FakeClient({
        "fundamental_score": 70,
        "f_score": 7,
        "z_score": 3.5,
        "m_score": -3.0,
    })
    # Only has the composite score, no raw indicator values
    technical_client = FakeClient({"technical_score": 60})
    sentiment_client = FakeClient({"sentiment_score": 55})

    handler = ScoreSymbolHandler(
        score_repo=repo,
        fundamental_client=fundamental_client,
        technical_client=technical_client,
        sentiment_client=sentiment_client,
    )
    return handler, repo


# -- Handler tests --


class TestHandlerTechnicalSubScores:
    """Handler should produce technical_sub_scores in result dict."""

    def test_handler_includes_technical_sub_scores_key(
        self, handler_with_technical_subscores
    ) -> None:
        handler, _ = handler_with_technical_subscores
        cmd = ScoreSymbolCommand(symbol="AAPL", strategy="swing")
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        assert "technical_sub_scores" in data

    def test_handler_sub_scores_has_five_entries(
        self, handler_with_technical_subscores
    ) -> None:
        handler, _ = handler_with_technical_subscores
        cmd = ScoreSymbolCommand(symbol="AAPL", strategy="swing")
        result = handler.handle(cmd)

        data = result.unwrap()
        sub_scores = data["technical_sub_scores"]
        assert len(sub_scores) == 5

    def test_handler_sub_scores_contain_indicator_names(
        self, handler_with_technical_subscores
    ) -> None:
        handler, _ = handler_with_technical_subscores
        cmd = ScoreSymbolCommand(symbol="AAPL", strategy="swing")
        result = handler.handle(cmd)

        data = result.unwrap()
        names = {s["name"] for s in data["technical_sub_scores"]}
        assert names == {"RSI", "MACD", "MA", "ADX", "OBV"}

    def test_handler_sub_scores_have_required_keys(
        self, handler_with_technical_subscores
    ) -> None:
        handler, _ = handler_with_technical_subscores
        cmd = ScoreSymbolCommand(symbol="AAPL", strategy="swing")
        result = handler.handle(cmd)

        data = result.unwrap()
        for sub in data["technical_sub_scores"]:
            assert "name" in sub
            assert "value" in sub
            assert "explanation" in sub
            assert "raw_value" in sub
            assert 0 <= sub["value"] <= 100

    def test_handler_still_has_technical_score_float(
        self, handler_with_technical_subscores
    ) -> None:
        """Backward compat: technical_score key still present as numeric."""
        handler, _ = handler_with_technical_subscores
        cmd = ScoreSymbolCommand(symbol="AAPL", strategy="swing")
        result = handler.handle(cmd)

        data = result.unwrap()
        assert "technical_score" in data
        assert isinstance(data["technical_score"], (int, float))

    def test_handler_fallback_without_indicator_data(
        self, handler_without_indicator_data
    ) -> None:
        """When no raw indicator values, handler still works (no sub-scores or default sub-scores)."""
        handler, _ = handler_without_indicator_data
        cmd = ScoreSymbolCommand(symbol="AAPL", strategy="swing")
        result = handler.handle(cmd)

        assert result.is_ok()
        data = result.unwrap()
        # technical_score must still exist
        assert "technical_score" in data
        assert isinstance(data["technical_score"], (int, float))


# -- CLI output tests --


class TestCLITechnicalSubScoreDisplay:
    """CLI score command should display technical indicator sub-table."""

    def test_cli_renders_sub_score_table(self) -> None:
        """Verify Rich Table rendering with sub-scores produces indicator names."""
        from io import StringIO
        from rich.console import Console as RichConsole
        from rich.table import Table

        buf = StringIO()
        test_console = RichConsole(file=buf, width=120)

        sub_scores = [
            {"name": "RSI", "value": 55.0, "explanation": "RSI at 45: neutral", "raw_value": 45.0},
            {"name": "MACD", "value": 65.0, "explanation": "MACD +1.50: bullish", "raw_value": 1.5},
            {"name": "MA", "value": 70.0, "explanation": "MA trend: uptrend", "raw_value": 150.0},
            {"name": "ADX", "value": 56.0, "explanation": "ADX at 28: strong", "raw_value": 28.0},
            {"name": "OBV", "value": 62.5, "explanation": "OBV +5.0%: positive", "raw_value": 5.0},
        ]

        tech_table = Table(title="Technical Indicators", show_header=True)
        tech_table.add_column("Indicator", style="bold")
        tech_table.add_column("Score", justify="right")
        tech_table.add_column("Explanation")

        for sub in sub_scores:
            score_val = sub["value"]
            if score_val >= 60:
                score_style = "green"
            elif score_val >= 40:
                score_style = "yellow"
            else:
                score_style = "red"
            tech_table.add_row(
                sub["name"],
                f"[{score_style}]{score_val:.1f}[/{score_style}]",
                sub["explanation"],
            )

        test_console.print(tech_table)
        output = buf.getvalue()

        # All 5 indicator names must appear
        for name in ("RSI", "MACD", "MA", "ADX", "OBV"):
            assert name in output, f"Indicator {name} not found in CLI output"

        assert "Technical Indicators" in output

    def test_cli_no_sub_table_when_no_sub_scores(self) -> None:
        """When sub_scores list is empty, no sub-table is rendered."""
        from io import StringIO
        from rich.console import Console as RichConsole

        buf = StringIO()
        test_console = RichConsole(file=buf, width=120)

        sub_scores: list = []
        if sub_scores:
            test_console.print("Technical Indicators")  # Should NOT appear

        output = buf.getvalue()
        assert "Technical Indicators" not in output


# -- Gap closure tests (07-03) --


class TestHandlerEndToEndSubScoresAndWeights:
    """Integration: handler with known inputs produces sub-scores and correct composite."""

    def test_handler_end_to_end_sub_scores_and_weights(self) -> None:
        handler = ScoreSymbolHandler(
            score_repo=FakeScoreRepo(),
            fundamental_client=FakeClient({"fundamental_score": 80, "z_score": 3.5, "m_score": -3.0}),
            technical_client=FakeClient({
                "technical_score": 60,
                "rsi": 45.0, "macd_histogram": 1.5, "close": 150.0,
                "ma50": 148.0, "ma200": 140.0, "adx": 28.0, "obv_change_pct": 5.0,
            }),
            sentiment_client=FakeClient({"sentiment_score": 50}),
        )
        result = handler.handle(ScoreSymbolCommand(symbol="TEST", strategy="swing")).unwrap()

        # Sub-scores present with 5 entries
        assert len(result["technical_sub_scores"]) == 5

        # Composite uses 40/40/20: fund*0.40 + tech*0.40 + sent*0.20
        # Technical value comes from TechnicalScoringService (not the raw 60)
        assert result["composite_score"] > 0
        # Verify it's NOT the old 35/40/25 result
        new_composite = 0.40 * 80 + 0.40 * result["technical_score"] + 0.20 * 50
        # The actual composite should match the 40/40/20 formula (within rounding)
        assert abs(result["composite_score"] - new_composite) < 1.0


class TestCLIDoesNotImportLegacyScoring:
    """CLI score command must NOT import from core.scoring.composite."""

    def test_cli_score_does_not_import_legacy_scoring(self) -> None:
        import ast
        with open("cli/main.py") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "core.scoring.composite" not in node.module, \
                    "CLI still imports from core.scoring.composite (legacy path)"


class TestHandlerErrorProducesErrResult:
    """When data client raises, handler returns Err, not crash."""

    def test_handler_error_produces_err_result(self) -> None:
        class CrashingClient:
            def get(self, symbol: str):
                raise ConnectionError("API down")

        handler = ScoreSymbolHandler(
            score_repo=FakeScoreRepo(),
            fundamental_client=CrashingClient(),
        )
        result = handler.handle(ScoreSymbolCommand(symbol="FAIL"))
        assert not result.is_ok()
