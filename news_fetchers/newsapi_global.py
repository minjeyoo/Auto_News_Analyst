"""NewsAPI.org global article adapter."""

from __future__ import annotations

from datetime import date, datetime
import os
from typing import Any

import requests

try:
    from ..domain_types import NewsRecord
except ImportError:  # Allows running from project root without package install.
    from domain_types import NewsRecord

from .common import canonical_url, clean_html, in_date_range


class NewsApiGlobalFetcher:
    base_url = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: str | None = None, session: Any | None = None, timeout: int = 15, page_size: int = 50) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("NEWSAPI_API_KEY", "")
        self.session = session or requests
        self.timeout = timeout
        self.page_size = page_size

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        if not self.api_key:
            return []
        records: list[NewsRecord] = []
        for ticker in tickers:
            query = " ".join([ticker, *keywords]).strip()
            response = self.session.get(
                self.base_url,
                params={
                    "q": query,
                    "from": start.isoformat(),
                    "to": end.isoformat(),
                    "language": "en",
                    "sortBy": "relevancy",
                    "pageSize": self.page_size,
                    "apiKey": self.api_key,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            records.extend(_parse_articles(ticker, response.json(), start, end, query))
        return records


def _parse_articles(ticker: str, payload: dict, start: date, end: date, query: str) -> list[NewsRecord]:
    records: list[NewsRecord] = []
    for item in payload.get("articles", []):
        published_at = _parse_newsapi_time(str(item.get("publishedAt", "")))
        if published_at is None or not in_date_range(published_at, start, end):
            continue
        source = item.get("source") or {}
        records.append(
            NewsRecord(
                ticker=ticker,
                title=clean_html(str(item.get("title", ""))),
                body=clean_html(str(item.get("description", "") or item.get("content", ""))),
                published_at=published_at,
                source="newsapi_global",
                url=canonical_url(str(item.get("url", ""))),
                metadata={
                    "provider": "newsapi_global",
                    "source_name": str(source.get("name", "")),
                    "query": query,
                },
            )
        )
    return records


def _parse_newsapi_time(value: str) -> datetime | None:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed
