"""Tests for EdgartoolsClient — SEC financial data with filing_date tracking."""
from __future__ import annotations

import asyncio
from datetime import date
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _set_edgar_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set EDGAR_IDENTITY env var for all tests in this module."""
    monkeypatch.setenv("EDGAR_IDENTITY", "TestBot test@example.com")
    # Prevent set_identity from closing real HTTP clients during tests
    monkeypatch.setattr(
        "src.data_ingest.infrastructure.edgartools_client.set_identity", lambda _: None
    )


def _make_mock_filing(
    filing_date: date,
    period_of_report: date,
    *,
    has_financials: bool = True,
) -> MagicMock:
    """Create a mock edgartools Filing object."""
    filing = MagicMock()
    filing.filing_date = filing_date
    filing.period_of_report = period_of_report

    if has_financials:
        tenq = MagicMock()
        income = MagicMock()
        balance = MagicMock()
        cashflow = MagicMock()

        # Income statement
        income.get_value.side_effect = lambda key, default=0.0: {
            "Revenues": 100_000_000.0,
            "NetIncomeLoss": 20_000_000.0,
            "OperatingIncomeLoss": 30_000_000.0,
        }.get(key, default)

        # Balance sheet
        balance.get_value.side_effect = lambda key, default=0.0: {
            "Assets": 500_000_000.0,
            "Liabilities": 200_000_000.0,
            "RetainedEarningsAccumulatedDeficit": 150_000_000.0,
        }.get(key, default)

        # Cash flow
        cashflow.get_value.side_effect = lambda key, default=0.0: {
            "NetCashProvidedByUsedInOperatingActivities": 40_000_000.0,
        }.get(key, default)

        tenq.financials = MagicMock()
        tenq.financials.income_statement = income
        tenq.financials.balance_sheet = balance
        tenq.financials.cash_flow_statement = cashflow

        filing.obj.return_value = tenq
    else:
        filing.obj.return_value = None

    return filing


class TestEdgartoolsClientInit:
    """Test EdgartoolsClient initialization."""

    def test_creates_without_semaphore(self) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        client = EdgartoolsClient()
        assert client._semaphore is None

    def test_accepts_semaphore(self) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        sem = asyncio.Semaphore(5)
        client = EdgartoolsClient(semaphore=sem)
        assert client._semaphore is sem


class TestEdgartoolsClientFetchFinancials:
    """Test async SEC financial data fetching."""

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_fetch_financials_returns_list_of_dicts(
        self, mock_company_cls: MagicMock
    ) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = [
            _make_mock_filing(date(2024, 11, 1), date(2024, 9, 30)),
        ]
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        result = await client.fetch_financials("AAPL", quarters=1)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert "filing_date" in result[0]
        assert "period_end" in result[0]

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_filing_date_is_extracted_correctly(
        self, mock_company_cls: MagicMock
    ) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        expected_filing_date = date(2024, 11, 1)
        expected_period_end = date(2024, 9, 30)

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = [
            _make_mock_filing(expected_filing_date, expected_period_end),
        ]
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        result = await client.fetch_financials("AAPL", quarters=1)

        assert result[0]["filing_date"] == expected_filing_date
        assert result[0]["period_end"] == expected_period_end

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_handles_missing_xbrl_gracefully(
        self, mock_company_cls: MagicMock
    ) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = [
            _make_mock_filing(date(2024, 11, 1), date(2024, 9, 30), has_financials=False),
        ]
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        result = await client.fetch_financials("AAPL", quarters=1)

        # Missing XBRL should be skipped, not raise an error
        assert isinstance(result, list)
        assert len(result) == 0  # Filing without financials is skipped

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_extracts_financial_metrics(
        self, mock_company_cls: MagicMock
    ) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = [
            _make_mock_filing(date(2024, 11, 1), date(2024, 9, 30)),
        ]
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        result = await client.fetch_financials("AAPL", quarters=1)

        record = result[0]
        assert "revenue" in record
        assert "net_income" in record
        assert "total_assets" in record
        assert "total_liabilities" in record
        assert "operating_cashflow" in record

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_fetch_with_semaphore(self, mock_company_cls: MagicMock) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = [
            _make_mock_filing(date(2024, 11, 1), date(2024, 9, 30)),
        ]
        mock_company.get_filings.return_value = mock_filings

        sem = asyncio.Semaphore(2)
        client = EdgartoolsClient(semaphore=sem)
        result = await client.fetch_financials("AAPL", quarters=1)

        assert len(result) >= 1

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_multiple_filings_processed(
        self, mock_company_cls: MagicMock
    ) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = [
            _make_mock_filing(date(2024, 11, 1), date(2024, 9, 30)),
            _make_mock_filing(date(2024, 8, 1), date(2024, 6, 30)),
            _make_mock_filing(date(2024, 5, 1), date(2024, 3, 31)),
        ]
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        result = await client.fetch_financials("AAPL", quarters=3)

        assert len(result) == 3

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_form_type_is_included(self, mock_company_cls: MagicMock) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = [
            _make_mock_filing(date(2024, 11, 1), date(2024, 9, 30)),
        ]
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        result = await client.fetch_financials("AAPL", quarters=1)

        assert "form_type" in result[0]

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_handles_company_not_found(self, mock_company_cls: MagicMock) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company_cls.side_effect = Exception("Company not found")

        client = EdgartoolsClient()
        result = await client.fetch_financials("INVALID", quarters=1)

        assert result == []

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_default_quarters_is_12(self, mock_company_cls: MagicMock) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = []
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        await client.fetch_financials("AAPL")

        mock_filings.head.assert_called_with(12)


class TestEdgartoolsTickerFieldFix:
    """Test that _extract_filing returns the actual ticker, not filing_date."""

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_ticker_field_contains_actual_ticker(
        self, mock_company_cls: MagicMock
    ) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = [
            _make_mock_filing(date(2024, 11, 1), date(2024, 9, 30)),
        ]
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        result = await client.fetch_financials("AAPL", quarters=1)

        assert result[0]["ticker"] == "AAPL"

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_ticker_field_is_not_filing_date(
        self, mock_company_cls: MagicMock
    ) -> None:
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company = mock_company_cls.return_value
        filing_date = date(2024, 11, 1)
        mock_filings = MagicMock()
        mock_filings.head.return_value = [
            _make_mock_filing(filing_date, date(2024, 9, 30)),
        ]
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        result = await client.fetch_financials("MSFT", quarters=1)

        # Must NOT be the string representation of filing_date
        assert result[0]["ticker"] != str(filing_date)
        assert result[0]["ticker"] == "MSFT"


class TestEdgartoolsSmallCapXBRL:
    """Test edgartools handles small-cap tickers with sparse/missing XBRL."""

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_missing_cashflow_statement_returns_zero_cashflow(
        self, mock_company_cls: MagicMock
    ) -> None:
        """Small-cap filing with income_statement but no cash_flow_statement."""
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        filing = MagicMock()
        filing.filing_date = date(2024, 11, 1)
        filing.period_of_report = date(2024, 9, 30)

        tenq = MagicMock()
        income = MagicMock()
        income.get_value.side_effect = lambda key, default=0.0: {
            "Revenues": 5_000_000.0,
            "NetIncomeLoss": 500_000.0,
            "OperatingIncomeLoss": 800_000.0,
        }.get(key, default)

        balance = MagicMock()
        balance.get_value.side_effect = lambda key, default=0.0: {
            "Assets": 10_000_000.0,
            "Liabilities": 4_000_000.0,
            "RetainedEarningsAccumulatedDeficit": 3_000_000.0,
        }.get(key, default)

        tenq.financials = MagicMock()
        tenq.financials.income_statement = income
        tenq.financials.balance_sheet = balance
        tenq.financials.cash_flow_statement = None  # Missing for small-cap
        filing.obj.return_value = tenq

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = [filing]
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        result = await client.fetch_financials("SMCP", quarters=1)

        assert len(result) == 1
        assert result[0]["operating_cashflow"] == 0.0
        assert result[0]["ticker"] == "SMCP"

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_sparse_xbrl_returns_zero_defaults(
        self, mock_company_cls: MagicMock
    ) -> None:
        """Filing with all statements but get_value returns defaults for most fields."""
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        filing = MagicMock()
        filing.filing_date = date(2024, 11, 1)
        filing.period_of_report = date(2024, 9, 30)

        tenq = MagicMock()
        # All statements exist but return default 0.0 for everything
        for attr_name in ("income_statement", "balance_sheet", "cash_flow_statement"):
            stmt = MagicMock()
            stmt.get_value.side_effect = lambda key, default=0.0: default
            setattr(tenq.financials, attr_name, stmt)

        filing.obj.return_value = tenq

        mock_company = mock_company_cls.return_value
        mock_filings = MagicMock()
        mock_filings.head.return_value = [filing]
        mock_company.get_filings.return_value = mock_filings

        client = EdgartoolsClient()
        result = await client.fetch_financials("TINY", quarters=1)

        assert len(result) == 1
        assert result[0]["revenue"] == 0.0
        assert result[0]["net_income"] == 0.0
        assert result[0]["operating_cashflow"] == 0.0

    @patch("src.data_ingest.infrastructure.edgartools_client.Company")
    async def test_company_not_found_returns_empty_list(
        self, mock_company_cls: MagicMock
    ) -> None:
        """Unknown small-cap ticker where Company() raises."""
        from src.data_ingest.infrastructure.edgartools_client import EdgartoolsClient

        mock_company_cls.side_effect = Exception("No SEC filings found")

        client = EdgartoolsClient()
        result = await client.fetch_financials("ZZZZZ", quarters=1)

        assert result == []
