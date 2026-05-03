from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from collect_news import load_keywords, parse_args, resolve_window, summarize
from domain_types import NewsRecord


class CollectNewsCliTest(unittest.TestCase):
    def test_parse_args_requires_tickers_and_accepts_sources(self):
        args = parse_args(["--tickers", "삼성전자", "AAPL", "--sources", "naver", "gdelt", "sec"])

        self.assertEqual(args.tickers, ["삼성전자", "AAPL"])
        self.assertEqual(args.sources, ["naver", "gdelt", "sec"])

    def test_resolve_window_uses_days_when_start_is_omitted(self):
        args = parse_args(["--tickers", "AAPL", "--days", "3"])

        start, end = resolve_window(args, today=date(2026, 5, 3))

        self.assertEqual(start, date(2026, 5, 1))
        self.assertEqual(end, date(2026, 5, 3))

    def test_load_keywords_from_group(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "keywords.json"
            path.write_text(json.dumps({"korea": ["실적", "가이던스"]}), encoding="utf-8")

            self.assertEqual(load_keywords(path, "korea"), ["실적", "가이던스"])

    def test_explicit_keywords_override_file(self):
        self.assertEqual(load_keywords("missing.json", "global", ["earnings"]), ["earnings"])


class SummarizeTest(unittest.TestCase):
    def test_summarize_counts_sources_and_tickers(self):
        records = [
            NewsRecord("AAPL", "t1", "b", datetime(2026, 5, 1), "naver_news"),
        ]

        summary = summarize(
            records=records,
            cached=records,
            written=1,
            start=date(2026, 5, 1),
            end=date(2026, 5, 3),
            sources=["naver"],
        )

        self.assertEqual(summary["fetched_count"], 1)
        self.assertEqual(summary["cached_count"], 1)
        self.assertEqual(summary["by_source"], {"naver_news": 1})
        self.assertEqual(summary["by_ticker"], {"AAPL": 1})


if __name__ == "__main__":
    unittest.main()
