"""Unit tests for RealSentimentAdapter — external calls fully mocked.

Phase 27-02: Tests adapter logic by mocking yfinance, Alpaca News, and VADER.
No real API calls are made.

Note: yfinance is imported locally inside each method as `import yfinance as yf`,
so we patch it at `yfinance.Ticker` (the underlying module), not the adapter module.
"""
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from src.scoring.infrastructure.core_scoring_adapter import RealSentimentAdapter
from src.scoring.domain.value_objects import SentimentConfidence


REQUIRED_KEYS = {
    "sentiment_score",
    "news_score",
    "insider_score",
    "institutional_score",
    "analyst_score",
    "confidence",
}


# -- Helper: build minimal yfinance mock with empty data -----------------------


def _make_empty_ticker() -> MagicMock:
    """Return a Ticker mock where all data properties return empty DataFrames."""
    ticker = MagicMock()
    ticker.recommendations = pd.DataFrame()
    ticker.analyst_price_targets = {}
    ticker.insider_transactions = pd.DataFrame()
    ticker.institutional_holders = pd.DataFrame()
    ticker.info = {}
    return ticker


def _make_bullish_ticker(strong_buy: int, buy: int, hold: int, sell: int, strong_sell: int) -> MagicMock:
    """Return ticker with recommendation data and empty other fields."""
    ticker = MagicMock()
    rec_df = pd.DataFrame([{
        "strongBuy": strong_buy, "buy": buy,
        "hold": hold, "sell": sell, "strongSell": strong_sell,
    }])
    ticker.recommendations = rec_df
    ticker.analyst_price_targets = {}
    ticker.insider_transactions = pd.DataFrame()
    ticker.institutional_holders = pd.DataFrame()
    ticker.info = {}
    return ticker


# -- Required keys -------------------------------------------------------------


class TestGetReturnsRequiredKeys:
    """adapter.get() always returns all required keys."""

    @patch("yfinance.Ticker")
    def test_get_returns_required_keys(self, mock_ticker_cls: MagicMock) -> None:
        mock_ticker_cls.return_value = _make_empty_ticker()
        adapter = RealSentimentAdapter(alpaca_key=None, alpaca_secret=None)
        result = adapter.get("AAPL")
        assert REQUIRED_KEYS.issubset(result.keys()), (
            f"Missing keys: {REQUIRED_KEYS - result.keys()}"
        )

    @patch("yfinance.Ticker")
    def test_confidence_is_sentimentconfidence_enum(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        mock_ticker_cls.return_value = _make_empty_ticker()
        adapter = RealSentimentAdapter(alpaca_key=None)
        result = adapter.get("MSFT")
        assert isinstance(result["confidence"], SentimentConfidence)

    @patch("yfinance.Ticker")
    def test_sentiment_score_in_range(self, mock_ticker_cls: MagicMock) -> None:
        mock_ticker_cls.return_value = _make_empty_ticker()
        adapter = RealSentimentAdapter()
        result = adapter.get("GOOG")
        assert 0 <= result["sentiment_score"] <= 100


# -- Confidence: all fail → NONE -----------------------------------------------


class TestConfidenceNoneWhenAllFail:
    """When all 4 sources raise exceptions, confidence=NONE and score=50.0."""

    @patch("yfinance.Ticker")
    def test_all_sources_fail_gives_none_confidence(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        mock_ticker_cls.side_effect = Exception("yfinance unavailable")
        adapter = RealSentimentAdapter(alpaca_key=None)
        result = adapter.get("FAIL")
        assert result["confidence"] == SentimentConfidence.NONE

    @patch("yfinance.Ticker")
    def test_all_sources_fail_gives_neutral_score(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        mock_ticker_cls.side_effect = Exception("yfinance unavailable")
        adapter = RealSentimentAdapter(alpaca_key=None)
        result = adapter.get("FAIL")
        assert result["sentiment_score"] == 50.0

    @patch("yfinance.Ticker")
    def test_all_sources_fail_all_sub_scores_none(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        mock_ticker_cls.side_effect = Exception("yfinance unavailable")
        adapter = RealSentimentAdapter(alpaca_key=None)
        result = adapter.get("FAIL")
        assert result["news_score"] is None
        assert result["insider_score"] is None
        assert result["institutional_score"] is None
        assert result["analyst_score"] is None


# -- Confidence: all 4 sources available → HIGH --------------------------------


class TestConfidenceHighWhenAllAvailable:
    """When all 4 sources return data, confidence=HIGH."""

    @patch("yfinance.Ticker")
    def test_all_4_sources_available_gives_high_confidence(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        # Build a ticker that returns valid data for all 3 yfinance sources
        ticker = MagicMock()

        # Recommendations: strongBuy=10, buy=5, hold=3, sell=1, strongSell=1
        rec_df = pd.DataFrame([
            {"strongBuy": 10, "buy": 5, "hold": 3, "sell": 1, "strongSell": 1}
        ])
        ticker.recommendations = rec_df

        # Insider transactions: some buys (within last 180 days)
        insider_df = pd.DataFrame([
            {"Start Date": pd.Timestamp.now(), "Transaction": "Purchase"},
            {"Start Date": pd.Timestamp.now(), "Transaction": "Purchase"},
            {"Start Date": pd.Timestamp.now(), "Transaction": "Sale"},
        ])
        ticker.insider_transactions = insider_df

        # Institutional holders: 2 rows with % Out data
        inst_df = pd.DataFrame([
            {"% Out": 0.08},
            {"% Out": 0.05},
        ])
        ticker.institutional_holders = inst_df

        # Analyst price targets + current price
        ticker.analyst_price_targets = {"mean": 300.0}
        ticker.info = {"currentPrice": 250.0}

        mock_ticker_cls.return_value = ticker

        # Mock the 4th source: news via _fetch_news_sentiment returning 70.0
        with patch.object(
            RealSentimentAdapter, "_fetch_news_sentiment", return_value=70.0
        ):
            adapter = RealSentimentAdapter(alpaca_key="key", alpaca_secret="secret")
            result = adapter.get("AAPL")

        assert result["confidence"] == SentimentConfidence.HIGH, (
            f"Expected HIGH confidence, got {result['confidence']}"
        )


# -- Confidence: 3 sources → MEDIUM -------------------------------------------


class TestConfidenceMediumWhen3Available:
    """When exactly 3 sources return data (1 fails), confidence=MEDIUM."""

    @patch("yfinance.Ticker")
    def test_3_sources_gives_medium_confidence(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        ticker = MagicMock()

        # Recommendations: valid data
        rec_df = pd.DataFrame([{
            "strongBuy": 8, "buy": 4, "hold": 3, "sell": 1, "strongSell": 0
        }])
        ticker.recommendations = rec_df

        # Institutional: valid data (2 rows with different % Out values)
        inst_df = pd.DataFrame([{"% Out": 0.06}, {"% Out": 0.04}])
        ticker.institutional_holders = inst_df

        # Analyst: valid price target
        ticker.analyst_price_targets = {"mean": 280.0}
        ticker.info = {"currentPrice": 250.0}

        # Insider: valid data with recent buys (3rd source)
        insider_df = pd.DataFrame([
            {"Start Date": pd.Timestamp.now(), "Transaction": "Purchase"},
            {"Start Date": pd.Timestamp.now(), "Transaction": "Sale"},
        ])
        ticker.insider_transactions = insider_df

        mock_ticker_cls.return_value = ticker

        # 4th source: no news (alpaca_key=None → news_score=None)
        adapter = RealSentimentAdapter(alpaca_key=None)
        result = adapter.get("AAPL")

        # Available: recommendations + institutional + analyst + insider = 4 possible
        # But news=None (no key) → 3 from yfinance, 0 news = 3 total → MEDIUM
        # Wait: insider might return None if dates don't match — ensure it returns a score
        # confidence_map: {3: MEDIUM}
        assert result["confidence"] == SentimentConfidence.MEDIUM, (
            f"Expected MEDIUM, got {result['confidence']} "
            f"(analyst={result['analyst_score']}, inst={result['institutional_score']}, "
            f"insider={result['insider_score']}, news={result['news_score']})"
        )


# -- Analyst score: bullish ratio ----------------------------------------------


class TestAnalystScoreBullishRatio:
    """Analyst score uses strongBuy+buy / total bullish ratio."""

    @patch("yfinance.Ticker")
    def test_bullish_majority_gives_high_analyst_score(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        """strongBuy=10, buy=10, hold=5, sell=0, strongSell=0 → bullish_ratio=20/25=0.8 → >70."""
        mock_ticker_cls.return_value = _make_bullish_ticker(
            strong_buy=10, buy=10, hold=5, sell=0, strong_sell=0
        )
        adapter = RealSentimentAdapter(alpaca_key=None)
        result = adapter.get("BULL")
        assert result["analyst_score"] is not None
        # bullish_ratio = 20/25 = 0.8 → bullish_score = 80.0 (no price target)
        assert result["analyst_score"] > 70, (
            f"Expected analyst_score > 70 for bullish majority, got {result['analyst_score']}"
        )

    @patch("yfinance.Ticker")
    def test_bearish_majority_gives_low_analyst_score(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        """strongBuy=0, buy=2, hold=10, sell=8, strongSell=5 → bullish=2/25=0.08 → <40."""
        mock_ticker_cls.return_value = _make_bullish_ticker(
            strong_buy=0, buy=2, hold=10, sell=8, strong_sell=5
        )
        adapter = RealSentimentAdapter(alpaca_key=None)
        result = adapter.get("BEAR")
        assert result["analyst_score"] is not None
        # bullish_ratio = 2/25 = 0.08 → bullish_score = 8.0 → <40
        assert result["analyst_score"] < 40, (
            f"Expected analyst_score < 40 for bearish majority, got {result['analyst_score']}"
        )


# -- No Alpaca keys → news_score=None ------------------------------------------


class TestNoAlpacaKeysSkipsNews:
    """Without Alpaca keys, news_score is None (no API call attempted)."""

    @patch("yfinance.Ticker")
    def test_no_alpaca_keys_news_score_is_none(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        mock_ticker_cls.return_value = _make_empty_ticker()
        adapter = RealSentimentAdapter(alpaca_key=None, alpaca_secret=None)
        result = adapter.get("AAPL")
        assert result["news_score"] is None

    def test_no_alpaca_keys_news_fetch_returns_none_directly(self) -> None:
        """_fetch_news_sentiment returns None immediately when no keys."""
        adapter = RealSentimentAdapter(alpaca_key=None, alpaca_secret=None)
        # Call _fetch_news_sentiment directly — should return None without any API call
        result = adapter._fetch_news_sentiment("AAPL")
        assert result is None


# -- Graceful degradation: empty DataFrames ------------------------------------


class TestGracefulDegradationEmptyDataFrames:
    """Empty DataFrames from yfinance return None sub-scores."""

    @patch("yfinance.Ticker")
    def test_empty_insider_df_gives_none_insider_score(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        ticker = _make_empty_ticker()
        ticker.insider_transactions = pd.DataFrame()
        mock_ticker_cls.return_value = ticker

        adapter = RealSentimentAdapter(alpaca_key=None)
        result = adapter.get("AAPL")
        assert result["insider_score"] is None

    @patch("yfinance.Ticker")
    def test_empty_institutional_df_gives_none_institutional_score(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        ticker = _make_empty_ticker()
        ticker.institutional_holders = pd.DataFrame()
        mock_ticker_cls.return_value = ticker

        adapter = RealSentimentAdapter(alpaca_key=None)
        result = adapter.get("AAPL")
        assert result["institutional_score"] is None

    @patch("yfinance.Ticker")
    def test_empty_recommendations_gives_none_analyst_score(
        self, mock_ticker_cls: MagicMock
    ) -> None:
        ticker = _make_empty_ticker()
        ticker.recommendations = pd.DataFrame()
        ticker.analyst_price_targets = {}
        mock_ticker_cls.return_value = ticker

        adapter = RealSentimentAdapter(alpaca_key=None)
        result = adapter.get("AAPL")
        assert result["analyst_score"] is None


# -- VADER news compound mapping -----------------------------------------------


class TestNewsVADERCompoundMapping:
    """News score maps VADER compound from [-1,+1] to [0,100]."""

    def test_news_vader_compound_0_5_maps_to_75(self) -> None:
        """compound=0.5 → (0.5+1)/2*100 = 75.0."""
        adapter = RealSentimentAdapter(alpaca_key="key", alpaca_secret="secret")

        # Build mock articles
        mock_articles = []
        for _ in range(5):
            article = MagicMock()
            article.headline = "Stock rises on strong earnings report"
            mock_articles.append(article)

        mock_response = MagicMock()
        mock_response.news = mock_articles

        # Mock VADER to always return compound=0.5
        mock_analyzer = MagicMock()
        mock_analyzer.polarity_scores.return_value = {"compound": 0.5}

        with patch("alpaca.data.historical.news.NewsClient") as mock_nc, \
             patch("alpaca.data.requests.NewsRequest"), \
             patch("vaderSentiment.vaderSentiment.SentimentIntensityAnalyzer") as mock_vader:
            mock_nc.return_value.get_news.return_value = mock_response
            mock_vader.return_value = mock_analyzer

            result = adapter._fetch_news_sentiment("AAPL")

        assert result is not None
        # compound=0.5 → (0.5+1.0)/2.0*100 = 75.0
        assert abs(result - 75.0) < 1.0, f"Expected ~75.0, got {result}"

    def test_news_vader_negative_compound_maps_below_50(self) -> None:
        """Negative compound → score < 50."""
        adapter = RealSentimentAdapter(alpaca_key="key", alpaca_secret="secret")

        mock_articles = [MagicMock() for _ in range(5)]
        for a in mock_articles:
            a.headline = "Stock drops on weak guidance"

        mock_response = MagicMock()
        mock_response.news = mock_articles

        mock_analyzer = MagicMock()
        mock_analyzer.polarity_scores.return_value = {"compound": -0.4}

        with patch("alpaca.data.historical.news.NewsClient") as mock_nc, \
             patch("alpaca.data.requests.NewsRequest"), \
             patch("vaderSentiment.vaderSentiment.SentimentIntensityAnalyzer") as mock_vader:
            mock_nc.return_value.get_news.return_value = mock_response
            mock_vader.return_value = mock_analyzer

            result = adapter._fetch_news_sentiment("AAPL")

        assert result is not None
        # compound=-0.4 → (-0.4+1.0)/2.0*100 = 30.0
        assert result < 50.0, f"Expected < 50 for negative compound, got {result}"
