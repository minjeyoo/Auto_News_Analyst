"""Combine multiple news sources behind the controller's NewsFetcher protocol."""

from __future__ import annotations

from datetime import date
import logging

try:
    from ..domain_types import NewsRecord
except ImportError:  # Allows running from project root without package install.
    from domain_types import NewsRecord

from .common import canonical_url


logger = logging.getLogger(__name__)


class AggregatingNewsFetcher:
    def __init__(self, fetchers: list) -> None:
        self.fetchers = fetchers

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        merged: list[NewsRecord] = []
        for fetcher in self.fetchers:
            try:
                merged.extend(fetcher.fetch(tickers, start, end, keywords))
            except Exception as exc:  # noqa: BLE001 - one flaky feed should not stop collection.
                logger.warning("%s failed: %s", fetcher.__class__.__name__, exc)
        return dedupe_news(merged)


def dedupe_news(records: list[NewsRecord]) -> list[NewsRecord]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[NewsRecord] = []
    for record in sorted(records, key=lambda item: item.published_at):
        key = (record.ticker, canonical_url(record.url), record.title.lower().strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique

