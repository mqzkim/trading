"""Market-wide indicator collection using yfinance as primary source."""
import yfinance as yf
import pandas as pd
from . import cache


def _fetch(ticker: str, period: str = "1y") -> pd.DataFrame:
    return yf.Ticker(ticker).history(period=period, auto_adjust=True)


def get_vix() -> float:
    """Current VIX level."""
    cache_key = "market:vix"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    df = _fetch("^VIX", "5d")
    value = float(df["Close"].iloc[-1])
    cache.set(cache_key, value, cache.MARKET_TTL)
    return value


def get_sp500_vs_200ma() -> float:
    """S&P 500 close / 200-day MA -- ratio above 1.0 means bullish."""
    cache_key = "market:sp500_vs_200ma"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    df = _fetch("^GSPC", "2y")
    close = df["Close"]
    ma200 = close.rolling(200).mean()
    ratio = float(close.iloc[-1] / ma200.iloc[-1])
    cache.set(cache_key, ratio, cache.MARKET_TTL)
    return ratio


def get_yield_curve_slope() -> float:
    """10Y - 3M yield spread (basis points). Negative = inverted."""
    cache_key = "market:yield_curve"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    ten_year = yf.Ticker("^TNX").history(period="5d")["Close"].iloc[-1]
    three_month = yf.Ticker("^IRX").history(period="5d")["Close"].iloc[-1]
    spread = float((ten_year - three_month) * 100)  # convert % to bps
    cache.set(cache_key, spread, cache.MARKET_TTL)
    return spread


def get_all() -> dict:
    """Return all market indicators as a dict."""
    return {
        "vix": get_vix(),
        "sp500_vs_200ma": get_sp500_vs_200ma(),
        "yield_curve_slope_bps": get_yield_curve_slope(),
    }
