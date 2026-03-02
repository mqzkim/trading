"""DataClient: EODHD (Phase 1) with yfinance fallback.

Usage:
    client = DataClient()
    result = client.get_price_history("AAPL", days=756)
    result = client.get_fundamentals("AAPL")
    result = client.get_full("AAPL")
"""
import os
import logging
from typing import Any

import pandas as pd
import yfinance as yf
import requests
from dotenv import load_dotenv

from . import cache, indicators, preprocessor

load_dotenv()
logger = logging.getLogger(__name__)

EODHD_BASE = "https://eodhd.com/api"


class DataClient:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.getenv("EODHD_API_KEY")
        self._use_eodhd = bool(self._api_key)
        if not self._use_eodhd:
            logger.warning("EODHD_API_KEY not set — using yfinance fallback")

    # -- Price History ----------------------------------------------------------

    def get_price_history(self, symbol: str, days: int = 756) -> pd.DataFrame:
        """Return cleaned OHLCV DataFrame with 'days' trading days."""
        cache_key = f"price:{symbol}:{days}"
        cached = cache.get(cache_key)
        if cached is not None:
            return pd.DataFrame(cached)

        if self._use_eodhd:
            df = self._eodhd_price(symbol, days)
        else:
            df = self._yfinance_price(symbol, days)

        df = preprocessor.preprocess_ohlcv(df)
        cache.set(cache_key, df.to_dict(orient="list"), cache.PRICE_TTL)
        return df

    def _eodhd_price(self, symbol: str, days: int) -> pd.DataFrame:
        """Fetch OHLCV from EODHD."""
        import math
        from datetime import date, timedelta

        end = date.today()
        # approximate: 756 trading days ~ 1050 calendar days (3 years)
        start = end - timedelta(days=math.ceil(days * 1.4))
        params = {
            "api_token": self._api_key,
            "fmt": "json",
            "from": start.isoformat(),
            "to": end.isoformat(),
        }
        url = f"{EODHD_BASE}/eod/{symbol}"
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").rename(
            columns={"open": "open", "high": "high", "low": "low",
                     "close": "close", "adjusted_close": "adj_close",
                     "volume": "volume"}
        )
        return df.tail(days)

    def _yfinance_price(self, symbol: str, days: int) -> pd.DataFrame:
        """Fetch OHLCV from yfinance (fallback)."""
        period = "5y" if days > 504 else "3y"
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, auto_adjust=True)
        df.columns = [c.lower() for c in df.columns]
        df = df[["open", "high", "low", "close", "volume"]].tail(days)
        return df

    # -- Fundamentals -----------------------------------------------------------

    def get_fundamentals(self, symbol: str) -> dict[str, Any]:
        """Return parsed fundamental data dict."""
        cache_key = f"fundamentals:{symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        if self._use_eodhd:
            data = self._eodhd_fundamentals(symbol)
        else:
            data = self._yfinance_fundamentals(symbol)

        data = preprocessor.normalize_fundamentals(data)
        cache.set(cache_key, data, cache.FUNDAMENTALS_TTL)
        return data

    def _eodhd_fundamentals(self, symbol: str) -> dict:
        url = f"{EODHD_BASE}/fundamentals/{symbol}"
        resp = requests.get(url, params={"api_token": self._api_key, "fmt": "json"}, timeout=30)
        resp.raise_for_status()
        raw = resp.json()
        return {
            "income": raw.get("Financials", {}).get("Income_Statement", {}).get("quarterly", {}),
            "balance": raw.get("Financials", {}).get("Balance_Sheet", {}).get("quarterly", {}),
            "cashflow": raw.get("Financials", {}).get("Cash_Flow", {}).get("quarterly", {}),
            "highlights": raw.get("Highlights", {}),
            "valuation": raw.get("Valuation", {}),
        }

    def _yfinance_fundamentals(self, symbol: str) -> dict:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        return {
            "income": {},
            "balance": {},
            "cashflow": {},
            "highlights": {
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "revenue": info.get("totalRevenue"),
                "net_income": info.get("netIncomeToCommon"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "roa": info.get("returnOnAssets"),
                "roe": info.get("returnOnEquity"),
                "fcf": info.get("freeCashflow"),
            },
            "valuation": {
                "pb": info.get("priceToBook"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
            },
        }

    # -- Full Data Package ------------------------------------------------------

    def get_full(self, symbol: str, days: int = 756) -> dict[str, Any]:
        """Return complete data package: OHLCV + indicators + fundamentals."""
        df = self.get_price_history(symbol, days)
        ind = indicators.compute_all(df)

        # Get latest values for indicators
        def last(s: pd.Series) -> float:
            v = s.dropna()
            return float(v.iloc[-1]) if len(v) > 0 else float("nan")

        return {
            "symbol": symbol,
            "price": {
                "open": float(df["open"].iloc[-1]),
                "high": float(df["high"].iloc[-1]),
                "low": float(df["low"].iloc[-1]),
                "close": float(df["close"].iloc[-1]),
                "volume": float(df["volume"].iloc[-1]),
            },
            "indicators": {
                "ma50": last(ind["ma50"]),
                "ma200": last(ind["ma200"]),
                "rsi14": last(ind["rsi14"]),
                "atr21": last(ind["atr21"]),
                "adx14": last(ind["adx14"]),
                "obv": last(ind["obv"]),
                "macd": last(ind["macd"]),
                "macd_signal": last(ind["macd_signal"]),
                "macd_histogram": last(ind["macd_histogram"]),
            },
            "fundamentals": self.get_fundamentals(symbol),
            "history_days": len(df),
        }
