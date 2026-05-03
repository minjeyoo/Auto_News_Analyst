"""Build a source-aware industry report from cached news and filings."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re

try:
    from .domain_types import NewsRecord
    from .news_cache import NewsJsonlCache
except ImportError:  # Allows `python3 build_industry_report.py` from project root.
    from domain_types import NewsRecord
    from news_cache import NewsJsonlCache


SOURCE_WEIGHTS = {
    "sec_edgar": 1.6,
    "dart_disclosure": 1.5,
    "alpha_vantage_news": 1.3,
    "finnhub_news": 1.25,
    "newsapi_global": 1.15,
    "gdelt_doc": 1.1,
    "investing_rss": 1.05,
    "google_news_rss_global": 1.05,
    "google_news_rss": 1.0,
    "naver_news": 0.9,
}
WEAK_TERMS = {"ai", "ev", "ls", "tm", "se", "mu"}
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9.+-]{1,}|[가-힣A-Za-z0-9][가-힣A-Za-z0-9.+-]{1,}")


@dataclass(frozen=True)
class IndustryReportConfig:
    cache_dir: Path = Path("cached_news")
    themes_path: Path = Path("industry_themes.json")
    output_path: Path = Path("reports/industry_report.md")
    start: date = date.today()
    end: date = date.today()
    max_evidence_per_theme: int = 8
    report_type: str = "global_equity_theme_map"


def build_industry_report(config: IndustryReportConfig) -> str:
    themes = json.loads(config.themes_path.read_text(encoding="utf-8"))
    records = NewsJsonlCache(config.cache_dir).load(config.start, config.end)
    theme_matches = match_records_to_themes(records, themes)
    if config.report_type == "daily_local_news_report":
        markdown = render_daily_local_news_report(config, records)
    elif config.report_type == "global_equity_theme_map":
        markdown = render_global_equity_theme_map(config, themes, theme_matches, records)
    else:
        raise ValueError(f"unknown report_type: {config.report_type}")
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(markdown, encoding="utf-8")
    return markdown


def match_records_to_themes(records: list[NewsRecord], themes: dict) -> dict[str, list[tuple[NewsRecord, float]]]:
    matches: dict[str, list[tuple[NewsRecord, float]]] = defaultdict(list)
    for theme_name, theme in themes.items():
        terms = _theme_terms(theme)
        for record in records:
            score = _score_record(record, terms)
            if score < 2.0:
                continue
            matches[theme_name].append((record, score * SOURCE_WEIGHTS.get(record.source, 1.0)))
    return {
        theme_name: sorted(values, key=lambda item: (-item[1], item[0].record_key if hasattr(item[0], "record_key") else item[0].title))
        for theme_name, values in matches.items()
    }


def render_global_equity_theme_map(
    config: IndustryReportConfig,
    themes: dict,
    theme_matches: dict[str, list[tuple[NewsRecord, float]]],
    all_records: list[NewsRecord],
) -> str:
    lines = [
        f"# 글로벌 산업 흐름과 전세계 관련 주식 맵 - {config.end.isoformat()}",
        "",
        f"- 분석 기간: {config.start.isoformat()}..{config.end.isoformat()}",
        f"- 캐시에 저장된 증거 수: {len(all_records)}",
        f"- 출처별 커버리지: {_format_counter(Counter(record.source for record in all_records))}",
        "",
        "## 산업 테마별 신호",
        "",
    ]
    for theme_name, theme in themes.items():
        evidence = theme_matches.get(theme_name, [])[: config.max_evidence_per_theme]
        source_counter = Counter(record.source for record, _ in theme_matches.get(theme_name, []))
        lines.extend(
            [
                f"### {theme_name}",
                "",
                f"- 설명: {theme.get('description', '')}",
                f"- 매칭된 증거 수: {len(theme_matches.get(theme_name, []))}",
                f"- 출처 구성: {_format_counter(source_counter)}",
                f"- 글로벌 추적 종목: {', '.join(theme.get('global_stocks', [])[:12])}",
                f"- 한국 추적 종목: {', '.join(theme.get('korea_stocks', [])[:8])}",
                "",
                "| 출처 | 종목/검색어 | 증거 |",
                "|---|---|---|",
            ]
        )
        if not evidence:
            lines.append("| - | - | 캐시에서 매칭된 증거가 없습니다. |")
        for record, score in evidence:
            title = record.title.replace("|", " ").strip()
            url = record.url.strip()
            evidence_text = f"[{title}]({url})" if url else title
            lines.append(f"| {_source_label(record.source)} | {record.ticker} | {evidence_text} |")
        lines.append("")
    lines.extend(
        [
            "## 데이터 품질 메모",
            "",
            "- SEC EDGAR와 DART는 공시 증거이므로 존재할 때 높은 가중치로 반영합니다.",
            "- GDELT는 글로벌 뉴스 폭을 넓히는 용도지만, 공개 API 제한으로 일별 커버리지가 줄어들 수 있습니다.",
            "- Investing.com은 공식 RSS 피드만 사용하며, 웹페이지 스크래핑은 사용하지 않습니다.",
            "- 새로운 테마를 발견하려는 목적이라면 수집 전에 `derive_keywords.py`로 검색어를 먼저 파생해야 합니다.",
            "",
        ]
    )
    return "\n".join(lines)


def render_daily_local_news_report(config: IndustryReportConfig, records: list[NewsRecord]) -> str:
    local_records = [
        record
        for record in records
        if record.source in {"naver_news", "google_news_rss"} and _looks_local_record(record)
    ]
    by_ticker: dict[str, list[NewsRecord]] = defaultdict(list)
    for record in local_records:
        by_ticker[record.ticker].append(record)

    lines = [
        f"# 국내 뉴스 플로우 리포트 - {config.end.isoformat()}",
        "",
        f"- 분석 기간: {config.start.isoformat()}..{config.end.isoformat()}",
        f"- 국내 뉴스 증거 수: {len(local_records)}",
        f"- 출처별 커버리지: {_format_counter(Counter(record.source for record in local_records))}",
        "",
        "## 종목별 국내 뉴스 플로우",
        "",
    ]
    if not by_ticker:
        lines.append("캐시에 매칭된 국내 뉴스가 없습니다.")
        return "\n".join(lines) + "\n"

    for ticker, ticker_records in sorted(by_ticker.items(), key=lambda item: (-len(item[1]), item[0])):
        source_counter = Counter(record.source for record in ticker_records)
        lines.extend(
            [
                f"### {ticker}",
                "",
                f"- 뉴스 수: {len(ticker_records)}",
                f"- 출처 구성: {_format_counter(source_counter)}",
                "",
                "| 시간 | 출처 | 제목 |",
                "|---|---|---|",
            ]
        )
        for record in sorted(ticker_records, key=lambda item: item.published_at, reverse=True)[: config.max_evidence_per_theme]:
            title = record.title.replace("|", " ").strip()
            evidence = f"[{title}]({record.url})" if record.url else title
            lines.append(f"| {record.published_at:%Y-%m-%d %H:%M} | {_source_label(record.source)} | {evidence} |")
        lines.append("")

    lines.extend(
        [
            "## 데이터 품질 메모",
            "",
            "- 이 리포트는 국내 뉴스 플로우를 보기 위한 출력이므로 네이버 뉴스와 한국어 Google 뉴스 RSS를 우선 반영합니다.",
            "- 글로벌 산업 해석과 전세계 관련 종목은 별도 `global_equity_theme_map` 리포트에서 확인합니다.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an industry report from cached news evidence.")
    parser.add_argument("--cache-dir", type=Path, default=Path("cached_news"))
    parser.add_argument("--themes", type=Path, default=Path("industry_themes.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start", type=_parse_date, required=True)
    parser.add_argument("--end", type=_parse_date, required=True)
    parser.add_argument("--max-evidence", type=int, default=8)
    parser.add_argument(
        "--report-type",
        choices=("daily_local_news_report", "global_equity_theme_map"),
        default="global_equity_theme_map",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    markdown = build_industry_report(
        IndustryReportConfig(
            cache_dir=args.cache_dir,
            themes_path=args.themes,
            output_path=args.output,
            start=args.start,
            end=args.end,
            max_evidence_per_theme=args.max_evidence,
            report_type=args.report_type,
        )
    )
    print(markdown)
    return 0


def _theme_terms(theme: dict) -> set[str]:
    values: list[str] = []
    values.append(str(theme.get("description", "")))
    values.extend(str(item) for item in theme.get("global_queries", []))
    values.extend(str(item) for item in theme.get("global_stocks", []))
    values.extend(str(item) for item in theme.get("korea_stocks", []))
    terms: set[str] = set()
    for value in values:
        for raw in value.replace("/", " ").replace(",", " ").split():
            token = raw.strip("()[]{}:;,.+-").lower()
            if _is_theme_term(token):
                terms.add(token)
    return terms


def _score_record(record: NewsRecord, terms: set[str]) -> float:
    text = f"{record.ticker} {record.title} {record.body}".lower()
    text_tokens = set(TOKEN_RE.findall(text))
    score = 0.0
    for term in terms:
        if " " in term and term in text:
            score += 2.0
        elif term in text_tokens:
            score += 0.5 if term in WEAK_TERMS else 1.0
        elif len(term) >= 5 and term in text:
            score += 0.75
    return score


def _is_theme_term(token: str) -> bool:
    if not token:
        return False
    if token in WEAK_TERMS:
        return token in {"ai", "ev"}
    if token.isdigit():
        return False
    if len(token) < 3:
        return False
    return True


def _looks_local_record(record: NewsRecord) -> bool:
    text = f"{record.ticker} {record.title} {record.body}"
    return any("\uac00" <= char <= "\ud7a3" for char in text)


def _format_counter(counter: Counter) -> str:
    if not counter:
        return "none"
    return ", ".join(f"{_source_label(str(key))}={value}" for key, value in counter.most_common())


def _source_label(source: str) -> str:
    labels = {
        "sec_edgar": "SEC EDGAR",
        "dart_disclosure": "DART 공시",
        "alpha_vantage_news": "Alpha Vantage",
        "finnhub_news": "Finnhub",
        "newsapi_global": "NewsAPI",
        "gdelt_doc": "GDELT",
        "investing_rss": "Investing.com RSS",
        "google_news_rss_global": "Google 글로벌 뉴스 RSS",
        "google_news_rss": "Google 뉴스 RSS",
        "naver_news": "네이버 뉴스",
    }
    return labels.get(source, source)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


if __name__ == "__main__":
    raise SystemExit(main())
