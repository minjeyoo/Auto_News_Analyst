"""Investing.com RSS adapter."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
import xml.etree.ElementTree as ET

import requests

try:
    from ..domain_types import NewsRecord
except ImportError:  # Allows running from project root without package install.
    from domain_types import NewsRecord

from .common import canonical_url, clean_html, in_date_range, parse_feed_datetime


class InvestingRssFetcher:
    """Read officially published Investing.com RSS feeds.

    This avoids brittle webpage scraping and only consumes the publisher's RSS
    syndication endpoints.
    """

    default_feeds = (
        "https://www.investing.com/rss/news.rss",
        "https://www.investing.com/rss/news_25.rss",
        "https://www.investing.com/rss/news_14.rss",
    )

    def __init__(
        self,
        session: Any | None = None,
        timeout: int = 15,
        feeds: tuple[str, ...] | None = None,
    ) -> None:
        self.session = session or requests
        self.timeout = timeout
        self.feeds = feeds or self.default_feeds

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        records: list[NewsRecord] = []
        for feed_url in self.feeds:
            records.extend(self._fetch_feed(feed_url=feed_url, tickers=tickers, start=start, end=end, keywords=keywords))
        return records

    def _fetch_feed(
        self,
        *,
        feed_url: str,
        tickers: list[str],
        start: date,
        end: date,
        keywords: list[str],
    ) -> list[NewsRecord]:
        response = self.session.get(feed_url, timeout=self.timeout)
        response.raise_for_status()
        root = ET.fromstring(response.text)

        records: list[NewsRecord] = []
        for item in root.findall("./channel/item"):
            published_at = _parse_investing_datetime(_text(item, "pubDate"))
            if published_at is None or not in_date_range(published_at, start, end):
                continue
            title = clean_html(_text(item, "title"))
            body = clean_html(_text(item, "description"))
            matched_ticker = _match_ticker(f"{title} {body}", tickers)
            if not matched_ticker:
                continue
            if keywords and not _matches_keywords(f"{title} {body}", keywords):
                continue
            records.append(
                NewsRecord(
                    ticker=matched_ticker,
                    title=title,
                    body=body,
                    published_at=published_at,
                    source="investing_rss",
                    url=canonical_url(_text(item, "link")),
                    metadata={"provider": "investing_rss", "feed_url": feed_url},
                )
            )
        return records


def _text(element: ET.Element, tag: str) -> str:
    found = element.find(tag)
    return found.text if found is not None and found.text else ""


def _match_ticker(text: str, tickers: list[str]) -> str:
    lowered = text.lower()
    for ticker in tickers:
        if ticker.lower() in lowered:
            return ticker
    return ""


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _parse_investing_datetime(value: str) -> datetime | None:
    parsed = parse_feed_datetime(value)
    if parsed is not None:
        return parsed
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
