"""SEC EDGAR filing adapter for US-listed companies."""

from __future__ import annotations

from datetime import date, datetime
import os
from typing import Any

import requests

try:
    from ..domain_types import NewsRecord
except ImportError:  # Allows running from project root without package install.
    from domain_types import NewsRecord


class SecEdgarFetcher:
    ticker_map_url = "https://www.sec.gov/files/company_tickers.json"
    submissions_url = "https://data.sec.gov/submissions/CIK{cik}.json"

    def __init__(self, session: Any | None = None, timeout: int = 15, user_agent: str | None = None) -> None:
        self.session = session or requests
        self.timeout = timeout
        self.user_agent = user_agent or os.getenv("SEC_USER_AGENT", "Auto-News-Analyst/0.1 contact@example.com")
        self._ticker_to_cik: dict[str, str] | None = None

    def fetch(self, tickers: list[str], start: date, end: date, keywords: list[str]) -> list[NewsRecord]:
        records: list[NewsRecord] = []
        ticker_to_cik = self._load_ticker_map()
        for ticker in tickers:
            cik = ticker_to_cik.get(ticker.upper())
            if not cik:
                continue
            records.extend(self._fetch_company(ticker=ticker, cik=cik, start=start, end=end, keywords=keywords))
        return records

    def _fetch_company(
        self,
        *,
        ticker: str,
        cik: str,
        start: date,
        end: date,
        keywords: list[str],
    ) -> list[NewsRecord]:
        response = self.session.get(
            self.submissions_url.format(cik=cik),
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        recent = response.json().get("filings", {}).get("recent", {})

        records: list[NewsRecord] = []
        for filing in _iter_recent_filings(recent):
            filing_date = date.fromisoformat(filing["filingDate"])
            if not start <= filing_date <= end:
                continue
            title = _filing_title(filing)
            if keywords and not _matches_keywords(title, keywords):
                continue
            accession = filing["accessionNumber"].replace("-", "")
            document_url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{filing['primaryDocument']}"
            )
            records.append(
                NewsRecord(
                    ticker=ticker,
                    title=title,
                    body=f"{filing['form']} filed on {filing['filingDate']}",
                    published_at=datetime.combine(filing_date, datetime.min.time()),
                    source="sec_edgar",
                    url=document_url,
                    metadata={
                        "provider": "sec_edgar",
                        "form": filing["form"],
                        "accession_number": filing["accessionNumber"],
                        "primary_document": filing["primaryDocument"],
                    },
                )
            )
        return records

    def _load_ticker_map(self) -> dict[str, str]:
        if self._ticker_to_cik is not None:
            return self._ticker_to_cik
        response = self.session.get(self.ticker_map_url, headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        self._ticker_to_cik = {
            str(item["ticker"]).upper(): str(item["cik_str"]).zfill(10)
            for item in payload.values()
            if item.get("ticker") and item.get("cik_str")
        }
        return self._ticker_to_cik

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"}


def _iter_recent_filings(recent: dict) -> list[dict[str, str]]:
    keys = ["accessionNumber", "filingDate", "form", "primaryDocument", "primaryDocDescription"]
    row_count = min(len(recent.get(key, [])) for key in keys) if all(key in recent for key in keys) else 0
    return [{key: str(recent[key][index]) for key in keys} for index in range(row_count)]


def _filing_title(filing: dict[str, str]) -> str:
    description = filing.get("primaryDocDescription", "").strip()
    if description:
        return f"{filing['form']} - {description}"
    return f"{filing['form']} filing"


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)
