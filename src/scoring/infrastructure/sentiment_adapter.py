"""Sentiment infrastructure adapters — VADER-based sentiment analysis.

VADERSentimentAnalyzer:
  Implements SentimentAnalyzer Protocol (duck typing, no ABC).
  Maps VADER compound score [-1, 1] to SentimentScore value [0, 100].

Score formulas (spec-exact):
  value      = (compound + 1) / 2 * 100
  confidence = min(n_headlines / 10, 1.0) * abs(compound)
"""
from __future__ import annotations

import logging

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src.shared.domain import Ok, Err, Result
from src.scoring.domain.value_objects import SentimentScore

logger = logging.getLogger(__name__)


class VADERSentimentAnalyzer:
    """VADER-based sentiment analyzer implementing the SentimentAnalyzer Protocol.

    Concrete implementation for SentimentAnalyzer (duck-typed protocol —
    no ABC inheritance required).

    Args:
        symbol: Stock ticker used for metadata tagging only.
        texts:  List of news headline strings to analyse.

    Returns:
        Ok(SentimentScore) — analysis succeeded (even for single headline).
        Err("no_headlines_available") — texts list was empty.
        Err(str) — unexpected VADER failure.

    Score formulas:
        compound   = mean VADER compound across all headlines  ∈ [-1, 1]
        value      = (compound + 1) / 2 * 100                 ∈ [0, 100]
        confidence = min(n_headlines / 10, 1.0) * abs(compound)
    """

    def __init__(self) -> None:
        self._sia: SentimentIntensityAnalyzer = SentimentIntensityAnalyzer()

    def analyze(self, symbol: str, texts: list[str]) -> Result[SentimentScore, str]:
        """Analyse a list of headlines and return a SentimentScore.

        Args:
            symbol: Ticker symbol — stored in metadata, not used for scoring.
            texts:  Non-empty list of headline strings.

        Returns:
            Ok(SentimentScore) on success.
            Err("no_headlines_available") when *texts* is empty.
            Err(str) on unexpected errors.
        """
        if not texts:
            return Err("no_headlines_available")  # type: ignore[return-value]

        try:
            compounds = [
                self._sia.polarity_scores(text)["compound"]
                for text in texts
            ]
        except Exception as exc:  # pragma: no cover
            logger.warning("VADERSentimentAnalyzer failed for %s: %s", symbol, exc)
            return Err(f"vader_error: {exc}")  # type: ignore[return-value]

        n_headlines = len(compounds)
        compound = sum(compounds) / n_headlines

        value = (compound + 1) / 2 * 100
        confidence = min(n_headlines / 10, 1.0) * abs(compound)

        score = SentimentScore(
            value=round(value, 4),
            confidence=round(confidence, 4),
            metadata={
                "symbol": symbol,
                "n_items": n_headlines,
                "compound": round(compound, 6),
            },
        )

        logger.debug(
            "VADERSentimentAnalyzer %s: n=%d compound=%.4f value=%.2f conf=%.4f",
            symbol, n_headlines, compound, score.value, score.confidence,
        )

        return Ok(score)
