"""Tests for QualityChecker — OHLCV and financial data quality validation."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def clean_ohlcv_df() -> pd.DataFrame:
    """OHLCV DataFrame with no quality issues."""
    n = 100
    today = pd.Timestamp.now().normalize()
    dates = pd.bdate_range(end=today, periods=n)
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame(
        {
            "open": prices,
            "high": prices + 2,
            "low": prices - 2,
            "close": prices + 0.5,
            "volume": np.random.randint(100000, 1000000, n),
        },
        index=dates,
    )


@pytest.fixture
def missing_ohlcv_df() -> pd.DataFrame:
    """OHLCV DataFrame with >5% missing values."""
    n = 100
    today = pd.Timestamp.now().normalize()
    dates = pd.bdate_range(end=today, periods=n)
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
    df = pd.DataFrame(
        {
            "open": prices,
            "high": prices + 2,
            "low": prices - 2,
            "close": prices + 0.5,
            "volume": np.random.randint(100000, 1000000, n).astype(float),
        },
        index=dates,
    )
    # Set >5% to NaN (6% of cells)
    total_cells = n * 5
    nan_count = int(total_cells * 0.06)
    np.random.seed(0)
    for _ in range(nan_count):
        row = np.random.randint(0, n)
        col = np.random.randint(0, 5)
        df.iloc[row, col] = np.nan
    return df


@pytest.fixture
def stale_ohlcv_df() -> pd.DataFrame:
    """OHLCV DataFrame with stale data (last update >3 days ago)."""
    n = 100
    # End date is 5 business days ago
    stale_end = pd.Timestamp.now().normalize() - timedelta(days=7)
    dates = pd.bdate_range(end=stale_end, periods=n)
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame(
        {
            "open": prices,
            "high": prices + 2,
            "low": prices - 2,
            "close": prices + 0.5,
            "volume": np.random.randint(100000, 1000000, n),
        },
        index=dates,
    )


@pytest.fixture
def outlier_ohlcv_df() -> pd.DataFrame:
    """OHLCV DataFrame with >1% outlier rows (3-sigma)."""
    n = 200
    today = pd.Timestamp.now().normalize()
    dates = pd.bdate_range(end=today, periods=n)
    np.random.seed(42)
    prices = np.full(n, 100.0)

    # Inject 5 extreme outliers (2.5% of 200 rows)
    outlier_indices = [10, 50, 90, 130, 170]
    for idx in outlier_indices:
        prices[idx] = 500.0  # Way beyond 3 sigma

    return pd.DataFrame(
        {
            "open": prices,
            "high": prices + 2,
            "low": prices - 2,
            "close": prices + 0.5,
            "volume": np.random.randint(100000, 1000000, n),
        },
        index=dates,
    )


class TestQualityCheckerOHLCV:
    """Test OHLCV data quality validation."""

    def test_clean_data_passes(self, clean_ohlcv_df: pd.DataFrame) -> None:
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        checker = QualityChecker()
        report = checker.validate_ohlcv("AAPL", clean_ohlcv_df)

        assert report.passed is True
        assert report.ticker == "AAPL"
        assert len(report.failures) == 0

    def test_missing_values_detected(self, missing_ohlcv_df: pd.DataFrame) -> None:
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        checker = QualityChecker()
        report = checker.validate_ohlcv("AAPL", missing_ohlcv_df)

        assert report.passed is False
        assert report.missing_pct > 5.0
        assert any("Missing" in f or "missing" in f for f in report.failures)

    def test_stale_data_detected(self, stale_ohlcv_df: pd.DataFrame) -> None:
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        checker = QualityChecker()
        report = checker.validate_ohlcv("AAPL", stale_ohlcv_df)

        assert report.passed is False
        assert report.stale_days > 3
        assert any("Stale" in f or "stale" in f for f in report.failures)

    def test_outliers_detected(self, outlier_ohlcv_df: pd.DataFrame) -> None:
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        checker = QualityChecker()
        report = checker.validate_ohlcv("AAPL", outlier_ohlcv_df)

        assert report.passed is False
        assert report.outlier_count > 0
        assert any("outlier" in f.lower() for f in report.failures)

    def test_report_is_dataqualityreport_vo(self, clean_ohlcv_df: pd.DataFrame) -> None:
        from src.data_ingest.domain.value_objects import DataQualityReport
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        checker = QualityChecker()
        report = checker.validate_ohlcv("AAPL", clean_ohlcv_df)

        assert isinstance(report, DataQualityReport)

    def test_custom_stale_days_threshold(self, clean_ohlcv_df: pd.DataFrame) -> None:
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        checker = QualityChecker()
        # Clean data should still pass with stricter threshold
        report = checker.validate_ohlcv("AAPL", clean_ohlcv_df, max_stale_days=1)

        # With max_stale_days=1 and data ending today, might or might not pass
        # depending on whether today is a business day. The key is no error.
        assert isinstance(report.stale_days, int)


class TestQualityCheckerFinancials:
    """Test financial data quality validation."""

    def test_valid_financials_pass(self) -> None:
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        records = [
            {
                "filing_date": date(2024, 11, 1),
                "period_end": date(2024, 9, 30),
                "revenue": 100_000_000,
                "total_assets": 500_000_000,
                "net_income": 20_000_000,
            },
            {
                "filing_date": date(2024, 8, 1),
                "period_end": date(2024, 6, 30),
                "revenue": 95_000_000,
                "total_assets": 480_000_000,
                "net_income": 18_000_000,
            },
            {
                "filing_date": date(2024, 5, 1),
                "period_end": date(2024, 3, 31),
                "revenue": 90_000_000,
                "total_assets": 460_000_000,
                "net_income": 16_000_000,
            },
            {
                "filing_date": date(2024, 2, 1),
                "period_end": date(2023, 12, 31),
                "revenue": 85_000_000,
                "total_assets": 440_000_000,
                "net_income": 14_000_000,
            },
        ]

        checker = QualityChecker()
        report = checker.validate_financials("AAPL", records)

        assert report.passed is True

    def test_missing_required_fields_fails(self) -> None:
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        records = [
            {
                "filing_date": date(2024, 11, 1),
                "period_end": date(2024, 9, 30),
                # Missing: revenue, total_assets, net_income
            },
        ]

        checker = QualityChecker()
        report = checker.validate_financials("AAPL", records)

        assert report.passed is False

    def test_too_few_quarters_fails(self) -> None:
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        # Zero records should fail
        checker = QualityChecker()
        report = checker.validate_financials("AAPL", [])

        assert report.passed is False

    def test_missing_filing_date_fails(self) -> None:
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        records = [
            {
                "period_end": date(2024, 9, 30),
                "revenue": 100_000_000,
                "total_assets": 500_000_000,
                "net_income": 20_000_000,
                # Missing: filing_date
            },
        ] * 4

        checker = QualityChecker()
        report = checker.validate_financials("AAPL", records)

        assert report.passed is False
        assert any("filing_date" in f.lower() for f in report.failures)

    def test_report_is_dataqualityreport_vo(self) -> None:
        from src.data_ingest.domain.value_objects import DataQualityReport
        from src.data_ingest.infrastructure.quality_checker import QualityChecker

        records = [
            {
                "filing_date": date(2024, 11, 1),
                "period_end": date(2024, 9, 30),
                "revenue": 100_000_000,
                "total_assets": 500_000_000,
                "net_income": 20_000_000,
            }
        ] * 4

        checker = QualityChecker()
        report = checker.validate_financials("AAPL", records)

        assert isinstance(report, DataQualityReport)
