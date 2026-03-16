"""CoreScoringAdapter -- DDD infrastructure adapter wrapping core scoring functions.

Bridges the DDD scoring bounded context with existing proven scoring logic
in core/scoring/. Does NOT rewrite scoring math -- only adapts interfaces.

Wrapped functions:
  core.scoring.safety: altman_z_score, beneish_m_score
  core.scoring.fundamental: piotroski_f_score, compute_fundamental_score

TechnicalIndicatorAdapter:
  Bridges core.data.indicators to TechnicalScoringService (domain).
  The ONLY place pandas touches the domain -- extracts float values from Series.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

from core.data import indicators
from core.data.client import DataClient
from core.scoring.safety import altman_z_score, beneish_m_score
from core.scoring.fundamental import piotroski_f_score, compute_fundamental_score, mohanram_g_score

from src.scoring.domain.value_objects import SafetyGate, TechnicalScore
from src.scoring.domain.services import TechnicalScoringService


class CoreScoringAdapter:
    """Infrastructure adapter wrapping core/scoring/ functions for DDD compliance.

    This adapter translates between DDD-style dict inputs and the positional
    arguments expected by core scoring functions. It also maps results to
    domain Value Objects (SafetyGate).
    """

    def compute_altman_z(self, financial_data: dict[str, Any]) -> float:
        """Compute Altman Z-Score from financial data dict.

        Args:
            financial_data: Dict with keys: working_capital, total_assets,
                retained_earnings, ebit, market_cap, total_liabilities, revenue.

        Returns:
            Float Z-Score. > 1.81 = safe zone, < 1.81 = distress zone.
        """
        return altman_z_score(
            working_capital=financial_data.get("working_capital", 0.0),
            total_assets=financial_data.get("total_assets", 0.0),
            retained_earnings=financial_data.get("retained_earnings", 0.0),
            ebit=financial_data.get("ebit", 0.0),
            market_cap=financial_data.get("market_cap", 0.0),
            total_liabilities=financial_data.get("total_liabilities", 0.0),
            revenue=financial_data.get("revenue", 0.0),
        )

    def compute_beneish_m(
        self, current: dict[str, Any], previous: dict[str, Any]
    ) -> float:
        """Compute Beneish M-Score from current and previous period data.

        Calculates the 8 M-Score input ratios from two periods,
        then delegates to core.scoring.safety.beneish_m_score().

        Args:
            current: Current period financials (receivables, revenue, etc.)
            previous: Previous period financials.

        Returns:
            Float M-Score. < -1.78 = clean, > -1.78 = possible manipulation.
        """

        def _safe_div(numerator: float, denominator: float, default: float = 1.0) -> float:
            if denominator == 0:
                return default
            return numerator / denominator

        # Extract current period
        recv_c = float(current.get("receivables", 0))
        rev_c = float(current.get("revenue", 1))
        gp_c = float(current.get("gross_profit", rev_c * 0.4))
        ta_c = float(current.get("total_assets", 1))
        ppe_c = float(current.get("ppe", ta_c * 0.3))
        depr_c = float(current.get("depreciation", ppe_c * 0.1))
        sga_c = float(current.get("sga", rev_c * 0.2))
        tl_c = float(current.get("total_liabilities", ta_c * 0.5))
        ni_c = float(current.get("net_income", 0))
        ocf_c = float(current.get("operating_cashflow", ni_c))

        # Extract previous period
        recv_p = float(previous.get("receivables", recv_c))
        rev_p = float(previous.get("revenue", rev_c))
        gp_p = float(previous.get("gross_profit", rev_p * 0.4))
        ta_p = float(previous.get("total_assets", ta_c))
        ppe_p = float(previous.get("ppe", ta_p * 0.3))
        depr_p = float(previous.get("depreciation", ppe_p * 0.1))
        sga_p = float(previous.get("sga", rev_p * 0.2))
        tl_p = float(previous.get("total_liabilities", ta_p * 0.5))

        # Calculate 8 M-Score input ratios
        # DSRI: Days Sales Receivable Index
        dsri = _safe_div(recv_c / max(rev_c, 1), recv_p / max(rev_p, 1))

        # GMI: Gross Margin Index
        gm_c = _safe_div(gp_c, rev_c, 0.4)
        gm_p = _safe_div(gp_p, rev_p, 0.4)
        gmi = _safe_div(gm_p, gm_c)

        # AQI: Asset Quality Index
        aq_c = 1.0 - _safe_div(ppe_c + ta_c * 0.1, ta_c, 0.5)
        aq_p = 1.0 - _safe_div(ppe_p + ta_p * 0.1, ta_p, 0.5)
        aqi = _safe_div(aq_c, aq_p)

        # SGI: Sales Growth Index
        sgi = _safe_div(rev_c, rev_p)

        # DEPI: Depreciation Index
        depr_rate_c = _safe_div(depr_c, depr_c + ppe_c, 0.1)
        depr_rate_p = _safe_div(depr_p, depr_p + ppe_p, 0.1)
        depi = _safe_div(depr_rate_p, depr_rate_c)

        # SGAI: SGA Expense Index
        sga_ratio_c = _safe_div(sga_c, rev_c, 0.2)
        sga_ratio_p = _safe_div(sga_p, rev_p, 0.2)
        sgai = _safe_div(sga_ratio_c, sga_ratio_p)

        # LVGI: Leverage Index
        lev_c = _safe_div(tl_c, ta_c, 0.5)
        lev_p = _safe_div(tl_p, ta_p, 0.5)
        lvgi = _safe_div(lev_c, lev_p)

        # TATA: Total Accruals to Total Assets
        tata = _safe_div(ni_c - ocf_c, ta_c, 0.0)

        return beneish_m_score(dsri, gmi, aqi, sgi, depi, sgai, lvgi, tata)

    def compute_piotroski_f(self, highlights: dict[str, Any]) -> int:
        """Compute Piotroski F-Score (0-9) from highlights dict.

        Args:
            highlights: Dict with keys: roa, fcf, debt_to_equity,
                current_ratio, roe, revenue, market_cap.

        Returns:
            Integer 0-9. Higher = stronger fundamentals.
        """
        return piotroski_f_score(highlights)

    def check_safety_gate(self, z_score: float, m_score: float) -> SafetyGate:
        """Create SafetyGate VO from Z-Score and M-Score.

        Args:
            z_score: Altman Z-Score value.
            m_score: Beneish M-Score value.

        Returns:
            SafetyGate VO with .passed property checking:
            Z > 1.81 AND M < -1.78
        """
        return SafetyGate(z_score=z_score, m_score=m_score)

    def compute_mohanram_g(self, data: dict[str, Any]) -> int:
        """Compute Mohanram G-Score (0-8) from financial data dict.

        Args:
            data: Dict with keys: roa, cfo_to_assets, cfo, net_income,
                roa_variance, sales_growth_variance, rd_to_assets,
                capex_to_assets, ad_to_assets, and sector_median_* versions.
                Missing R&D/advertising/capex default to 0.0 (conservative).

        Returns:
            Integer 0-8. Higher = better growth quality.
        """
        return mohanram_g_score(
            roa=data.get("roa", 0.0),
            cfo_to_assets=data.get("cfo_to_assets", 0.0),
            cfo=data.get("cfo", 0.0),
            net_income=data.get("net_income", 0.0),
            roa_variance=data.get("roa_variance", 0.0),
            sales_growth_variance=data.get("sales_growth_variance", 0.0),
            rd_to_assets=data.get("rd_to_assets", 0.0),
            capex_to_assets=data.get("capex_to_assets", 0.0),
            ad_to_assets=data.get("ad_to_assets", 0.0),
            sector_median_roa=data.get("sector_median_roa", 0.0),
            sector_median_cfo_to_assets=data.get("sector_median_cfo_to_assets", 0.0),
            sector_median_roa_variance=data.get("sector_median_roa_variance", 0.0),
            sector_median_sales_growth_variance=data.get("sector_median_sales_growth_variance", 0.0),
            sector_median_rd_to_assets=data.get("sector_median_rd_to_assets", 0.0),
            sector_median_capex_to_assets=data.get("sector_median_capex_to_assets", 0.0),
            sector_median_ad_to_assets=data.get("sector_median_ad_to_assets", 0.0),
        )

    def compute_full_fundamental(
        self, highlights: dict[str, Any], valuation: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute full fundamental score including safety + sub-scores.

        Delegates to core.scoring.fundamental.compute_fundamental_score().

        Args:
            highlights: Company financial highlights.
            valuation: Valuation metrics (pb, ev_ebitda, etc.)

        Returns:
            Dict with safety_passed, f_score, value_score, quality_score,
            fundamental_score (composite 0-100).
        """
        return compute_fundamental_score(highlights, valuation)


class FundamentalDataAdapter:
    """Infrastructure adapter providing fundamental data via .get(symbol).

    Wraps DataClient + CoreScoringAdapter to keep core/ imports out of handlers.
    """

    def __init__(
        self,
        data_client: DataClient | None = None,
        scoring_adapter: CoreScoringAdapter | None = None,
    ) -> None:
        self._client = data_client or DataClient()
        self._scoring = scoring_adapter or CoreScoringAdapter()

    def get(self, symbol: str) -> dict:
        """Fetch fundamental data and compute scores for a symbol."""
        fund_data = self._client.get_fundamentals(symbol)
        highlights = fund_data.get("highlights", {})
        valuation = fund_data.get("valuation", {})
        return compute_fundamental_score(highlights, valuation)


class SentimentDataAdapter:
    """Infrastructure adapter providing sentiment data via .get(symbol).

    Wraps core/scoring/sentiment to keep core/ imports out of handlers.
    Kept for backward compatibility -- use RealSentimentAdapter for live data.
    """

    def get(self, symbol: str) -> dict:
        """Compute sentiment score for a symbol."""
        from core.scoring.sentiment import compute_sentiment_score  # type: ignore[import-untyped]
        return compute_sentiment_score(symbol)  # type: ignore[arg-type]


class RealSentimentAdapter:
    """Infrastructure adapter fetching real sentiment data from 4 live sources.

    Sources:
      1. Alpaca News API + VADER — news sentiment
      2. yfinance insider_transactions — insider buy/sell ratio
      3. yfinance institutional_holders — institutional holdings QoQ change
      4. yfinance recommendations + analyst_price_targets — analyst sentiment

    All external calls are wrapped in try/except: returns None on failure.
    Confidence is determined by count of non-None sub-scores.
    """

    # Sub-score weights for composite sentiment (re-normalized if some missing)
    _WEIGHTS = {
        "news": 0.35,
        "insider": 0.25,
        "institutional": 0.20,
        "analyst": 0.20,
    }

    def __init__(
        self,
        alpaca_key: str | None = None,
        alpaca_secret: str | None = None,
    ) -> None:
        self._alpaca_key = alpaca_key
        self._alpaca_secret = alpaca_secret

    def get(self, symbol: str) -> dict:
        """Fetch all 4 sentiment sub-scores and return composite dict.

        Returns:
            Dict with keys:
              sentiment_score (0-100), news_score (float|None),
              insider_score (float|None), institutional_score (float|None),
              analyst_score (float|None), confidence (SentimentConfidence)
        """
        from src.scoring.domain.value_objects import SentimentConfidence

        news_score = self._fetch_news_sentiment(symbol)
        insider_score = self._fetch_insider_score(symbol)
        institutional_score = self._fetch_institutional_score(symbol)
        analyst_score = self._fetch_analyst_score(symbol)

        # Determine confidence from count of available sub-scores
        scores = {
            "news": news_score,
            "insider": insider_score,
            "institutional": institutional_score,
            "analyst": analyst_score,
        }
        available_count = sum(1 for v in scores.values() if v is not None)
        confidence_map = {
            0: SentimentConfidence.NONE,
            1: SentimentConfidence.LOW,
            2: SentimentConfidence.LOW,
            3: SentimentConfidence.MEDIUM,
            4: SentimentConfidence.HIGH,
        }
        confidence = confidence_map[available_count]

        # Compute composite sentiment as weighted average of available sub-scores
        if available_count > 0:
            total_weight = sum(
                self._WEIGHTS[k] for k, v in scores.items() if v is not None
            )
            composite = sum(
                self._WEIGHTS[k] * v
                for k, v in scores.items()
                if v is not None
            ) / total_weight
        else:
            composite = 50.0  # neutral fallback

        composite = max(0.0, min(100.0, composite))

        return {
            "sentiment_score": round(composite, 1),
            "news_score": news_score,
            "insider_score": insider_score,
            "institutional_score": institutional_score,
            "analyst_score": analyst_score,
            "confidence": confidence,
        }

    def _fetch_news_sentiment(self, symbol: str) -> float | None:
        """Fetch last 30 days of news from Alpaca, score with VADER.

        Returns:
            0-100 score or None if keys missing or < 3 articles found.
        """
        if not self._alpaca_key or not self._alpaca_secret:
            return None

        try:
            from alpaca.data.historical.news import NewsClient
            from alpaca.data.requests import NewsRequest
            from datetime import datetime, timedelta
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore[import-untyped]

            client = NewsClient(
                api_key=self._alpaca_key,
                secret_key=self._alpaca_secret,
            )
            start = datetime.utcnow() - timedelta(days=30)
            request = NewsRequest(symbols=symbol, start=start, limit=50)  # type: ignore[arg-type]
            news_response = client.get_news(request)

            # Extract articles from response
            articles = []
            if hasattr(news_response, "news"):
                articles = news_response.news
            elif isinstance(news_response, dict) and "news" in news_response:
                articles = news_response["news"]
            elif isinstance(news_response, list):
                articles = news_response

            if len(articles) < 3:
                return None

            analyzer = SentimentIntensityAnalyzer()
            compounds = []
            for article in articles:
                headline = ""
                if hasattr(article, "headline"):
                    headline = article.headline or ""
                elif isinstance(article, dict):
                    headline = article.get("headline", "")
                if headline:
                    score = analyzer.polarity_scores(headline)
                    compounds.append(score["compound"])

            if not compounds:
                return None

            avg_compound = sum(compounds) / len(compounds)
            # Map compound [-1, +1] to [0, 100]
            return round((avg_compound + 1.0) / 2.0 * 100.0, 1)

        except Exception:
            return None

    def _fetch_insider_score(self, symbol: str) -> float | None:
        """Fetch insider transactions via yfinance.

        Computes buy/(buy+sell) ratio over last 180 days.
        Returns 0-100 score or None if no data.
        """
        try:
            import yfinance as yf  # type: ignore[import-untyped]
            from datetime import datetime, timedelta

            ticker = yf.Ticker(symbol)
            df = ticker.insider_transactions
            if df is None or (hasattr(df, "empty") and df.empty):
                return None

            # Filter to last 180 days
            cutoff = datetime.now() - timedelta(days=180)
            if "Start Date" in df.columns:
                date_col = "Start Date"
            elif "Date" in df.columns:
                date_col = "Date"
            else:
                return None

            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df[df[date_col] >= pd.Timestamp(cutoff)]

            if df.empty:
                return None

            # Count buys and sells
            buys = 0
            sells = 0
            for _, row in df.iterrows():
                text = str(row.get("Transaction", row.get("Text", ""))).lower()
                if "buy" in text or "purchase" in text:
                    buys += 1
                elif "sell" in text or "sale" in text:
                    sells += 1

            total = buys + sells
            if total == 0:
                return None

            ratio = buys / total
            return round(ratio * 100.0, 1)

        except Exception:
            return None

    def _fetch_institutional_score(self, symbol: str) -> float | None:
        """Fetch institutional holdings via yfinance.

        Computes QoQ pctHeld change. Maps [-5%, +5%] change to [0, 100].
        Returns None if insufficient data.
        """
        try:
            import yfinance as yf  # type: ignore[import-untyped]

            ticker = yf.Ticker(symbol)
            df = ticker.institutional_holders
            if df is None or (hasattr(df, "empty") and df.empty):
                return None

            # Look for "% Out" or "pctHeld" column
            pct_col = None
            for col in ["% Out", "pctHeld", "Pct Held"]:
                if col in df.columns:
                    pct_col = col
                    break

            if pct_col is None or len(df) < 2:
                return None

            latest = float(df[pct_col].iloc[0]) if not pd.isna(df[pct_col].iloc[0]) else None
            prior = float(df[pct_col].iloc[1]) if not pd.isna(df[pct_col].iloc[1]) else None

            if latest is None or prior is None:
                return None

            # Handle percentage vs fraction (yfinance returns fractions like 0.03)
            if latest < 1.0:
                latest *= 100.0
            if prior < 1.0:
                prior *= 100.0

            change_pct = latest - prior
            # Map [-5%, +5%] change to [0, 100]
            score = max(0.0, min(100.0, (change_pct + 5.0) / 10.0 * 100.0))
            return round(score, 1)

        except Exception:
            return None

    def _fetch_analyst_score(self, symbol: str) -> float | None:
        """Fetch analyst recommendations and price targets via yfinance.

        Combines:
          - 60%: bullish_ratio from recommendations (strongBuy+buy / total)
          - 40%: upside_score from analyst price target vs current price

        Returns 0-100 score or None if no data.
        """
        try:
            import yfinance as yf  # type: ignore[import-untyped]

            ticker = yf.Ticker(symbol)

            # -- Analyst recommendations --
            recs = ticker.recommendations
            bullish_score: float | None = None

            if recs is not None and not (hasattr(recs, "empty") and recs.empty):
                # Get most recent period
                rec_row = recs.iloc[0] if len(recs) > 0 else None
                if rec_row is not None:
                    strong_buy = float(rec_row.get("strongBuy", 0) or 0)
                    buy = float(rec_row.get("buy", 0) or 0)
                    hold = float(rec_row.get("hold", 0) or 0)
                    sell = float(rec_row.get("sell", 0) or 0)
                    strong_sell = float(rec_row.get("strongSell", 0) or 0)
                    total = strong_buy + buy + hold + sell + strong_sell
                    if total > 0:
                        ratio = (strong_buy + buy) / total
                        bullish_score = round(ratio * 100.0, 1)

            # -- Analyst price targets --
            upside_score: float | None = None
            try:
                targets = ticker.analyst_price_targets
                current_price: float | None = None

                # Try to get current price
                info = ticker.info
                current_price = info.get("currentPrice") or info.get("regularMarketPrice")

                if targets and current_price and float(current_price) > 0:
                    mean_target = targets.get("mean") or targets.get("current")
                    if mean_target and float(mean_target) > 0:
                        upside_pct = (float(mean_target) - float(current_price)) / float(current_price) * 100
                        # Map [-20%, +40%] upside to [0, 100]
                        upside_score = max(0.0, min(100.0, (upside_pct + 20.0) / 60.0 * 100.0))
                        upside_score = round(upside_score, 1)
            except Exception:
                upside_score = None

            # Combine scores
            if bullish_score is not None and upside_score is not None:
                return round(0.6 * bullish_score + 0.4 * upside_score, 1)
            elif bullish_score is not None:
                return bullish_score
            elif upside_score is not None:
                return upside_score
            else:
                return None

        except Exception:
            return None


def _safe_last(s: pd.Series) -> float:
    """Extract last non-NaN value from a pandas Series, or NaN if empty."""
    v = s.dropna()
    return float(v.iloc[-1]) if len(v) > 0 else float("nan")


def _safe_float(val: float) -> float | None:
    """Convert float to float|None, replacing NaN with None."""
    if math.isnan(val):
        return None
    return val


class TechnicalIndicatorAdapter:
    """Infrastructure adapter bridging core/data/indicators to TechnicalScoringService.

    This is the ONLY place where pandas touches the domain layer.
    Extracts float values from pandas Series and passes only primitives to the
    domain service.
    """

    def __init__(
        self,
        data_client: DataClient | None = None,
        scoring_service: TechnicalScoringService | None = None,
    ) -> None:
        self._client = data_client or DataClient()
        self._service = scoring_service or TechnicalScoringService()

    def compute_technical_subscores(self, symbol: str, days: int = 756) -> TechnicalScore:
        """Compute full technical score with sub-score breakdown for a symbol.

        Flow:
          1. Fetch OHLCV via DataClient
          2. Compute all indicators via core.data.indicators.compute_all()
          3. Extract last float value from each Series (handle NaN)
          4. Compute OBV change percentage (60-day lookback)
          5. Pass floats to TechnicalScoringService.compute()

        Args:
            symbol: Stock ticker (e.g., "AAPL")
            days: Number of trading days of history to fetch

        Returns:
            TechnicalScore with 5 sub-scores and composite value
        """
        df = self._client.get_price_history(symbol, days)
        ind = indicators.compute_all(df)

        # Extract latest values as float | None
        rsi = _safe_float(_safe_last(ind["rsi14"]))
        macd_histogram = _safe_float(_safe_last(ind["macd_histogram"]))
        close = _safe_float(float(df["close"].iloc[-1])) if len(df) > 0 else None
        ma50 = _safe_float(_safe_last(ind["ma50"]))
        ma200 = _safe_float(_safe_last(ind["ma200"]))
        adx = _safe_float(_safe_last(ind["adx14"]))
        atr21 = _safe_float(_safe_last(ind["atr21"])) if "atr21" in ind else None

        # OBV change percentage (60-day lookback)
        obv_series = ind["obv"]
        obv_change_pct = self._compute_obv_change(obv_series)

        return self._service.compute(
            rsi=rsi,
            macd_histogram=macd_histogram,
            close=close,
            ma50=ma50,
            ma200=ma200,
            adx=adx,
            obv_change_pct=obv_change_pct,
            atr21=atr21,
        )

    def get(self, symbol: str, days: int = 756) -> dict:
        """Fetch OHLCV and return raw indicator values as dict.

        Returns dict with keys matching handler's expected format:
        technical_score, rsi, macd_histogram, close, ma50, ma200, adx, obv_change_pct.
        """
        from core.scoring.technical import compute_technical_score  # type: ignore[import-untyped]

        df = self._client.get_price_history(symbol, days)
        ind = indicators.compute_all(df)
        result = compute_technical_score(df, ind)

        # Merge raw indicator values for sub-score computation
        result["rsi"] = _safe_float(_safe_last(ind["rsi14"]))
        result["macd_histogram"] = _safe_float(_safe_last(ind["macd_histogram"]))
        result["close"] = _safe_float(float(df["close"].iloc[-1])) if len(df) > 0 else None
        result["ma50"] = _safe_float(_safe_last(ind["ma50"]))
        result["ma200"] = _safe_float(_safe_last(ind["ma200"]))
        result["adx"] = _safe_float(_safe_last(ind["adx14"]))
        result["obv_change_pct"] = self._compute_obv_change(ind["obv"])
        result["atr21"] = _safe_float(_safe_last(ind["atr21"])) if "atr21" in ind else None

        return result

    @staticmethod
    def _compute_obv_change(obv_series: pd.Series, lookback: int = 60) -> float | None:
        """Compute OBV percentage change over lookback period.

        Returns None if insufficient data.
        """
        clean = obv_series.dropna()
        if len(clean) < lookback:
            return None

        obv_recent = float(clean.iloc[-1])
        obv_past = float(clean.iloc[-lookback])

        if obv_past == 0:
            return None

        return (obv_recent - obv_past) / abs(obv_past) * 100
