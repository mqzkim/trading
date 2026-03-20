"""YFinanceNewsProvider — yfinance news fetching with 1-hour TTL cache.

Implements the NewsProvider Protocol via duck typing (structural subtyping —
no Protocol inheritance required).

Concrete impl of: src.scoring.domain.services.NewsProvider
Test double:      InMemoryNewsProvider (tests/scoring/)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from src.shared.domain import Ok, Err, Result
from src.scoring.domain.value_objects import NewsItem


_TTL_SECONDS: int = 3600  # 1 hour


class YFinanceNewsProvider:
    """YFinance 뉴스 제공자 — yfinance API를 통해 뉴스 헤드라인 조회.

    구체 구현: NewsProvider Protocol (duck typing — Protocol 상속 불필요).
    캐시 전략: dict + timestamp, TTL = 1시간.

    캐시 만료 또는 미존재 시 yfinance에서 새로 조회하고 결과를 저장.
    네트워크/파싱 오류는 Err(str)로 래핑하여 반환.
    """

    def __init__(self) -> None:
        # _cache: symbol -> (items, fetched_at)
        self._cache: dict[str, tuple[list[NewsItem], datetime]] = {}

    def fetch(self, symbol: str) -> Result[list[NewsItem], str]:
        """심볼에 대한 뉴스 헤드라인 조회.

        캐시 유효 시: 캐시된 목록 반환 (Ok).
        캐시 만료/없음: yfinance에서 새로 조회 후 캐시 갱신.

        Args:
            symbol: 종목 코드 (예: "AAPL")

        Returns:
            Ok(list[NewsItem]) — 뉴스 목록 (빈 목록도 Ok로 반환)
            Err(str) — 네트워크 오류, 파싱 실패 등 조회 불가 사유
        """
        now = datetime.utcnow()

        # Check cache validity
        cached = self._cache.get(symbol)
        if cached is not None:
            items, fetched_at = cached
            elapsed = (now - fetched_at).total_seconds()
            if elapsed < _TTL_SECONDS:
                return Ok(items)

        # Fetch from yfinance
        try:
            import yfinance as yf  # type: ignore[import-untyped]
            ticker = yf.Ticker(symbol)
            raw_news: list[dict[str, Any]] = ticker.news or []
        except Exception as exc:  # noqa: BLE001
            return Err(f"yfinance fetch failed for {symbol!r}: {exc}")  # type: ignore[arg-type]

        # Parse news items, skip unparseable entries
        items: list[NewsItem] = []
        for article in raw_news:
            try:
                headline = (
                    article.get("title")
                    or article.get("headline")
                    or ""
                )
                if not headline:
                    continue

                # Resolve publication datetime from various yfinance field formats
                pub_ts = (
                    article.get("providerPublishTime")
                    or article.get("pubDate")
                )
                if isinstance(pub_ts, (int, float)):
                    published_at = datetime.utcfromtimestamp(pub_ts)
                elif isinstance(pub_ts, str):
                    published_at = datetime.fromisoformat(pub_ts)
                else:
                    published_at = now

                items.append(NewsItem(headline=str(headline), published_at=published_at))
            except Exception:  # noqa: BLE001
                # Skip malformed articles silently — partial data is better than none
                continue

        # Store in cache with current timestamp
        self._cache[symbol] = (items, now)
        return Ok(items)
