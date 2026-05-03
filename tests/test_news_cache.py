from datetime import date, datetime
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest

from domain_types import NewsRecord
from news_cache import CachedNewsFetcher, NewsJsonlCache, news_record_from_dict, news_record_to_dict


class FakeFetcher:
    def __init__(self, records):
        self.records = records
        self.calls = 0

    def fetch(self, tickers, start, end, keywords):
        self.calls += 1
        return self.records


def record(ticker="AAPL", day=20, title="Apple guidance raised"):
    return NewsRecord(
        ticker=ticker,
        title=title,
        body="Analysts raised estimates.",
        published_at=datetime(2026, 4, day, 9, 0, 0),
        source="unit_test",
        url=f"https://example.com/{ticker}/{day}",
        metadata={"query": ticker},
    )


class NewsRecordSerializationTest(unittest.TestCase):
    def test_roundtrip_preserves_record_fields(self):
        original = record()

        restored = news_record_from_dict(news_record_to_dict(original))

        self.assertEqual(restored, original)


class NewsJsonlCacheTest(unittest.TestCase):
    def test_write_and_load_records_by_date_range(self):
        with TemporaryDirectory() as tmp:
            cache = NewsJsonlCache(Path(tmp))
            cache.write_records([record(day=20), record(day=21, ticker="MSFT")])

            loaded = cache.load(date(2026, 4, 20), date(2026, 4, 20))

            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].ticker, "AAPL")
            self.assertIn("collected_at", loaded[0].metadata)

    def test_write_dedupes_existing_records(self):
        with TemporaryDirectory() as tmp:
            cache = NewsJsonlCache(Path(tmp))
            same = record()

            cache.write_records([same])
            cache.write_records([same])

            loaded = cache.load(date(2026, 4, 20), date(2026, 4, 20))
            self.assertEqual(len(loaded), 1)

    def test_load_filters_tickers_and_sources(self):
        with TemporaryDirectory() as tmp:
            cache = NewsJsonlCache(Path(tmp))
            cache.write_records([record(), record(ticker="MSFT", title="Microsoft")])

            loaded = cache.load(date(2026, 4, 20), date(2026, 4, 20), tickers=["MSFT"])

            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].ticker, "MSFT")


class CachedNewsFetcherTest(unittest.TestCase):
    def test_refresh_false_uses_cache_only(self):
        with TemporaryDirectory() as tmp:
            cache = NewsJsonlCache(Path(tmp))
            cached = record()
            cache.write_records([cached])
            upstream = FakeFetcher([record(ticker="MSFT", title="Fresh")])
            fetcher = CachedNewsFetcher(upstream, cache, refresh=False)

            loaded = fetcher.fetch(["AAPL", "MSFT"], date(2026, 4, 20), date(2026, 4, 20), [])

            self.assertEqual(upstream.calls, 0)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].ticker, "AAPL")

    def test_refresh_true_merges_fresh_and_cached_records(self):
        with TemporaryDirectory() as tmp:
            cache = NewsJsonlCache(Path(tmp))
            cache.write_records([record()])
            upstream = FakeFetcher([record(ticker="MSFT", title="Fresh")])
            fetcher = CachedNewsFetcher(upstream, cache, refresh=True)

            loaded = fetcher.fetch(["AAPL", "MSFT"], date(2026, 4, 20), date(2026, 4, 20), [])
            reloaded = cache.load(date(2026, 4, 20), date(2026, 4, 20))

            self.assertEqual(upstream.calls, 1)
            self.assertEqual({item.ticker for item in loaded}, {"AAPL", "MSFT"})
            self.assertEqual({item.ticker for item in reloaded}, {"AAPL", "MSFT"})


if __name__ == "__main__":
    unittest.main()

