from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from collect_news import (
    build_collection_keywords,
    load_company_terms,
    load_global_queries,
    load_keywords,
    parse_args,
    resolve_window,
    summarize,
)
from domain_types import NewsRecord


class CollectNewsCliTest(unittest.TestCase):
    def test_parse_args_requires_tickers_and_accepts_sources(self):
        args = parse_args(["--tickers", "삼성전자", "AAPL", "--sources", "naver", "gdelt", "sec"])

        self.assertEqual(args.tickers, ["삼성전자", "AAPL"])
        self.assertEqual(args.sources, ["naver", "gdelt", "sec"])

    def test_default_sources_are_naver_and_google(self):
        args = parse_args(["--tickers", "삼성전자"])

        self.assertEqual(args.sources, ["naver", "google"])

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

    def test_load_global_queries_from_industry_themes(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "themes.json"
            path.write_text(
                json.dumps({"ai": {"global_queries": ["AI capex", "HBM supply"]}}),
                encoding="utf-8",
            )

            self.assertEqual(load_global_queries(path), ["AI capex", "HBM supply"])

    def test_load_company_terms_matches_ticker_or_alias(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "aliases.json"
            path.write_text(
                json.dumps(
                    {
                        "삼성전자": {
                            "tickers": ["005930.KS"],
                            "korean_names": ["삼성전자"],
                            "english_names": ["Samsung Electronics"],
                            "aliases": ["Samsung HBM"],
                            "business_keywords": ["HBM", "DRAM"],
                        }
                    }
                ),
                encoding="utf-8",
            )

            terms = load_company_terms(path, ["005930.KS"])

            self.assertIn("Samsung HBM", terms)
            self.assertIn("DRAM", terms)

    def test_build_collection_keywords_can_add_global_queries_and_aliases(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            theme_path = root / "themes.json"
            alias_path = root / "aliases.json"
            theme_path.write_text(json.dumps({"ai": {"global_queries": ["AI capex"]}}), encoding="utf-8")
            alias_path.write_text(
                json.dumps({"Nvidia": {"tickers": ["NVDA"], "business_keywords": ["Blackwell"]}}),
                encoding="utf-8",
            )

            keywords = build_collection_keywords(
                base_keywords=["earnings"],
                tickers=["NVDA"],
                include_global_queries=True,
                include_company_aliases=True,
                theme_file=theme_path,
                company_alias_file=alias_path,
            )

            self.assertEqual(keywords, ["earnings", "AI capex", "NVDA", "Nvidia", "Blackwell"])


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
