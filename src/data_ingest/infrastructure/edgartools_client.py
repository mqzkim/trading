"""EdgartoolsClient — SEC financial data with filing_date tracking.

Fetches 10-Q/10-K filings via edgartools, extracting financial metrics
with filing_date as the primary temporal key (for point-in-time correctness).
Runs sync edgartools calls in executor for async compatibility.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from edgar import Company

logger = logging.getLogger(__name__)

# SEC EDGAR rate limit: 10 req/sec. Conservative delay between filings.
_SEC_DELAY = 0.2


class EdgartoolsClient:
    """SEC financial data client using edgartools.

    Extracts filing_date (SEC submission date) as the temporal key
    instead of period_of_report (fiscal quarter end) to prevent
    look-ahead bias in downstream queries.
    """

    def __init__(self, semaphore: asyncio.Semaphore | None = None) -> None:
        self._semaphore = semaphore

    async def fetch_financials(
        self, ticker: str, quarters: int = 12
    ) -> list[dict[str, Any]]:
        """Fetch quarterly financial statements from SEC EDGAR.

        Args:
            ticker: Stock symbol (e.g., "AAPL").
            quarters: Number of quarters to fetch (default 12 = ~3 years).

        Returns:
            List of dicts, each containing financial metrics with
            filing_date and period_end dates. Empty list if company
            not found or all filings lack XBRL data.
        """
        loop = asyncio.get_running_loop()

        if self._semaphore is not None:
            async with self._semaphore:
                return await loop.run_in_executor(
                    None, self._fetch_sync, ticker, quarters
                )

        return await loop.run_in_executor(None, self._fetch_sync, ticker, quarters)

    def _fetch_sync(self, ticker: str, quarters: int) -> list[dict[str, Any]]:
        """Synchronous fetch logic run inside executor."""
        try:
            company = Company(ticker)
        except Exception:
            logger.warning("Company not found for ticker %s", ticker)
            return []

        results: list[dict[str, Any]] = []

        # Fetch 10-Q filings
        try:
            filings_10q = company.get_filings(form="10-Q").head(quarters)
            for filing in filings_10q:
                record = self._extract_filing(filing, form_type="10-Q")
                if record is not None:
                    results.append(record)
                time.sleep(_SEC_DELAY)
        except Exception:
            logger.warning("Failed to fetch 10-Q filings for %s", ticker, exc_info=True)

        return results

    def _extract_filing(
        self, filing: Any, form_type: str
    ) -> dict[str, Any] | None:
        """Extract financial metrics from a single filing.

        Returns None if XBRL financials cannot be parsed.
        """
        filing_date = filing.filing_date
        period_end = filing.period_of_report

        try:
            tenq = filing.obj()
        except Exception:
            logger.warning(
                "Failed to parse filing object for %s (%s)",
                filing_date,
                form_type,
            )
            return None

        if tenq is None or not hasattr(tenq, "financials") or tenq.financials is None:
            logger.warning(
                "No XBRL financials for filing %s (%s)", filing_date, form_type
            )
            return None

        financials = tenq.financials
        income = getattr(financials, "income_statement", None)
        balance = getattr(financials, "balance_sheet", None)
        cashflow = getattr(financials, "cash_flow_statement", None)

        def _get(statement: Any, key: str, default: float = 0.0) -> float:
            if statement is None:
                return default
            try:
                val = statement.get_value(key, default)
                return float(val) if val is not None else default
            except Exception:
                return default

        revenue = _get(income, "Revenues")
        net_income = _get(income, "NetIncomeLoss")
        ebit = _get(income, "OperatingIncomeLoss")

        total_assets = _get(balance, "Assets")
        total_liabilities = _get(balance, "Liabilities")
        retained_earnings = _get(balance, "RetainedEarningsAccumulatedDeficit")

        operating_cashflow = _get(
            cashflow, "NetCashProvidedByUsedInOperatingActivities"
        )

        # Derived metrics (safe division)
        working_capital = total_assets - total_liabilities
        free_cashflow = operating_cashflow  # Simplified; capex not always available

        current_ratio = 0.0
        if total_liabilities > 0:
            current_ratio = total_assets / total_liabilities

        debt_to_equity = 0.0
        equity = total_assets - total_liabilities
        if equity > 0:
            debt_to_equity = total_liabilities / equity

        roa = 0.0
        if total_assets > 0:
            roa = net_income / total_assets

        roe = 0.0
        if equity > 0:
            roe = net_income / equity

        return {
            "ticker": str(filing_date),  # Will be overridden by caller context
            "filing_date": filing_date,
            "period_end": period_end,
            "form_type": form_type,
            "revenue": revenue,
            "net_income": net_income,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "working_capital": working_capital,
            "retained_earnings": retained_earnings,
            "ebit": ebit,
            "operating_cashflow": operating_cashflow,
            "free_cashflow": free_cashflow,
            "current_ratio": current_ratio,
            "debt_to_equity": debt_to_equity,
            "roa": roa,
            "roe": roe,
        }
