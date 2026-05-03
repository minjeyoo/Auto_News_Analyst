"""GDELT DOC 2.0 global news adapter."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import requests

try:
    from ..domain_types import NewsRecord
except ImportError:  # Allows running from project root without package install.
    from domain_types import NewsRecord

from .common import canonical_url, clean_html, in_date_range


class GdeltNewsFetcher:
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(self, session: Any | None = None, timeout: int = 15, max_records: int = 25) -> None:
        self.session = session or requests
        self.timeout = timeout
        self.max_records = max_records

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        records: list[NewsRecord] = []
        for ticker in tickers:
            query = self._build_query(ticker, keywords)
            records.extend(self._fetch_query(ticker=ticker, query=query, start=start, end=end))
        return records

    def _fetch_query(self, *, ticker: str, query: str, start: date, end: date) -> list[NewsRecord]:
        response = self.session.get(
            self.base_url,
            params={
                "query": query,
                "mode": "ArtList",
                "format": "json",
                "sort": "HybridRel",
                "maxrecords": self.max_records,
                "startdatetime": f"{start:%Y%m%d}000000",
                "enddatetime": f"{end:%Y%m%d}235959",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()

        records: list[NewsRecord] = []
        for article in payload.get("articles", []):
            published_at = _parse_gdelt_datetime(str(article.get("seendate", "")))
            if published_at is None or not in_date_range(published_at, start, end):
                continue
            records.append(
                NewsRecord(
                    ticker=ticker,
                    title=clean_html(str(article.get("title", ""))),
                    body=clean_html(str(article.get("snippet", ""))),
                    published_at=published_at,
                    source="gdelt_doc",
                    url=canonical_url(str(article.get("url", ""))),
                    metadata={
                        "query": query,
                        "provider": "gdelt_doc",
                        "domain": str(article.get("domain", "")),
                        "language": str(article.get("language", "")),
                        "country": str(article.get("sourceCountry", "")),
                    },
                )
            )
        return records

    @staticmethod
    def _build_query(ticker: str, keywords: list[str]) -> str:
        terms = [ticker, *keywords]
        return " ".join(term for term in terms if term).strip()


def _parse_gdelt_datetime(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y%m%d%H%M%S", "%Y%m%dT%H%M%SZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None
