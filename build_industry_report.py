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


def build_industry_report(config: IndustryReportConfig) -> str:
    themes = json.loads(config.themes_path.read_text(encoding="utf-8"))
    records = NewsJsonlCache(config.cache_dir).load(config.start, config.end)
    theme_matches = match_records_to_themes(records, themes)
    markdown = render_report(config, themes, theme_matches, records)
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


def render_report(
    config: IndustryReportConfig,
    themes: dict,
    theme_matches: dict[str, list[tuple[NewsRecord, float]]],
    all_records: list[NewsRecord],
) -> str:
    lines = [
        f"# Source-Aware Global Industry Report - {config.end.isoformat()}",
        "",
        f"- Window: {config.start.isoformat()}..{config.end.isoformat()}",
        f"- Cached evidence records: {len(all_records)}",
        f"- Source coverage: {_format_counter(Counter(record.source for record in all_records))}",
        "",
        "## Theme Signals",
        "",
    ]
    for theme_name, theme in themes.items():
        evidence = theme_matches.get(theme_name, [])[: config.max_evidence_per_theme]
        source_counter = Counter(record.source for record, _ in theme_matches.get(theme_name, []))
        lines.extend(
            [
                f"### {theme_name}",
                "",
                f"- Description: {theme.get('description', '')}",
                f"- Matched evidence: {len(theme_matches.get(theme_name, []))}",
                f"- Source mix: {_format_counter(source_counter)}",
                f"- Global stocks: {', '.join(theme.get('global_stocks', [])[:12])}",
                f"- Korea stocks: {', '.join(theme.get('korea_stocks', [])[:8])}",
                "",
                "| Source | Ticker | Evidence |",
                "|---|---|---|",
            ]
        )
        if not evidence:
            lines.append("| - | - | No matched evidence in cache. |")
        for record, score in evidence:
            title = record.title.replace("|", " ").strip()
            url = record.url.strip()
            evidence_text = f"[{title}]({url})" if url else title
            lines.append(f"| {record.source} | {record.ticker} | {evidence_text} |")
        lines.append("")
    lines.extend(
        [
            "## Data Quality Notes",
            "",
            "- SEC EDGAR and DART are treated as high-weight filing evidence when present.",
            "- GDELT is included as global breadth evidence, but public API rate limits can reduce daily coverage.",
            "- Keyword derivation should be run before collection when the goal is to discover new themes rather than confirm a fixed thesis.",
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


def _format_counter(counter: Counter) -> str:
    if not counter:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counter.most_common())


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


if __name__ == "__main__":
    raise SystemExit(main())
