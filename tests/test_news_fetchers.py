from datetime import date
import unittest

from news_fetchers.aggregator import dedupe_news
from news_fetchers.alpha_vantage_news import AlphaVantageNewsFetcher
from news_fetchers.dart_disclosures import DartDisclosureFetcher
from news_fetchers.finnhub_news import FinnhubNewsFetcher
from news_fetchers.gdelt_news import GdeltNewsFetcher
from news_fetchers.google_news_rss import GoogleNewsRssFetcher
from news_fetchers.investing_rss import InvestingRssFetcher
from news_fetchers.naver_news import NaverNewsFetcher
from news_fetchers.newsapi_global import NewsApiGlobalFetcher
from news_fetchers.sec_edgar import SecEdgarFetcher


class FakeResponse:
    def __init__(self, payload=None, text=""):
        self._payload = payload or {}
        self.text = text

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class QueueSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class NaverNewsFetcherTest(unittest.TestCase):
    def test_fetch_parses_and_filters_naver_news(self):
        response = FakeResponse(
            {
                "items": [
                    {
                        "title": "<b>삼성전자</b> 실적 개선",
                        "description": "영업이익 전망 상향",
                        "originallink": "https://example.com/a#fragment",
                        "pubDate": "Mon, 20 Apr 2026 09:00:00 +0900",
                    },
                    {
                        "title": "오래된 기사",
                        "description": "기간 밖",
                        "originallink": "https://example.com/old",
                        "pubDate": "Mon, 10 Mar 2026 09:00:00 +0900",
                    },
                ]
            }
        )
        session = FakeSession(response)
        fetcher = NaverNewsFetcher("id", "secret", session=session)

        records = fetcher.fetch(["삼성전자"], date(2026, 4, 1), date(2026, 4, 30), ["실적"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].title, "삼성전자 실적 개선")
        self.assertEqual(records[0].source, "naver_news")
        self.assertEqual(records[0].url, "https://example.com/a")
        self.assertIn("X-Naver-Client-Id", session.calls[0][1]["headers"])

    def test_unconfigured_naver_fetcher_returns_empty_list(self):
        fetcher = NaverNewsFetcher("", "", session=FakeSession(FakeResponse()))

        self.assertEqual(fetcher.fetch(["AAPL"], date(2026, 4, 1), date(2026, 4, 30), []), [])


class GoogleNewsRssFetcherTest(unittest.TestCase):
    def test_fetch_parses_google_rss(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss><channel>
          <item>
            <title>Apple guidance raised</title>
            <link>https://news.google.com/rss/articles/abc</link>
            <description>Analysts raise estimates</description>
            <pubDate>Mon, 20 Apr 2026 00:00:00 GMT</pubDate>
          </item>
        </channel></rss>
        """
        fetcher = GoogleNewsRssFetcher(session=FakeSession(FakeResponse(text=xml)))

        records = fetcher.fetch(["AAPL"], date(2026, 4, 1), date(2026, 4, 30), ["earnings"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].ticker, "AAPL")
        self.assertEqual(records[0].source, "google_news_rss")


class GdeltNewsFetcherTest(unittest.TestCase):
    def test_fetch_parses_gdelt_articles(self):
        session = FakeSession(
            FakeResponse(
                {
                    "articles": [
                        {
                            "title": "Nvidia data center demand rises",
                            "snippet": "AI infrastructure spending keeps growing",
                            "url": "https://example.com/a#frag",
                            "seendate": "20260420093000",
                            "domain": "example.com",
                            "language": "English",
                            "sourceCountry": "US",
                        }
                    ]
                }
            )
        )
        fetcher = GdeltNewsFetcher(session=session)

        records = fetcher.fetch(["NVDA"], date(2026, 4, 1), date(2026, 4, 30), ["AI"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source, "gdelt_doc")
        self.assertEqual(records[0].url, "https://example.com/a")
        self.assertEqual(session.calls[0][1]["params"]["format"], "json")


class InvestingRssFetcherTest(unittest.TestCase):
    def test_fetch_parses_official_investing_rss(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss><channel>
          <item>
            <title>Nvidia shares rise as AI capex expands</title>
            <link>https://www.investing.com/news/stock-market-news/example</link>
            <description>NVDA demand remains strong</description>
            <pubDate>2026-04-20 00:00:00</pubDate>
          </item>
        </channel></rss>
        """
        fetcher = InvestingRssFetcher(session=FakeSession(FakeResponse(text=xml)), feeds=("https://example.com/rss",))

        records = fetcher.fetch(["NVDA"], date(2026, 4, 1), date(2026, 4, 30), ["AI"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source, "investing_rss")
        self.assertEqual(records[0].ticker, "NVDA")


class SecEdgarFetcherTest(unittest.TestCase):
    def test_fetch_maps_ticker_and_parses_recent_filings(self):
        session = QueueSession(
            [
                FakeResponse({"0": {"ticker": "AAPL", "cik_str": 320193}}),
                FakeResponse(
                    {
                        "filings": {
                            "recent": {
                                "accessionNumber": ["0000320193-26-000001"],
                                "filingDate": ["2026-04-20"],
                                "form": ["8-K"],
                                "primaryDocument": ["aapl-20260420.htm"],
                                "primaryDocDescription": ["Current report"],
                            }
                        }
                    }
                ),
            ]
        )
        fetcher = SecEdgarFetcher(session=session, user_agent="test@example.com")

        records = fetcher.fetch(["AAPL"], date(2026, 4, 1), date(2026, 4, 30), ["current"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source, "sec_edgar")
        self.assertIn("0000320193", records[0].url)
        self.assertIn("User-Agent", session.calls[0][1]["headers"])


class AlphaVantageNewsFetcherTest(unittest.TestCase):
    def test_unconfigured_fetcher_returns_empty_list(self):
        fetcher = AlphaVantageNewsFetcher(api_key="", session=FakeSession(FakeResponse()))

        self.assertEqual(fetcher.fetch(["AAPL"], date(2026, 4, 1), date(2026, 4, 30), []), [])

    def test_fetch_parses_feed(self):
        session = FakeSession(
            FakeResponse(
                {
                    "feed": [
                        {
                            "title": "Apple earnings preview",
                            "summary": "Margin focus",
                            "url": "https://example.com/alpha",
                            "time_published": "20260420T093000",
                            "source": "Example",
                            "overall_sentiment_score": "0.2",
                            "overall_sentiment_label": "Bullish",
                        }
                    ]
                }
            )
        )
        fetcher = AlphaVantageNewsFetcher(api_key="key", session=session)

        records = fetcher.fetch(["AAPL"], date(2026, 4, 1), date(2026, 4, 30), ["earnings"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source, "alpha_vantage_news")
        self.assertEqual(session.calls[0][1]["params"]["function"], "NEWS_SENTIMENT")


class FinnhubNewsFetcherTest(unittest.TestCase):
    def test_fetch_parses_company_news(self):
        session = FakeSession(
            FakeResponse(
                [
                    {
                        "headline": "Microsoft capex rises",
                        "summary": "Cloud demand",
                        "url": "https://example.com/finnhub",
                        "datetime": 1776677400,
                        "source": "Example",
                    }
                ]
            )
        )
        fetcher = FinnhubNewsFetcher(api_key="key", session=session)

        records = fetcher.fetch(["MSFT"], date(2026, 4, 1), date(2026, 4, 30), ["capex"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source, "finnhub_news")


class NewsApiGlobalFetcherTest(unittest.TestCase):
    def test_fetch_parses_articles(self):
        session = FakeSession(
            FakeResponse(
                {
                    "articles": [
                        {
                            "title": "TSMC demand",
                            "description": "AI chips",
                            "url": "https://example.com/newsapi",
                            "publishedAt": "2026-04-20T09:30:00Z",
                            "source": {"name": "Example"},
                        }
                    ]
                }
            )
        )
        fetcher = NewsApiGlobalFetcher(api_key="key", session=session)

        records = fetcher.fetch(["TSM"], date(2026, 4, 1), date(2026, 4, 30), ["AI"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source, "newsapi_global")


class DartDisclosureFetcherTest(unittest.TestCase):
    def test_fetch_parses_matching_disclosures(self):
        session = FakeSession(
            FakeResponse(
                {
                    "status": "000",
                    "total_page": "1",
                    "list": [
                        {
                            "corp_name": "삼성전자",
                            "report_nm": "분기보고서",
                            "flr_nm": "삼성전자",
                            "rcept_dt": "20260420",
                            "rcept_no": "20260420000001",
                            "corp_code": "00126380",
                            "stock_code": "005930",
                        }
                    ],
                }
            )
        )
        fetcher = DartDisclosureFetcher(api_key="key", session=session)

        records = fetcher.fetch(["삼성전자"], date(2026, 4, 1), date(2026, 4, 30), ["분기"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source, "dart_disclosure")
        self.assertIn("rcpNo=20260420000001", records[0].url)


class DedupeNewsTest(unittest.TestCase):
    def test_dedupe_removes_same_url_and_title(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss><channel>
          <item>
            <title>Same</title>
            <link>https://example.com/a#one</link>
            <description>one</description>
            <pubDate>Mon, 20 Apr 2026 00:00:00 GMT</pubDate>
          </item>
          <item>
            <title>Same</title>
            <link>https://example.com/a#two</link>
            <description>two</description>
            <pubDate>Mon, 20 Apr 2026 01:00:00 GMT</pubDate>
          </item>
        </channel></rss>
        """
        records = GoogleNewsRssFetcher(session=FakeSession(FakeResponse(text=xml))).fetch(
            ["AAPL"], date(2026, 4, 1), date(2026, 4, 30), []
        )

        self.assertEqual(len(dedupe_news(records)), 1)


if __name__ == "__main__":
    unittest.main()
