"""Shared helpers for news fetchers."""

from __future__ import annotations

from datetime import date, datetime
from email.utils import parsedate_to_datetime
import html
import re
from urllib.parse import urlparse


def clean_html(value: str) -> str:
    text = re.sub(r"</?b>", "", value or "")
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def parse_feed_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed


def in_date_range(value: datetime, start: date, end: date) -> bool:
    current = value.date()
    return start <= current <= end


def canonical_url(value: str) -> str:
    parsed = urlparse(value or "")
    if not parsed.scheme or not parsed.netloc:
        return value or ""
    return parsed._replace(fragment="").geturl()

