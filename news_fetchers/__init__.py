"""News collection adapters."""

from .aggregator import AggregatingNewsFetcher
from .google_news_rss import GoogleNewsRssFetcher
from .naver_news import NaverNewsFetcher

__all__ = ["AggregatingNewsFetcher", "GoogleNewsRssFetcher", "NaverNewsFetcher"]

