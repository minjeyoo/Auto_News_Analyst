from datetime import date
import unittest

from news_fetchers.aggregator import dedupe_news
from news_fetchers.google_news_rss import GoogleNewsRssFetcher
from news_fetchers.naver_news import NaverNewsFetcher


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

