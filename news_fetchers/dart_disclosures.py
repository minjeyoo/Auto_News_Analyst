"""OpenDART disclosure adapter for Korean companies."""

from __future__ import annotations

from datetime import date, datetime
import os
from typing import Any

import requests

try:
    from ..domain_types import NewsRecord
except ImportError:  # Allows running from project root without package install.
    from domain_types import NewsRecord

from .common import canonical_url, clean_html


class DartDisclosureFetcher:
    base_url = "https://opendart.fss.or.kr/api/list.json"

    def __init__(self, api_key: str | None = None, session: Any | None = None, timeout: int = 15, page_count: int = 100) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("DART_API_KEY", "")
        self.session = session or requests
        self.timeout = timeout
        self.page_count = page_count

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        if not self.api_key:
            return []
        records: list[NewsRecord] = []
        page_no = 1
        while True:
            response = self.session.get(
                self.base_url,
                params={
                    "crtfc_key": self.api_key,
                    "bgn_de": f"{start:%Y%m%d}",
                    "end_de": f"{end:%Y%m%d}",
                    "page_no": page_no,
                    "page_count": self.page_count,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") not in {"000", "013"}:
                raise ValueError(f"DART API error {payload.get('status')}: {payload.get('message')}")
            records.extend(_parse_disclosures(payload.get("list", []), tickers, keywords))
            total_page = int(payload.get("total_page") or page_no)
            if page_no >= total_page or not payload.get("list"):
                break
            page_no += 1
        return records


def _parse_disclosures(items: list[dict], tickers: list[str], keywords: list[str]) -> list[NewsRecord]:
    records: list[NewsRecord] = []
    for item in items:
        corp_name = str(item.get("corp_name", ""))
        report_name = clean_html(str(item.get("report_nm", "")))
        text = f"{corp_name} {report_name}"
        matched_ticker = _matched_term(text, tickers)
        if not matched_ticker:
            continue
        if keywords and not _matched_term(text, keywords):
            continue
        filing_date = datetime.strptime(str(item.get("rcept_dt", "")), "%Y%m%d")
        receipt_no = str(item.get("rcept_no", ""))
        records.append(
            NewsRecord(
                ticker=matched_ticker,
                title=f"{corp_name} - {report_name}",
                body=str(item.get("flr_nm", "")),
                published_at=filing_date,
                source="dart_disclosure",
                url=canonical_url(f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}"),
                metadata={
                    "provider": "dart_disclosure",
                    "corp_code": str(item.get("corp_code", "")),
                    "stock_code": str(item.get("stock_code", "")),
                    "receipt_no": receipt_no,
                },
            )
        )
    return records


def _matched_term(text: str, candidates: list[str]) -> str:
    lowered = text.lower()
    for candidate in candidates:
        if candidate.lower() in lowered:
            return candidate
    return ""
