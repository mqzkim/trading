"""Data preprocessing pipeline for OHLCV and fundamental data."""
import pandas as pd
import numpy as np


def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Clip values to [lower, upper] percentile bounds."""
    lo = series.quantile(lower)
    hi = series.quantile(upper)
    return series.clip(lo, hi)


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill then drop remaining NaN rows."""
    return df.ffill().dropna()


def preprocess_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean OHLCV dataframe.
    Expects columns: open, high, low, close, volume, adj_close (optional).
    Returns df with adjusted close as 'close' and outliers winsorized.
    """
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    # Use adjusted close if available
    if "adj_close" in df.columns:
        df["close"] = df["adj_close"]
        df.drop(columns=["adj_close"], inplace=True)

    # Winsorize returns column (skip volume)
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = winsorize(df[col])

    df = fill_missing(df)
    return df[["open", "high", "low", "close", "volume"]]


def normalize_fundamentals(data: dict) -> dict:
    """Convert None values and string numbers in fundamental data to float."""
    def _cast(v):
        if v is None:
            return float("nan")
        try:
            return float(v)
        except (TypeError, ValueError):
            return v

    return {k: _cast(v) if not isinstance(v, dict) else normalize_fundamentals(v)
            for k, v in data.items()}
