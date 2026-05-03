from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from derive_keywords import KeywordDerivationConfig, derive_keywords, rank_keywords
from domain_types import NewsRecord
from news_cache import NewsJsonlCache


class DeriveKeywordsTest(unittest.TestCase):
    def test_rank_keywords_prefers_repeated_domain_phrases(self):
        keywords = rank_keywords(
            [
                "AI infrastructure capex and HBM demand",
                "AI infrastructure spending drives HBM demand",
                "battery demand is different",
            ],
            top_n=5,
            min_count=2,
        )

        self.assertIn("AI infrastructure", keywords)
        self.assertIn("HBM", keywords)

    def test_derive_keywords_reads_reports_and_cached_news(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            reports.joinpath("daily.md").write_text("AI infrastructure HBM capex", encoding="utf-8")
            cache = NewsJsonlCache(root / "cache")
            cache.write_records(
                [
                    NewsRecord(
                        ticker="NVDA",
                        title="AI infrastructure capex rises",
                        body="HBM demand keeps growing",
                        published_at=datetime(2026, 5, 3, 9, 0),
                        source="gdelt_doc",
                    )
                ]
            )

            payload = derive_keywords(
                KeywordDerivationConfig(
                    cache_dir=root / "cache",
                    reports_dir=reports,
                    output_path=root / "derived_keywords.json",
                    start=date(2026, 5, 3),
                    end=date(2026, 5, 3),
                    top_n=10,
                    min_count=1,
                )
            )

            self.assertIn("global", payload)
            self.assertTrue((root / "derived_keywords.json").exists())
            self.assertIn("AI infrastructure", payload["global"])


if __name__ == "__main__":
    unittest.main()
