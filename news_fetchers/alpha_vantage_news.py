"""Alpha Vantage market news and sentiment adapter."""

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


class AlphaVantageNewsFetcher:
    base_url = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str | None = None, session: Any | None = None, timeout: int = 15, limit: int = 50) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.session = session or requests
        self.timeout = timeout
        self.limit = limit

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        if not self.api_key:
            return []
        records: list[NewsRecord] = []
        for ticker in tickers:
            response = self.session.get(
                self.base_url,
                params={
                    "function": "NEWS_SENTIMENT",
                    "tickers": ticker,
                    "topics": ",".join(keywords[:5]),
                    "time_from": f"{start:%Y%m%d}T0000",
                    "time_to": f"{end:%Y%m%d}T2359",
                    "sort": "RELEVANCE",
                    "limit": self.limit,
                    "apikey": self.api_key,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            records.extend(_parse_feed(ticker, response.json(), start, end))
        return records


def _parse_feed(ticker: str, payload: dict, start: date, end: date) -> list[NewsRecord]:
    records: list[NewsRecord] = []
    for item in payload.get("feed", []):
        published_at = _parse_alpha_time(str(item.get("time_published", "")))
        if published_at is None or not in_date_range(published_at, start, end):
            continue
        records.append(
            NewsRecord(
                ticker=ticker,
                title=clean_html(str(item.get("title", ""))),
                body=clean_html(str(item.get("summary", ""))),
                published_at=published_at,
                source="alpha_vantage_news",
                url=canonical_url(str(item.get("url", ""))),
                metadata={
                    "provider": "alpha_vantage_news",
                    "source_name": str(item.get("source", "")),
                    "overall_sentiment_score": str(item.get("overall_sentiment_score", "")),
                    "overall_sentiment_label": str(item.get("overall_sentiment_label", "")),
                },
            )
        )
    return records


def _parse_alpha_time(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%S")
    except ValueError:
        return None
