"""Unit tests for SentimentService — AC 12: NewsProvider Ok([]) propagates as Err.

AC 12: When NewsProvider returns Ok([]) (empty list), SentimentService.get_sentiment()
must return Err("no_headlines_available") — NOT Ok(neutral_score).
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.shared.domain import Ok, Err
from src.scoring.domain.services import SentimentService
from src.scoring.domain.value_objects import NewsItem, SentimentScore


# ---------------------------------------------------------------------------
# Inline test doubles (Protocol-compliant via duck typing)
# ---------------------------------------------------------------------------

class InMemoryNewsProvider:
    """Test double for NewsProvider — returns a pre-configured Result."""

    def __init__(self, result: Ok | Err) -> None:
        self._result = result

    def fetch(self, symbol: str) -> Ok | Err:  # type: ignore[override]
        return self._result


class InMemorySentimentAnalyzer:
    """Test double for SentimentAnalyzer — mirrors VADERSentimentAnalyzer contract.

    Returns Err("no_headlines_available") when texts is empty (matching VADER behavior).
    Otherwise returns a pre-configured Ok(SentimentScore).
    """

    def __init__(self, ok_result: Ok | None = None) -> None:
        self._ok_result = ok_result or Ok(
            SentimentScore(value=55.0, confidence=0.5, metadata={})
        )

    def analyze(self, symbol: str, texts: list[str]) -> Ok | Err:  # type: ignore[override]
        if not texts:
            return Err("no_headlines_available")  # type: ignore[arg-type]
        return self._ok_result


# ---------------------------------------------------------------------------
# AC 12 tests
# ---------------------------------------------------------------------------

class TestSentimentServiceEmptyNews:
    """AC 12: NewsProvider Ok([]) must propagate as Err("no_headlines_available")."""

    def test_ok_empty_list_returns_err_no_headlines(self) -> None:
        """Core AC-12 assertion: Ok([]) → Err("no_headlines_available")."""
        provider = InMemoryNewsProvider(Ok([]))
        analyzer = InMemorySentimentAnalyzer()
        service = SentimentService(news_provider=provider, sentiment_analyzer=analyzer)

        result = service.get_sentiment("AAPL")

        assert result.is_err(), "Expected Err but got Ok"
        assert result.error == "no_headlines_available"  # type: ignore[union-attr]

    def test_ok_empty_list_does_not_return_neutral_ok(self) -> None:
        """Regression guard: empty list must NOT silently return neutral 50.0."""
        provider = InMemoryNewsProvider(Ok([]))
        analyzer = InMemorySentimentAnalyzer()
        service = SentimentService(news_provider=provider, sentiment_analyzer=analyzer)

        result = service.get_sentiment("TSLA")

        assert not result.is_ok(), (
            "SentimentService returned Ok(neutral_score) for empty news list — "
            "should return Err('no_headlines_available') per AC 12"
        )

    def test_ok_with_headlines_returns_ok_score(self) -> None:
        """Non-empty list still produces Ok(SentimentScore) — regression guard."""
        news_item = NewsItem(headline="Apple beats earnings", published_at=datetime.now(timezone.utc))
        provider = InMemoryNewsProvider(Ok([news_item]))
        expected_score = SentimentScore(value=70.0, confidence=0.3, metadata={"symbol": "AAPL"})
        analyzer = InMemorySentimentAnalyzer(ok_result=Ok(expected_score))
        service = SentimentService(news_provider=provider, sentiment_analyzer=analyzer)

        result = service.get_sentiment("AAPL")

        assert result.is_ok()
        assert result.unwrap() is expected_score  # type: ignore[union-attr]

    def test_news_provider_err_propagates(self) -> None:
        """NewsProvider network failure also propagates as Err — regression guard."""
        provider = InMemoryNewsProvider(Err("network_timeout"))  # type: ignore[arg-type]
        analyzer = InMemorySentimentAnalyzer()
        service = SentimentService(news_provider=provider, sentiment_analyzer=analyzer)

        result = service.get_sentiment("MSFT")

        assert result.is_err()
        assert result.error == "network_timeout"  # type: ignore[union-attr]
