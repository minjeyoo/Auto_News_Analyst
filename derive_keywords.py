"""Derive next-run search keywords from reports and cached news."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
import json
from pathlib import Path
import re

try:
    from .news_cache import NewsJsonlCache
except ImportError:  # Allows `python3 derive_keywords.py` from project root.
    from news_cache import NewsJsonlCache


DEFAULT_STOPWORDS = {
    "and",
    "for",
    "the",
    "with",
    "from",
    "that",
    "this",
    "into",
    "about",
    "after",
    "before",
    "today",
    "market",
    "stock",
    "stocks",
    "company",
    "report",
    "reports",
    "news",
    "said",
    "says",
    "will",
    "are",
    "was",
    "were",
    "기자",
    "뉴스",
    "관련",
    "전망",
    "오늘",
    "이번",
    "대한",
    "통해",
    "기반",
    "시장",
    "종목",
    "기업",
    "산업",
    "글로벌",
    "HTTPS",
    "HTTP",
    "악마는",
    "프라다를",
    "입는다",
    "영화",
    "비스포크",
    "콤보",
    "세탁건조기",
    "국내",
    "올해",
    "있다",
    "시총",
    "클럽",
    "돌파",
    "400곳",
    "1조",
    "us",
    "dx",
    "ds",
    "sk",
    "ls",
    "사상",
    "노조",
    "탈퇴",
    "daily",
    "최대",
    "증시",
    "삼성전자는",
}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9.+-]{2,}|[가-힣A-Za-z0-9][가-힣A-Za-z0-9.+-]{1,}")
URL_RE = re.compile(r"https?://\S+|www\.\S+")


@dataclass(frozen=True)
class KeywordDerivationConfig:
    cache_dir: Path = Path("cached_news")
    reports_dir: Path = Path("reports")
    output_path: Path = Path("derived_keywords.json")
    start: date | None = None
    end: date | None = None
    top_n: int = 30
    min_count: int = 2


def derive_keywords(config: KeywordDerivationConfig) -> dict[str, list[str]]:
    start, end = _resolve_window(config.start, config.end)
    report_texts = _load_report_texts(config.reports_dir)
    news_texts = _load_news_texts(config.cache_dir, start, end)
    keywords = rank_keywords(
        [*report_texts, *news_texts],
        anchor_texts=report_texts,
        top_n=config.top_n,
        min_count=config.min_count,
    )
    payload = {
        "global": keywords,
        "derived": keywords,
        "metadata": [
            f"source_window={start.isoformat()}..{end.isoformat()}",
            f"reports_dir={config.reports_dir}",
            f"cache_dir={config.cache_dir}",
        ],
    }
    config.output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def rank_keywords(
    texts: list[str],
    *,
    anchor_texts: list[str] | None = None,
    top_n: int = 30,
    min_count: int = 2,
) -> list[str]:
    token_counter: Counter[str] = Counter()
    phrase_counter: Counter[str] = Counter()
    anchor_counter: Counter[str] = Counter()
    for text in texts:
        tokens = _extract_tokens(text)
        token_counter.update(tokens)
        phrase_counter.update(_phrases(tokens))
    for text in anchor_texts or []:
        anchor_tokens = _extract_tokens(text)
        anchor_counter.update(anchor_tokens)
        anchor_counter.update(_phrases(anchor_tokens))

    scored: Counter[str] = Counter()
    for token, count in token_counter.items():
        if count >= min_count and _has_anchor_or_is_symbol(token, anchor_counter):
            scored[token] += count * _token_weight(token) * _anchor_weight(token, anchor_counter)
    for phrase, count in phrase_counter.items():
        if count >= min_count and _has_anchor_or_is_symbol(phrase, anchor_counter):
            scored[phrase] += count * 2 * _anchor_weight(phrase, anchor_counter)

    return [keyword for keyword, _ in scored.most_common(top_n)]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Derive search keywords from reports and cached news.")
    parser.add_argument("--cache-dir", type=Path, default=Path("cached_news"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--output", type=Path, default=Path("derived_keywords.json"))
    parser.add_argument("--start", type=_parse_date, default=None)
    parser.add_argument("--end", type=_parse_date, default=None)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--top-n", type=int, default=30)
    parser.add_argument("--min-count", type=int, default=2)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    end = args.end or date.today()
    start = args.start or end - timedelta(days=max(0, args.days - 1))
    payload = derive_keywords(
        KeywordDerivationConfig(
            cache_dir=args.cache_dir,
            reports_dir=args.reports_dir,
            output_path=args.output,
            start=start,
            end=end,
            top_n=args.top_n,
            min_count=args.min_count,
        )
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _load_report_texts(reports_dir: Path) -> list[str]:
    if not reports_dir.exists():
        return []
    return [path.read_text(encoding="utf-8") for path in sorted(reports_dir.glob("*.md"))]


def _load_news_texts(cache_dir: Path, start: date, end: date) -> list[str]:
    cache = NewsJsonlCache(cache_dir)
    return [f"{record.title}\n{record.body}" for record in cache.load(start, end)]


def _phrases(tokens: list[str]) -> list[str]:
    phrases: list[str] = []
    for index in range(len(tokens) - 1):
        first, second = tokens[index], tokens[index + 1]
        if first == second:
            continue
        phrases.append(f"{first} {second}")
    return phrases


def _extract_tokens(text: str) -> list[str]:
    cleaned = URL_RE.sub(" ", text)
    cleaned = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", cleaned)
    tokens = [_normalize_token(token) for token in TOKEN_RE.findall(cleaned)]
    return [token for token in tokens if _is_signal_token(token)]


def _normalize_token(token: str) -> str:
    stripped = token.strip("._-+").strip()
    if _is_ascii(stripped):
        return stripped.upper() if stripped.isupper() or len(stripped) <= 5 else stripped.lower()
    return stripped


def _token_weight(token: str) -> int:
    if _is_ascii(token) and token.upper() == token and 2 <= len(token) <= 8:
        return 3
    return 1


def _anchor_weight(token: str, anchor_counter: Counter[str]) -> int:
    return 4 if anchor_counter.get(token, 0) else 1


def _has_anchor_or_is_symbol(token: str, anchor_counter: Counter[str]) -> bool:
    if not anchor_counter:
        return True
    if anchor_counter.get(token, 0):
        return True
    compact = token.replace(" ", "")
    return _is_ascii(compact) and compact.upper() == compact and 2 <= len(compact) <= 8


def _is_signal_token(token: str) -> bool:
    lowered = token.lower()
    if len(token) < 2 or lowered in DEFAULT_STOPWORDS:
        return False
    if token.isdigit():
        return False
    if re.fullmatch(r"\d+[가-힣A-Za-z]*", token):
        return False
    if len(token) > 40:
        return False
    return True


def _is_ascii(value: str) -> bool:
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


def _resolve_window(start: date | None, end: date | None) -> tuple[date, date]:
    resolved_end = end or date.today()
    resolved_start = start or resolved_end - timedelta(days=6)
    return resolved_start, resolved_end


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


if __name__ == "__main__":
    raise SystemExit(main())
