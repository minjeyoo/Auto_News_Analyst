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
    from .news_fetchers import (
        AggregatingNewsFetcher,
        AlphaVantageNewsFetcher,
        DartDisclosureFetcher,
        FinnhubNewsFetcher,
        GdeltNewsFetcher,
        GoogleNewsRssFetcher,
        InvestingRssFetcher,
        NaverNewsFetcher,
        NewsApiGlobalFetcher,
        SecEdgarFetcher,
    )
except ImportError:  # Allows `python3 collect_news.py` from project root.
    from domain_types import NewsRecord
    from news_cache import NewsJsonlCache
    from news_fetchers import (
        AggregatingNewsFetcher,
        AlphaVantageNewsFetcher,
        DartDisclosureFetcher,
        FinnhubNewsFetcher,
        GdeltNewsFetcher,
        GoogleNewsRssFetcher,
        InvestingRssFetcher,
        NaverNewsFetcher,
        NewsApiGlobalFetcher,
        SecEdgarFetcher,
    )


SUPPORTED_SOURCES = (
    "naver",
    "google",
    "google_global",
    "investing",
    "gdelt",
    "sec",
    "alpha_vantage",
    "finnhub",
    "newsapi",
    "dart",
)
DEFAULT_SOURCES = ("naver", "google")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect stock news into cached_news/*.jsonl")
    parser.add_argument("--tickers", nargs="+", required=True, help="Ticker or company names to search.")
    parser.add_argument("--keywords", nargs="*", default=None, help="Extra query keywords.")
    parser.add_argument("--keyword-file", default="news_keywords.json", help="JSON keyword file.")
    parser.add_argument("--keyword-group", default="global", help="Keyword group from keyword file.")
    parser.add_argument("--theme-file", default="industry_themes.json", help="Industry theme universe JSON file.")
    parser.add_argument("--company-alias-file", default="company_aliases.json", help="Company alias universe JSON file.")
    parser.add_argument("--include-global-queries", action="store_true", help="Add English global queries from industry themes.")
    parser.add_argument("--include-company-aliases", action="store_true", help="Add company aliases and business keywords.")
    parser.add_argument("--start", type=_parse_date, default=None, help="Start date YYYY-MM-DD.")
    parser.add_argument("--end", type=_parse_date, default=None, help="End date YYYY-MM-DD.")
    parser.add_argument("--days", type=int, default=3, help="Days to collect when --start is omitted.")
    parser.add_argument("--sources", nargs="+", choices=SUPPORTED_SOURCES, default=list(DEFAULT_SOURCES))
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
    if "google_global" in sources:
        fetchers.append(GoogleNewsRssFetcher(language="en", country="US", source_name="google_news_rss_global"))
    if "investing" in sources:
        fetchers.append(InvestingRssFetcher())
    if "gdelt" in sources:
        fetchers.append(GdeltNewsFetcher())
    if "sec" in sources:
        fetchers.append(SecEdgarFetcher())
    if "alpha_vantage" in sources:
        fetchers.append(AlphaVantageNewsFetcher())
    if "finnhub" in sources:
        fetchers.append(FinnhubNewsFetcher())
    if "newsapi" in sources:
        fetchers.append(NewsApiGlobalFetcher())
    if "dart" in sources:
        fetchers.append(DartDisclosureFetcher())
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


def load_global_queries(path: Path | str) -> list[str]:
    theme_path = Path(path)
    if not theme_path.exists():
        return []
    payload = json.loads(theme_path.read_text(encoding="utf-8"))
    queries: list[str] = []
    for theme in payload.values():
        if isinstance(theme, dict):
            queries.extend(str(value) for value in theme.get("global_queries", []) if str(value).strip())
    return _dedupe(queries)


def load_company_terms(path: Path | str, tickers: list[str]) -> list[str]:
    alias_path = Path(path)
    if not alias_path.exists():
        return []
    payload = json.loads(alias_path.read_text(encoding="utf-8"))
    requested = {ticker.lower() for ticker in tickers}
    terms: list[str] = []
    for name, company in payload.items():
        if not isinstance(company, dict):
            continue
        tickers_for_company = [str(value) for value in company.get("tickers", [])]
        names_for_company = [str(name), *[str(value) for value in company.get("korean_names", [])], *[str(value) for value in company.get("english_names", [])]]
        company_terms = [
            *tickers_for_company,
            *names_for_company,
            *[str(value) for value in company.get("aliases", [])],
            *[str(value) for value in company.get("business_keywords", [])],
        ]
        lower_terms = {term.lower() for term in company_terms}
        if requested.isdisjoint(lower_terms):
            continue
        terms.extend(term for term in company_terms if term.strip())
    return _dedupe(terms)


def build_collection_keywords(
    *,
    base_keywords: list[str],
    tickers: list[str],
    include_global_queries: bool,
    include_company_aliases: bool,
    theme_file: Path | str,
    company_alias_file: Path | str,
) -> list[str]:
    keywords = list(base_keywords)
    if include_global_queries:
        keywords.extend(load_global_queries(theme_file))
    if include_company_aliases:
        keywords.extend(load_company_terms(company_alias_file, tickers))
    return _dedupe(keywords)


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
    base_keywords = load_keywords(args.keyword_file, args.keyword_group, args.keywords)
    keywords = build_collection_keywords(
        base_keywords=base_keywords,
        tickers=args.tickers,
        include_global_queries=args.include_global_queries,
        include_company_aliases=args.include_company_aliases,
        theme_file=args.theme_file,
        company_alias_file=args.company_alias_file,
    )
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


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        normalized = str(value).strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
    return unique


if __name__ == "__main__":
    raise SystemExit(main())
