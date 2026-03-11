"""Tests for EdgartoolsClient — SEC financial data with filing_date tracking."""
from __future__ import annotations

import asyncio
from datetime import date
from unittest.mock import MagicMock, patch

import pytest


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
