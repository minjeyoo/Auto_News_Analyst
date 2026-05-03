"""Finnhub company news adapter."""

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


class FinnhubNewsFetcher:
    base_url = "https://finnhub.io/api/v1/company-news"

    def __init__(self, api_key: str | None = None, session: Any | None = None, timeout: int = 15) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("FINNHUB_API_KEY", "")
        self.session = session or requests
        self.timeout = timeout

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        if not self.api_key:
            return []
        records: list[NewsRecord] = []
        for ticker in tickers:
            response = self.session.get(
                self.base_url,
                params={"symbol": ticker, "from": start.isoformat(), "to": end.isoformat(), "token": self.api_key},
                timeout=self.timeout,
            )
            response.raise_for_status()
            records.extend(_parse_items(ticker, response.json(), start, end, keywords))
        return records


def _parse_items(ticker: str, payload: list[dict], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
    records: list[NewsRecord] = []
    for item in payload:
        published_at = datetime.fromtimestamp(int(item.get("datetime", 0)))
        text = f"{item.get('headline', '')} {item.get('summary', '')}"
        if not in_date_range(published_at, start, end) or (keywords and not _matches_keywords(text, keywords)):
            continue
        records.append(
            NewsRecord(
                ticker=ticker,
                title=clean_html(str(item.get("headline", ""))),
                body=clean_html(str(item.get("summary", ""))),
                published_at=published_at,
                source="finnhub_news",
                url=canonical_url(str(item.get("url", ""))),
                metadata={"provider": "finnhub_news", "source_name": str(item.get("source", ""))},
            )
        )
    return records


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)
