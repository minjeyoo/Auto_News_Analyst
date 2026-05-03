"""CLI entry point for collecting news into the JSONL cache."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path

from dotenv import load_dotenv

try:
    from .domain_types import NewsRecord
    from .news_cache import NewsJsonlCache
    from .news_fetchers import AggregatingNewsFetcher, GoogleNewsRssFetcher, NaverNewsFetcher
except ImportError:  # Allows `python3 collect_news.py` from project root.
    from domain_types import NewsRecord
    from news_cache import NewsJsonlCache
    from news_fetchers import AggregatingNewsFetcher, GoogleNewsRssFetcher, NaverNewsFetcher


SUPPORTED_SOURCES = ("naver", "google")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect stock news into cached_news/*.jsonl")
    parser.add_argument("--tickers", nargs="+", required=True, help="Ticker or company names to search.")
    parser.add_argument("--keywords", nargs="*", default=None, help="Extra query keywords.")
    parser.add_argument("--keyword-file", default="news_keywords.json", help="JSON keyword file.")
    parser.add_argument("--keyword-group", default="global", help="Keyword group from keyword file.")
    parser.add_argument("--start", type=_parse_date, default=None, help="Start date YYYY-MM-DD.")
    parser.add_argument("--end", type=_parse_date, default=None, help="End date YYYY-MM-DD.")
    parser.add_argument("--days", type=int, default=3, help="Days to collect when --start is omitted.")
    parser.add_argument("--sources", nargs="+", choices=SUPPORTED_SOURCES, default=list(SUPPORTED_SOURCES))
    parser.add_argument("--cache-dir", default="cached_news", help="Directory for JSONL cache files.")
    return parser.parse_args(argv)


def collect_news(
    *,
    tickers: list[str],
    start: date,
    end: date,
    keywords: list[str],
    sources: list[str],
    cache_dir: Path | str = "cached_news",
) -> dict:
    fetcher = build_fetcher(sources)
    records = fetcher.fetch(tickers, start, end, keywords)
    cache = NewsJsonlCache(cache_dir)
    written = cache.write_records(records)
    cached = cache.load(start, end, tickers=tickers)
    return summarize(records=records, cached=cached, written=written, start=start, end=end, sources=sources)


def build_fetcher(sources: list[str]) -> AggregatingNewsFetcher:
    fetchers = []
    if "naver" in sources:
        fetchers.append(NaverNewsFetcher())
    if "google" in sources:
        fetchers.append(GoogleNewsRssFetcher())
    return AggregatingNewsFetcher(fetchers)


def load_keywords(path: Path | str, group: str, explicit: list[str] | None = None) -> list[str]:
    if explicit is not None:
        return explicit

    keyword_path = Path(path)
    if not keyword_path.exists():
        return []

    payload = json.loads(keyword_path.read_text(encoding="utf-8"))
    values = payload.get(group, [])
    if not isinstance(values, list):
        raise ValueError(f"keyword group must be a list: {group}")
    return [str(value) for value in values if str(value).strip()]


def resolve_window(args: argparse.Namespace, today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    end = args.end or today
    if args.start:
        start = args.start
    else:
        start = end - timedelta(days=max(0, args.days - 1))
    if start > end:
        raise ValueError("--start must be on or before --end")
    return start, end


def summarize(
    *,
    records: list[NewsRecord],
    cached: list[NewsRecord],
    written: int,
    start: date,
    end: date,
    sources: list[str],
) -> dict:
    by_source: dict[str, int] = {}
    by_ticker: dict[str, int] = {}
    for record in records:
        by_source[record.source] = by_source.get(record.source, 0) + 1
        by_ticker[record.ticker] = by_ticker.get(record.ticker, 0) + 1
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "sources": sources,
        "fetched_count": len(records),
        "written_count": written,
        "cached_count": len(cached),
        "by_source": by_source,
        "by_ticker": by_ticker,
    }


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    start, end = resolve_window(args)
    keywords = load_keywords(args.keyword_file, args.keyword_group, args.keywords)
    summary = collect_news(
        tickers=args.tickers,
        start=start,
        end=end,
        keywords=keywords,
        sources=args.sources,
        cache_dir=args.cache_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


if __name__ == "__main__":
    raise SystemExit(main())

