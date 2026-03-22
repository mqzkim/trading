"""Scoring 도메인 공개 API.

이 파일에 없는 것은 외부에서 import 금지.
"""
from .value_objects import (
    Symbol,
    FundamentalScore,
    TechnicalIndicatorScore,
    TechnicalScore,
    SentimentScore,
    NewsItem,
    SafetyGate,
    CompositeScore,
    STRATEGY_WEIGHTS,
    DEFAULT_STRATEGY,
)
from .events import ScoreUpdatedEvent
from .services import (
    CompositeScoringService,
    SafetyFilterService,
    TechnicalScoringService,
    SentimentAnalyzer,
    NewsProvider,
    SentimentService,
    TECHNICAL_INDICATOR_WEIGHTS,
)
from .repositories import IScoreRepository

__all__ = [
    "Symbol",
    "FundamentalScore",
    "TechnicalIndicatorScore",
    "TechnicalScore",
    "SentimentScore",
    "NewsItem",
    "SafetyGate",
    "CompositeScore",
    "STRATEGY_WEIGHTS",
    "DEFAULT_STRATEGY",
    "ScoreUpdatedEvent",
    "CompositeScoringService",
    "SafetyFilterService",
    "TechnicalScoringService",
    "SentimentAnalyzer",
    "NewsProvider",
    "SentimentService",
    "TECHNICAL_INDICATOR_WEIGHTS",
    "IScoreRepository",
]
