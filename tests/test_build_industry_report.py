from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from build_industry_report import IndustryReportConfig, build_industry_report, match_records_to_themes
from domain_types import NewsRecord
from news_cache import NewsJsonlCache


class BuildIndustryReportTest(unittest.TestCase):
    def test_match_records_to_themes_uses_source_weighted_evidence(self):
        themes = {
            "ai_memory": {
                "description": "AI infrastructure HBM memory",
                "global_queries": ["HBM memory"],
                "global_stocks": ["NVDA"],
                "korea_stocks": ["SK하이닉스"],
            }
        }
        records = [
            NewsRecord("NVDA", "HBM demand rises", "", datetime(2026, 5, 3), "google_news_rss"),
            NewsRecord("NVDA", "HBM demand rises", "", datetime(2026, 5, 3), "sec_edgar"),
        ]

        matches = match_records_to_themes(records, themes)

        self.assertEqual(matches["ai_memory"][0][0].source, "sec_edgar")

    def test_build_industry_report_writes_source_aware_markdown(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = NewsJsonlCache(root / "cache")
            cache.write_records(
                [
                    NewsRecord(
                        "NVDA",
                        "AI infrastructure HBM filing",
                        "memory capex",
                        datetime(2026, 5, 3),
                        "sec_edgar",
                        "https://example.com/sec",
                    )
                ]
            )
            themes_path = root / "themes.json"
            themes_path.write_text(
                json.dumps(
                    {
                        "ai_memory": {
                            "description": "AI infrastructure HBM memory",
                            "global_queries": ["HBM memory"],
                            "global_stocks": ["NVDA"],
                            "korea_stocks": ["SK하이닉스"],
                        }
                    }
                ),
                encoding="utf-8",
            )

            markdown = build_industry_report(
                IndustryReportConfig(
                    cache_dir=root / "cache",
                    themes_path=themes_path,
                    output_path=root / "report.md",
                    start=date(2026, 5, 3),
                    end=date(2026, 5, 3),
                )
            )

            self.assertIn("출처 기반 글로벌 산업 리포트", markdown)
            self.assertIn("SEC EDGAR", markdown)
            self.assertTrue((root / "report.md").exists())


if __name__ == "__main__":
    unittest.main()
