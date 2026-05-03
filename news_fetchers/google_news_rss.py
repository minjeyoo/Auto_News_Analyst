"""Google News RSS adapter."""

from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import requests

try:
    from ..domain_types import NewsRecord
except ImportError:  # Allows running from project root without package install.
    from domain_types import NewsRecord

from .common import canonical_url, clean_html, in_date_range, parse_feed_datetime


class GoogleNewsRssFetcher:
    base_url = "https://news.google.com/rss/search"

    def __init__(
        self,
        session: Any | None = None,
        timeout: int = 10,
        language: str = "ko",
        country: str = "KR",
    ) -> None:
        self.session = session or requests
        self.timeout = timeout
        self.language = language
        self.country = country

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        records: list[NewsRecord] = []
        for ticker in tickers:
            query = self._build_query(ticker, keywords)
            records.extend(self._fetch_query(ticker=ticker, query=query, start=start, end=end))
        return records

    def _fetch_query(self, *, ticker: str, query: str, start: date, end: date) -> list[NewsRecord]:
        response = self.session.get(self._url(query), timeout=self.timeout)
        response.raise_for_status()
        root = ET.fromstring(response.text)

        records: list[NewsRecord] = []
        for item in root.findall("./channel/item"):
            published_at = parse_feed_datetime(_text(item, "pubDate"))
            if published_at is None or not in_date_range(published_at, start, end):
                continue
            records.append(
                NewsRecord(
                    ticker=ticker,
                    title=clean_html(_text(item, "title")),
                    body=clean_html(_text(item, "description")),
                    published_at=published_at,
                    source="google_news_rss",
                    url=canonical_url(_text(item, "link")),
                    metadata={"query": query, "provider": "google_news_rss"},
                )
            )
        return records

    def _url(self, query: str) -> str:
        encoded = quote_plus(query)
        return (
            f"{self.base_url}?q={encoded}"
            f"&hl={self.language}-{self.country}&gl={self.country}&ceid={self.country}:{self.language}"
        )

    @staticmethod
    def _build_query(ticker: str, keywords: list[str]) -> str:
        terms = [ticker, *keywords]
        return " ".join(term for term in terms if term).strip()


def _text(element: ET.Element, tag: str) -> str:
    found = element.find(tag)
    return found.text if found is not None and found.text else ""

