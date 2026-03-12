"""Regime indicator fetcher using yfinance for VIX/S&P500/yield data.

Fetches market-wide regime indicators as time series for storage in DuckDB.
Unlike core/data/market.py (which returns cached point-in-time values),
this client returns full historical DataFrames for trend analysis.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf


class RegimeDataClient:
    """Fetches regime indicator data from yfinance.

    Indicators:
        - VIX (^VIX): Volatility index
        - S&P 500 (^GSPC): Close, 200-day MA, ratio
        - Yield curve (^TNX, ^IRX): 10Y-3M spread in basis points
    """

    def fetch_regime_snapshot(self) -> dict:
        """Fetch current regime indicator values.

        Returns a dict with keys: date, vix, sp500_close, sp500_ma200,
        sp500_ratio, yield_10y, yield_3m, yield_spread_bps,
        adx, yield_spread.
        """
        from core.data.indicators import adx as compute_adx

        sp500_df = yf.Ticker("^GSPC").history(period="1y")
        vix_df = yf.Ticker("^VIX").history(period="5d")
        tnx_df = yf.Ticker("^TNX").history(period="5d")
        irx_df = yf.Ticker("^IRX").history(period="5d")

        sp500_close = float(sp500_df["Close"].iloc[-1])
        sp500_ma200 = float(sp500_df["Close"].rolling(200).mean().iloc[-1])
        sp500_ratio = sp500_close / sp500_ma200

        vix = float(vix_df["Close"].iloc[-1])
        yield_10y = float(tnx_df["Close"].iloc[-1])
        yield_3m = float(irx_df["Close"].iloc[-1])
        yield_spread_bps = (yield_10y - yield_3m) * 100

        # Compute ADX(14) from S&P500 OHLCV
        ohlcv = sp500_df.rename(
            columns={"High": "high", "Low": "low", "Close": "close"}
        )
        adx_series = compute_adx(ohlcv, 14)
        adx_value = float(adx_series.iloc[-1])

        return {
            "date": date.today(),
            "vix": vix,
            "sp500_close": sp500_close,
            "sp500_ma200": sp500_ma200,
            "sp500_ratio": sp500_ratio,
            "yield_10y": yield_10y,
            "yield_3m": yield_3m,
            "yield_spread_bps": yield_spread_bps,
            "adx": adx_value,
            "yield_spread": yield_spread_bps / 100,
        }

    def fetch_regime_history(self, years: int = 2) -> pd.DataFrame:
        """Fetch full time series of regime indicators.

        Args:
            years: Number of years of history to fetch (default 2).

        Returns:
            DataFrame with columns: date, vix, sp500_close, sp500_ma200,
            sp500_ratio, yield_10y, yield_3m, yield_spread_bps.
            Forward-fills NaN from index misalignment.
        """
        period = f"{years}y"

        sp500_df = yf.Ticker("^GSPC").history(period=period)
        vix_df = yf.Ticker("^VIX").history(period=period)
        tnx_df = yf.Ticker("^TNX").history(period=period)
        irx_df = yf.Ticker("^IRX").history(period=period)

        # Normalize index to date (remove timezone info from yfinance)
        sp500_close = sp500_df["Close"].rename("sp500_close")
        sp500_close.index = sp500_close.index.date

        sp500_ma200 = sp500_df["Close"].rolling(200).mean().rename("sp500_ma200")
        sp500_ma200.index = sp500_ma200.index.date

        vix_series = vix_df["Close"].rename("vix")
        vix_series.index = vix_series.index.date

        tnx_series = tnx_df["Close"].rename("yield_10y")
        tnx_series.index = tnx_series.index.date

        irx_series = irx_df["Close"].rename("yield_3m")
        irx_series.index = irx_series.index.date

        # Combine on date index, forward-fill misaligned dates
        combined = pd.concat(
            [sp500_close, sp500_ma200, vix_series, tnx_series, irx_series],
            axis=1,
        )
        combined = combined.ffill()

        # Compute derived columns
        combined["sp500_ratio"] = combined["sp500_close"] / combined["sp500_ma200"]
        combined["yield_spread_bps"] = (
            combined["yield_10y"] - combined["yield_3m"]
        ) * 100

        # Reset index to column
        combined.index.name = "date"
        combined = combined.reset_index()

        return combined[
            [
                "date",
                "vix",
                "sp500_close",
                "sp500_ma200",
                "sp500_ratio",
                "yield_10y",
                "yield_3m",
                "yield_spread_bps",
            ]
        ]
