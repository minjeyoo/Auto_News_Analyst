"""News collection adapters."""

from .aggregator import AggregatingNewsFetcher
from .alpha_vantage_news import AlphaVantageNewsFetcher
from .dart_disclosures import DartDisclosureFetcher
from .finnhub_news import FinnhubNewsFetcher
from .gdelt_news import GdeltNewsFetcher
from .google_news_rss import GoogleNewsRssFetcher
from .investing_rss import InvestingRssFetcher
from .naver_news import NaverNewsFetcher
from .newsapi_global import NewsApiGlobalFetcher
from .sec_edgar import SecEdgarFetcher

__all__ = [
    "AggregatingNewsFetcher",
    "AlphaVantageNewsFetcher",
    "DartDisclosureFetcher",
    "FinnhubNewsFetcher",
    "GdeltNewsFetcher",
    "GoogleNewsRssFetcher",
    "InvestingRssFetcher",
    "NaverNewsFetcher",
    "NewsApiGlobalFetcher",
    "SecEdgarFetcher",
]
