"""QualityChecker — data quality validation pipeline.

Validates OHLCV data for missing values, stale data, and outliers.
Validates financial data for required fields and filing_date presence.
Produces DataQualityReport VOs with specific failure reasons.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from src.data_ingest.domain.value_objects import DataQualityReport

logger = logging.getLogger(__name__)

# Required financial fields for quality validation
_REQUIRED_FINANCIAL_FIELDS = frozenset({"revenue", "total_assets", "net_income"})

# Minimum quarters for valid financial data
_MIN_QUARTERS = 1


class QualityChecker:
    """Validates data quality before downstream consumption.

    OHLCV checks:
    - Missing values: >5% total cells missing = fail
    - Stale data: >3 days since last data point = fail
    - Outliers: >1% of rows with 3-sigma outliers = fail

    Financial checks:
    - Required fields: revenue, total_assets, net_income must be present
    - Minimum quarters: at least 1 quarter of data required
    - Filing date: filing_date must be present (point-in-time requirement)
    """

    def validate_ohlcv(
        self,
        ticker: str,
        df: pd.DataFrame,
        max_stale_days: int = 3,
        now: pd.Timestamp | None = None,
    ) -> DataQualityReport:
        """Validate OHLCV DataFrame quality.

        Args:
            ticker: Stock symbol.
            df: OHLCV DataFrame with DatetimeIndex.
            max_stale_days: Maximum allowed business days since last data point.
            now: Override current timestamp for testing (default: now).

        Returns:
            DataQualityReport VO with pass/fail and specific failure reasons.
        """
        failures: list[str] = []

        # 1. Missing values check (>5% = fail)
        total_cells = df.shape[0] * df.shape[1]
        missing_count = int(df.isnull().sum().sum())
        missing_pct = (missing_count / total_cells * 100) if total_cells > 0 else 0.0

        if missing_pct > 5.0:
            failures.append(f"Missing values: {missing_pct:.1f}% (threshold: 5%)")

        # 2. Stale data check using business days (>max_stale_days = fail)
        stale_days = 0
        if len(df) > 0:
            last_date = pd.Timestamp(df.index.max())
            current = now if now is not None else pd.Timestamp.now().normalize()
            stale_days = int(
                np.busday_count(last_date.date(), current.date())
            )

            if stale_days > max_stale_days:
                failures.append(
                    f"Stale data: {stale_days} business days since last update "
                    f"(threshold: {max_stale_days})"
                )

        # 3. Outlier check (3-sigma, >1% of rows = fail)
        price_cols = [c for c in ("open", "high", "low", "close") if c in df.columns]
        outlier_count = 0

        for col in price_cols:
            series = df[col].dropna()
            if len(series) < 2:
                continue
            mean = series.mean()
            std = series.std()
            if std > 0:
                outliers = ((series - mean).abs() > 3 * std).sum()
                outlier_count += int(outliers)

        outlier_threshold = max(1, int(len(df) * 0.01))
        if outlier_count > outlier_threshold:
            failures.append(
                f"Excessive outliers: {outlier_count} "
                f"(threshold: {outlier_threshold}, 1% of {len(df)} rows)"
            )

        return DataQualityReport(
            ticker=ticker,
            passed=len(failures) == 0,
            missing_pct=round(missing_pct, 2),
            stale_days=stale_days,
            outlier_count=outlier_count,
            failures=tuple(failures),
        )

    def validate_financials(
        self,
        ticker: str,
        records: list[dict[str, Any]],
    ) -> DataQualityReport:
        """Validate financial data quality.

        Args:
            ticker: Stock symbol.
            records: List of financial record dicts from EdgartoolsClient.

        Returns:
            DataQualityReport VO with pass/fail and specific failure reasons.
        """
        failures: list[str] = []

        # 1. Minimum quarters check
        if len(records) < _MIN_QUARTERS:
            failures.append(
                f"Insufficient data: {len(records)} quarters "
                f"(minimum: {_MIN_QUARTERS})"
            )

        # 2. Required fields check
        missing_fields: set[str] = set()
        for record in records:
            for field in _REQUIRED_FINANCIAL_FIELDS:
                if field not in record:
                    missing_fields.add(field)

        if missing_fields:
            failures.append(
                f"Missing required fields: {sorted(missing_fields)}"
            )

        # 3. Filing date presence check (strict point-in-time)
        missing_filing_date = sum(
            1 for r in records if "filing_date" not in r or r["filing_date"] is None
        )
        if missing_filing_date > 0 and len(records) > 0:
            failures.append(
                f"Missing filing_date in {missing_filing_date}/{len(records)} records "
                "(required for point-in-time correctness)"
            )

        return DataQualityReport(
            ticker=ticker,
            passed=len(failures) == 0,
            missing_pct=0.0,
            stale_days=0,
            outlier_count=0,
            failures=tuple(failures),
        )
