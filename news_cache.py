"""JSONL news cache for reproducible backtests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol

try:
    from .domain_types import NewsRecord
    from .news_fetchers.aggregator import dedupe_news
except ImportError:  # Allows running from project root without package install.
    from domain_types import NewsRecord
    from news_fetchers.aggregator import dedupe_news


class NewsFetcher(Protocol):
    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        """Fetch news records for the given date range."""


class NewsJsonlCache:
    """Store records as one JSONL file per publication date."""

    def __init__(self, root: Path | str = "cached_news") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write_records(self, records: list[NewsRecord], collected_at: datetime | None = None) -> int:
        collected_at = collected_at or datetime.now(UTC)
        by_day: dict[date, list[NewsRecord]] = {}
        for record in records:
            enriched = _with_cache_metadata(record, collected_at)
            by_day.setdefault(enriched.published_at.date(), []).append(enriched)

        written = 0
        for day, daily_records in by_day.items():
            existing = self.load(day, day)
            merged = dedupe_news([*existing, *daily_records])
            self._write_day(day, merged)
            written += len(daily_records)
        return written

    def load(
        self,
        start: date,
        end: date,
        *,
        tickers: list[str] | None = None,
        sources: list[str] | None = None,
    ) -> list[NewsRecord]:
        ticker_set = set(tickers or [])
        source_set = set(sources or [])
        records: list[NewsRecord] = []
        for day in _date_range(start, end):
            path = self._path_for(day)
            if not path.exists():
                continue
            with path.open(encoding="utf-8") as fp:
                for line in fp:
                    if not line.strip():
                        continue
                    record = news_record_from_dict(json.loads(line))
                    if ticker_set and record.ticker not in ticker_set:
                        continue
                    if source_set and record.source not in source_set:
                        continue
                    records.append(record)
        return dedupe_news(records)

    def _write_day(self, day: date, records: list[NewsRecord]) -> None:
        path = self._path_for(day)
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
            tmp_path = Path(tmp.name)
            for record in sorted(records, key=lambda item: (item.published_at, item.ticker, item.url)):
                tmp.write(json.dumps(news_record_to_dict(record), ensure_ascii=False, sort_keys=True) + "\n")
        tmp_path.replace(path)

    def _path_for(self, day: date) -> Path:
        return self.root / f"{day.isoformat()}.jsonl"


class CachedNewsFetcher:
    """Wrap another fetcher with cache persistence.

    `refresh=True` collects fresh data from upstream and persists it.
    `refresh=False` returns only cached data, which is the correct mode for
    reproducible backtests.
    """

    def __init__(self, upstream: NewsFetcher, cache: NewsJsonlCache, *, refresh: bool = True) -> None:
        self.upstream = upstream
        self.cache = cache
        self.refresh = refresh

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        cached = self.cache.load(start, end, tickers=tickers)
        if not self.refresh:
            return cached

        fresh = self.upstream.fetch(tickers, start, end, keywords)
        self.cache.write_records(fresh)
        return dedupe_news([*cached, *fresh])


def news_record_to_dict(record: NewsRecord) -> dict:
    return {
        "ticker": record.ticker,
        "title": record.title,
        "body": record.body,
        "published_at": record.published_at.isoformat(),
        "source": record.source,
        "url": record.url,
        "metadata": record.metadata,
    }


def news_record_from_dict(payload: dict) -> NewsRecord:
    return NewsRecord(
        ticker=payload["ticker"],
        title=payload.get("title", ""),
        body=payload.get("body", ""),
        published_at=datetime.fromisoformat(payload["published_at"]),
        source=payload.get("source", ""),
        url=payload.get("url", ""),
        metadata=dict(payload.get("metadata", {})),
    )


def _with_cache_metadata(record: NewsRecord, collected_at: datetime) -> NewsRecord:
    return NewsRecord(
        ticker=record.ticker,
        title=record.title,
        body=record.body,
        published_at=record.published_at,
        source=record.source,
        url=record.url,
        metadata={**record.metadata, "collected_at": collected_at.isoformat()},
    )


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)
