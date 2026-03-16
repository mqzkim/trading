"""Unit tests for SentimentScore VO expansion and SentimentConfidence enum.

Phase 27-02: Covers backward compatibility, sub-score fields, validation,
confidence enum, and SentimentUpdatedEvent.
"""
import pytest

from src.scoring.domain.value_objects import SentimentScore, SentimentConfidence
from src.scoring.domain.events import SentimentUpdatedEvent
from src.shared.domain import DomainEvent


# -- SentimentConfidence enum --------------------------------------------------


class TestSentimentConfidenceEnum:
    """SentimentConfidence enum has four distinct variants."""

    def test_has_none_variant(self) -> None:
        assert SentimentConfidence.NONE is not None

    def test_has_low_variant(self) -> None:
        assert SentimentConfidence.LOW is not None

    def test_has_medium_variant(self) -> None:
        assert SentimentConfidence.MEDIUM is not None

    def test_has_high_variant(self) -> None:
        assert SentimentConfidence.HIGH is not None

    def test_all_four_variants_distinct(self) -> None:
        levels = [
            SentimentConfidence.NONE,
            SentimentConfidence.LOW,
            SentimentConfidence.MEDIUM,
            SentimentConfidence.HIGH,
        ]
        assert len(set(levels)) == 4

    def test_importable_from_domain_package(self) -> None:
        from src.scoring.domain import SentimentConfidence as DomainSC
        assert DomainSC.NONE is SentimentConfidence.NONE

    def test_is_str_enum_for_serialization(self) -> None:
        """SentimentConfidence is a str enum — values are strings."""
        assert isinstance(SentimentConfidence.NONE.value, str)
        assert isinstance(SentimentConfidence.HIGH.value, str)


# -- SentimentScore VO backward compatibility ----------------------------------


class TestSentimentScoreBackwardCompat:
    """SentimentScore(value=X) works exactly as before."""

    def test_value_only_construction(self) -> None:
        score = SentimentScore(value=50)
        assert score.value == 50

    def test_defaults_confidence_to_none(self) -> None:
        score = SentimentScore(value=50)
        assert score.confidence == SentimentConfidence.NONE

    def test_defaults_all_sub_scores_to_none(self) -> None:
        score = SentimentScore(value=50)
        assert score.news_score is None
        assert score.insider_score is None
        assert score.institutional_score is None
        assert score.analyst_score is None

    def test_value_boundary_zero(self) -> None:
        score = SentimentScore(value=0)
        assert score.value == 0

    def test_value_boundary_hundred(self) -> None:
        score = SentimentScore(value=100)
        assert score.value == 100


# -- SentimentScore VO full construction ---------------------------------------


class TestSentimentScoreFullConstruction:
    """SentimentScore with all sub-fields and confidence."""

    def test_high_confidence_all_fields(self) -> None:
        score = SentimentScore(
            value=70.0,
            news_score=65.0,
            insider_score=75.0,
            institutional_score=60.0,
            analyst_score=80.0,
            confidence=SentimentConfidence.HIGH,
        )
        assert score.value == 70.0
        assert score.news_score == 65.0
        assert score.insider_score == 75.0
        assert score.institutional_score == 60.0
        assert score.analyst_score == 80.0
        assert score.confidence == SentimentConfidence.HIGH

    def test_partial_sub_scores_news_only(self) -> None:
        score = SentimentScore(
            value=60.0,
            news_score=55.0,
            confidence=SentimentConfidence.LOW,
        )
        assert score.news_score == 55.0
        assert score.insider_score is None
        assert score.institutional_score is None
        assert score.analyst_score is None
        assert score.confidence == SentimentConfidence.LOW

    def test_is_frozen_immutable(self) -> None:
        score = SentimentScore(value=50, confidence=SentimentConfidence.MEDIUM)
        with pytest.raises((AttributeError, TypeError)):
            score.value = 99.0  # type: ignore[misc]


# -- SentimentScore VO validation ----------------------------------------------


class TestSentimentScoreValidation:
    """SentimentScore validation still rejects out-of-range values."""

    def test_rejects_negative_value(self) -> None:
        with pytest.raises(ValueError):
            SentimentScore(value=-1.0)

    def test_rejects_value_above_100(self) -> None:
        with pytest.raises(ValueError):
            SentimentScore(value=101.0)

    def test_rejects_large_negative(self) -> None:
        with pytest.raises(ValueError):
            SentimentScore(value=-50.0)


# -- SentimentUpdatedEvent -----------------------------------------------------


class TestSentimentUpdatedEvent:
    """SentimentUpdatedEvent is a DomainEvent subclass with all required fields."""

    def test_importable_from_events_module(self) -> None:
        from src.scoring.domain.events import SentimentUpdatedEvent as Evt
        assert Evt is not None

    def test_importable_from_domain_package(self) -> None:
        from src.scoring.domain import SentimentUpdatedEvent as Evt
        assert Evt is not None

    def test_is_domain_event_subclass(self) -> None:
        event = SentimentUpdatedEvent(
            symbol="AAPL",
            sentiment_score=70.0,
            confidence="HIGH",
            news_score=65.0,
            insider_score=None,
            institutional_score=75.0,
            analyst_score=80.0,
        )
        assert isinstance(event, DomainEvent)

    def test_all_required_fields_accessible(self) -> None:
        event = SentimentUpdatedEvent(
            symbol="TSLA",
            sentiment_score=55.0,
            confidence="MEDIUM",
            news_score=60.0,
            insider_score=50.0,
            institutional_score=None,
            analyst_score=55.0,
        )
        assert event.symbol == "TSLA"
        assert event.sentiment_score == 55.0
        assert event.confidence == "MEDIUM"
        assert event.news_score == 60.0
        assert event.insider_score == 50.0
        assert event.institutional_score is None
        assert event.analyst_score == 55.0

    def test_is_frozen(self) -> None:
        event = SentimentUpdatedEvent(
            symbol="AAPL",
            sentiment_score=70.0,
            confidence="HIGH",
            news_score=65.0,
            insider_score=None,
            institutional_score=75.0,
            analyst_score=80.0,
        )
        with pytest.raises((AttributeError, TypeError)):
            event.symbol = "GOOG"  # type: ignore[misc]

    def test_none_sub_scores_allowed(self) -> None:
        """All sub-scores can be None (e.g., when confidence=NONE)."""
        event = SentimentUpdatedEvent(
            symbol="SPY",
            sentiment_score=50.0,
            confidence="NONE",
            news_score=None,
            insider_score=None,
            institutional_score=None,
            analyst_score=None,
        )
        assert event.news_score is None
        assert event.insider_score is None
        assert event.institutional_score is None
        assert event.analyst_score is None
