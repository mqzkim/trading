"""Tests for data_ingest domain value objects and events."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.data_ingest.domain.value_objects import (
    DataQualityReport,
    FilingDate,
    FinancialStatement,
    MarketType,
    OHLCV,
    Ticker,
)
from src.data_ingest.domain.events import (
    DataIngestedEvent,
    QualityCheckFailedEvent,
)
from src.scoring.domain.value_objects import Symbol
from src.shared.domain import DomainEvent, ValueObject


# ── Ticker ──────────────────────────────────────────────────────────


class TestTicker:
    def test_valid_ticker(self) -> None:
        t = Ticker(ticker="AAPL")
        assert t.ticker == "AAPL"

    def test_valid_short_ticker(self) -> None:
        t = Ticker(ticker="A")
        assert t.ticker == "A"

    def test_valid_long_ticker(self) -> None:
        t = Ticker(ticker="ABCDEFGHIJ")  # 10 chars
        assert t.ticker == "ABCDEFGHIJ"

    def test_empty_ticker_raises(self) -> None:
        with pytest.raises(ValueError):
            Ticker(ticker="")

    def test_lowercase_ticker_raises(self) -> None:
        with pytest.raises(ValueError):
            Ticker(ticker="aapl")

    def test_special_chars_raises(self) -> None:
        with pytest.raises(ValueError):
            Ticker(ticker="AA!L")

    def test_too_long_ticker_raises(self) -> None:
        with pytest.raises(ValueError):
            Ticker(ticker="ABCDEFGHIJK")  # 11 chars

    def test_ticker_is_frozen(self) -> None:
        t = Ticker(ticker="AAPL")
        with pytest.raises(AttributeError):
            t.ticker = "MSFT"  # type: ignore[misc]

    def test_ticker_is_value_object(self) -> None:
        t = Ticker(ticker="AAPL")
        assert isinstance(t, ValueObject)

    def test_korean_6digit_ticker(self) -> None:
        t = Ticker(ticker="005930")
        assert t.ticker == "005930"

    def test_korean_short_ticker(self) -> None:
        t = Ticker(ticker="035420")
        assert t.ticker == "035420"

    def test_lowercase_non_numeric_raises(self) -> None:
        with pytest.raises(ValueError):
            Ticker(ticker="abc")


class TestMarketType:
    def test_us_value(self) -> None:
        assert MarketType.US.value == "us"

    def test_kr_value(self) -> None:
        assert MarketType.KR.value == "kr"

    def test_members(self) -> None:
        members = {m.name for m in MarketType}
        assert "US" in members
        assert "KR" in members


# ── OHLCV ───────────────────────────────────────────────────────────


class TestOHLCV:
    def test_valid_ohlcv(self) -> None:
        o = OHLCV(
            ticker="AAPL",
            date=date(2025, 1, 15),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000,
        )
        assert o.ticker == "AAPL"
        assert o.close == 153.0

    def test_high_less_than_low_raises(self) -> None:
        with pytest.raises(ValueError):
            OHLCV(
                ticker="AAPL",
                date=date(2025, 1, 15),
                open=150.0,
                high=148.0,
                low=149.0,
                close=153.0,
                volume=1000000,
            )

    def test_close_zero_raises(self) -> None:
        with pytest.raises(ValueError):
            OHLCV(
                ticker="AAPL",
                date=date(2025, 1, 15),
                open=150.0,
                high=155.0,
                low=149.0,
                close=0.0,
                volume=1000000,
            )

    def test_negative_volume_raises(self) -> None:
        with pytest.raises(ValueError):
            OHLCV(
                ticker="AAPL",
                date=date(2025, 1, 15),
                open=150.0,
                high=155.0,
                low=149.0,
                close=153.0,
                volume=-1,
            )

    def test_zero_volume_valid(self) -> None:
        o = OHLCV(
            ticker="AAPL",
            date=date(2025, 1, 15),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=0,
        )
        assert o.volume == 0

    def test_ohlcv_is_frozen(self) -> None:
        o = OHLCV(
            ticker="AAPL",
            date=date(2025, 1, 15),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000,
        )
        with pytest.raises(AttributeError):
            o.close = 200.0  # type: ignore[misc]


# ── FinancialStatement ──────────────────────────────────────────────


class TestFinancialStatement:
    def _make_valid(self, **overrides) -> FinancialStatement:
        defaults = dict(
            ticker="AAPL",
            period_end=date(2025, 9, 30),
            filing_date=date(2025, 11, 1),
            form_type="10-Q",
            revenue=100_000.0,
            net_income=25_000.0,
            total_assets=500_000.0,
            total_liabilities=200_000.0,
            working_capital=50_000.0,
            retained_earnings=150_000.0,
            ebit=35_000.0,
            operating_cashflow=40_000.0,
            free_cashflow=30_000.0,
            current_ratio=2.5,
            debt_to_equity=0.4,
            roa=0.05,
            roe=0.12,
        )
        defaults.update(overrides)
        return FinancialStatement(**defaults)

    def test_valid_financial_statement(self) -> None:
        fs = self._make_valid()
        assert fs.ticker == "AAPL"
        assert fs.period_end == date(2025, 9, 30)
        assert fs.filing_date == date(2025, 11, 1)

    def test_filing_date_before_period_end_raises(self) -> None:
        with pytest.raises(ValueError):
            self._make_valid(
                period_end=date(2025, 9, 30),
                filing_date=date(2025, 9, 15),  # before period_end
            )

    def test_filing_date_equals_period_end_valid(self) -> None:
        fs = self._make_valid(
            period_end=date(2025, 9, 30),
            filing_date=date(2025, 9, 30),
        )
        assert fs.filing_date == fs.period_end

    def test_stores_dates_as_date_objects(self) -> None:
        fs = self._make_valid()
        assert isinstance(fs.period_end, date)
        assert isinstance(fs.filing_date, date)

    def test_invalid_form_type_raises(self) -> None:
        with pytest.raises(ValueError):
            self._make_valid(form_type="8-K")

    def test_10k_form_type_valid(self) -> None:
        fs = self._make_valid(form_type="10-K")
        assert fs.form_type == "10-K"

    def test_financial_statement_is_frozen(self) -> None:
        fs = self._make_valid()
        with pytest.raises(AttributeError):
            fs.revenue = 0.0  # type: ignore[misc]


# ── FilingDate ──────────────────────────────────────────────────────


class TestFilingDate:
    def test_valid_filing_date(self) -> None:
        fd = FilingDate(value=date(2025, 1, 15))
        assert fd.value == date(2025, 1, 15)

    def test_today_valid(self) -> None:
        fd = FilingDate(value=date.today())
        assert fd.value == date.today()

    def test_tomorrow_plus_one_day_tolerance_valid(self) -> None:
        # Allow 1 day tolerance for timezone
        tomorrow = date.today() + timedelta(days=1)
        fd = FilingDate(value=tomorrow)
        assert fd.value == tomorrow

    def test_future_date_raises(self) -> None:
        future = date.today() + timedelta(days=10)
        with pytest.raises(ValueError):
            FilingDate(value=future)

    def test_filing_date_is_frozen(self) -> None:
        fd = FilingDate(value=date(2025, 1, 15))
        with pytest.raises(AttributeError):
            fd.value = date(2025, 2, 1)  # type: ignore[misc]


# ── DataQualityReport ───────────────────────────────────────────────


class TestDataQualityReport:
    def test_passed_report(self) -> None:
        r = DataQualityReport(
            ticker="AAPL",
            passed=True,
            missing_pct=0.0,
            stale_days=0,
            outlier_count=0,
            failures=(),
        )
        assert r.passed is True
        assert r.failures == ()

    def test_failed_report(self) -> None:
        r = DataQualityReport(
            ticker="AAPL",
            passed=False,
            missing_pct=10.5,
            stale_days=5,
            outlier_count=3,
            failures=("Missing 10.5% values", "Stale 5 days"),
        )
        assert r.passed is False
        assert len(r.failures) == 2

    def test_missing_pct_over_100_raises(self) -> None:
        with pytest.raises(ValueError):
            DataQualityReport(
                ticker="AAPL",
                passed=False,
                missing_pct=101.0,
                stale_days=0,
                outlier_count=0,
                failures=("too high",),
            )

    def test_negative_missing_pct_raises(self) -> None:
        with pytest.raises(ValueError):
            DataQualityReport(
                ticker="AAPL",
                passed=False,
                missing_pct=-1.0,
                stale_days=0,
                outlier_count=0,
                failures=("negative",),
            )

    def test_uses_tuple_not_list(self) -> None:
        r = DataQualityReport(
            ticker="AAPL",
            passed=True,
            missing_pct=0.0,
            stale_days=0,
            outlier_count=0,
            failures=(),
        )
        assert isinstance(r.failures, tuple)

    def test_quality_report_is_frozen(self) -> None:
        r = DataQualityReport(
            ticker="AAPL",
            passed=True,
            missing_pct=0.0,
            stale_days=0,
            outlier_count=0,
            failures=(),
        )
        with pytest.raises(AttributeError):
            r.passed = False  # type: ignore[misc]


# ── Domain Events ──────────────────────────────────────────────────


class TestDataIngestedEvent:
    def test_creates_event(self) -> None:
        e = DataIngestedEvent(ticker="AAPL", ohlcv_rows=756, financial_quarters=12)
        assert e.ticker == "AAPL"
        assert e.ohlcv_rows == 756
        assert e.financial_quarters == 12

    def test_inherits_domain_event(self) -> None:
        e = DataIngestedEvent(ticker="AAPL", ohlcv_rows=756, financial_quarters=12)
        assert isinstance(e, DomainEvent)

    def test_has_occurred_on(self) -> None:
        e = DataIngestedEvent(ticker="AAPL", ohlcv_rows=756, financial_quarters=12)
        assert e.occurred_on is not None


# ── Scoring Symbol VO (Korean ticker support) ─────────────────────


class TestScoringSymbolKorean:
    def test_us_ticker_succeeds(self) -> None:
        s = Symbol(ticker="AAPL")
        assert s.ticker == "AAPL"

    def test_korean_numeric_ticker_succeeds(self) -> None:
        s = Symbol(ticker="005930")
        assert s.ticker == "005930"

    def test_lowercase_non_numeric_raises(self) -> None:
        with pytest.raises(ValueError):
            Symbol(ticker="abc")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            Symbol(ticker="")

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError):
            Symbol(ticker="ABCDEFGHIJK")  # 11 chars


# ── Domain Events ──────────────────────────────────────────────────


class TestQualityCheckFailedEvent:
    def test_creates_event(self) -> None:
        e = QualityCheckFailedEvent(
            ticker="AAPL", failures=("Missing data", "Stale data")
        )
        assert e.ticker == "AAPL"
        assert len(e.failures) == 2

    def test_inherits_domain_event(self) -> None:
        e = QualityCheckFailedEvent(ticker="AAPL", failures=("error",))
        assert isinstance(e, DomainEvent)
