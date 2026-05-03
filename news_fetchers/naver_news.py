"""Naver Developers News Search API adapter."""

from __future__ import annotations

from datetime import date
import os
from typing import Any

from dotenv import load_dotenv
import requests

try:
    from ..domain_types import NewsRecord
except ImportError:  # Allows running from project root without package install.
    from domain_types import NewsRecord

from .common import canonical_url, clean_html, in_date_range, parse_feed_datetime


class NaverNewsFetcher:
    endpoint = "https://openapi.naver.com/v1/search/news.json"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        session: Any | None = None,
        timeout: int = 10,
    ) -> None:
        load_dotenv()
        self.client_id = client_id or os.environ.get("NAVER_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("NAVER_CLIENT_SECRET", "")
        self.session = session or requests
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        if not self.is_configured:
            return []

        records: list[NewsRecord] = []
        for ticker in tickers:
            query = self._build_query(ticker, keywords)
            records.extend(self._fetch_query(ticker=ticker, query=query, start=start, end=end))
        return records

    def _fetch_query(self, *, ticker: str, query: str, start: date, end: date) -> list[NewsRecord]:
        response = self.session.get(
            self.endpoint,
            params={"query": query, "display": 100, "start": 1, "sort": "date"},
            headers={
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        records: list[NewsRecord] = []
        for item in response.json().get("items", []):
            published_at = parse_feed_datetime(item.get("pubDate", ""))
            if published_at is None or not in_date_range(published_at, start, end):
                continue

            title = clean_html(item.get("title", ""))
            description = clean_html(item.get("description", ""))
            url = canonical_url(item.get("originallink") or item.get("link", ""))
            records.append(
                NewsRecord(
                    ticker=ticker,
                    title=title,
                    body=description,
                    published_at=published_at,
                    source="naver_news",
                    url=url,
                    metadata={"query": query, "provider": "naver"},
                )
            )
        return records

    @staticmethod
    def _build_query(ticker: str, keywords: list[str]) -> str:
        terms = [ticker, *keywords]
        return " ".join(term for term in terms if term).strip()

