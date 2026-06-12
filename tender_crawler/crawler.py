from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import httpx
import yaml
from bs4 import BeautifulSoup

from tender_crawler.profile import (
    DEFAULT_BUSINESS_PROFILE,
    DEFAULT_EXCLUDE_KEYWORDS,
    DEFAULT_INCLUDE_KEYWORDS,
    evaluate_relevance,
)
from tender_crawler.schemas import CrawlResult, TenderIn
from tender_crawler.settings import get_settings


@dataclass(frozen=True)
class SourceConfig:
    name: str
    type: str
    list_url: str
    enabled: bool = True
    base_url: Optional[str] = None
    page_url_pattern: Optional[str] = None
    pages: int = 1
    encoding: Optional[str] = None
    list_item_selector: str = ""
    title_selector: str = ""
    link_selector: str = "a"
    date_selector: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    business_profile: str = DEFAULT_BUSINESS_PROFILE
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    min_relevance_score: int = 0


def load_sources(config_path: str | Path) -> List[SourceConfig]:
    with Path(config_path).open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file) or {}

    defaults = {
        "business_profile": payload.get("business_profile", DEFAULT_BUSINESS_PROFILE),
        "include_keywords": payload.get("include_keywords", DEFAULT_INCLUDE_KEYWORDS),
        "exclude_keywords": payload.get("exclude_keywords", DEFAULT_EXCLUDE_KEYWORDS),
        "min_relevance_score": payload.get("min_relevance_score", 0),
    }
    sources: List[SourceConfig] = []
    for item in payload.get("sources", []):
        merged = {**defaults, **item}
        sources.append(SourceConfig(**merged))
    return sources


class TenderCrawler:
    def __init__(self) -> None:
        self.settings = get_settings()

    def crawl_source(self, source: SourceConfig) -> Tuple[CrawlResult, List[TenderIn]]:
        if not source.enabled:
            return CrawlResult(source=source.name, found=0, inserted=0, updated=0), []

        if source.type not in {"static_list", "ccgp_category"}:
            return (
                CrawlResult(
                    source=source.name,
                    found=0,
                    inserted=0,
                    updated=0,
                    errors=[f"Unsupported source type: {source.type}"],
                ),
                [],
            )

        items: List[TenderIn] = []
        raw_found = 0
        for page_url in self._page_urls(source):
            html = self._fetch_html(page_url, source.encoding)
            if source.type == "ccgp_category":
                page_raw_found, page_items = self._parse_ccgp_list(source, html, page_url)
            else:
                page_raw_found, page_items = self._parse_static_list(source, html, page_url)
            raw_found += page_raw_found
            items.extend(page_items)
            time.sleep(self.settings.request_delay_seconds)

        result = CrawlResult(source=source.name, found=len(items), raw_found=raw_found, inserted=0, updated=0)
        return result, items

    def _fetch_html(
        self,
        url: str,
        encoding: Optional[str] = None,
    ) -> str:
        last_error: Optional[Exception] = None
        for trust_env in (True, False):
            try:
                headers = {
                    "User-Agent": self.settings.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                }
                timeout = httpx.Timeout(
                    self.settings.request_timeout_seconds,
                    connect=self.settings.request_timeout_seconds,
                )
                transport = httpx.HTTPTransport(retries=2)
                with httpx.Client(
                    timeout=timeout,
                    headers=headers,
                    transport=transport,
                    trust_env=trust_env,
                    follow_redirects=True,
                ) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    if encoding:
                        response.encoding = encoding
                    return response.text
            except Exception as exc:
                last_error = exc
                continue

        raise RuntimeError(f"Failed to fetch {url}: {last_error!r}")

    def _page_urls(self, source: SourceConfig) -> List[str]:
        if source.pages <= 1:
            return [source.list_url]

        urls = [source.list_url]
        for page_number in range(2, source.pages + 1):
            if source.page_url_pattern:
                urls.append(source.page_url_pattern.format(page=page_number, index=page_number - 1))
            elif source.list_url.endswith("/"):
                urls.append(urljoin(source.list_url, f"index_{page_number - 1}.htm"))
        return urls

    def _parse_static_list(
        self,
        source: SourceConfig,
        html: str,
        page_url: str,
    ) -> Tuple[int, List[TenderIn]]:
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select(source.list_item_selector)
        tenders: List[TenderIn] = []
        base_url = source.base_url or page_url

        for row in rows:
            title_node = row.select_one(source.title_selector) if source.title_selector else row
            link_node = row.select_one(source.link_selector) if source.link_selector else title_node
            if title_node is None or link_node is None:
                continue

            title = title_node.get_text(" ", strip=True)
            href = link_node.get("href")
            if not title or not href:
                continue

            date_text = None
            if source.date_selector:
                date_node = row.select_one(source.date_selector)
                date_text = date_node.get_text(" ", strip=True) if date_node else None

            tender = TenderIn(
                source=source.name,
                source_url=urljoin(base_url, href),
                title=title,
                summary=row.get_text(" ", strip=True),
                province=source.province,
                city=source.city,
                publish_date=date_text,
                category=source.category,
                business_profile=source.business_profile,
                raw_text=row.get_text("\n", strip=True),
            )
            enriched = self._apply_relevance(source, tender)
            if enriched is not None:
                tenders.append(enriched)

        return len(rows), tenders

    def _parse_ccgp_list(
        self,
        source: SourceConfig,
        html: str,
        page_url: str,
    ) -> Tuple[int, List[TenderIn]]:
        soup = BeautifulSoup(html, "html.parser")
        rows = self._select_first_non_empty(
            soup,
            [
                "ul.vT-srch-result-list-bid li",
                ".vT-srch-result-list-bid li",
                ".c_list li",
                ".main_list li",
                ".list li",
                "li",
            ],
        )
        tenders: List[TenderIn] = []
        base_url = source.base_url or page_url

        for row in rows:
            link_node = row.select_one("a[href]")
            if link_node is None:
                continue
            title = link_node.get_text(" ", strip=True)
            href = link_node.get("href")
            if not title or not href:
                continue

            row_text = row.get_text(" ", strip=True)
            tender = TenderIn(
                source=source.name,
                source_url=urljoin(base_url, href),
                title=title,
                summary=row_text,
                province=source.province or self._extract_field(row_text, ["地域", "地区", "省份"]),
                city=source.city,
                buyer=self._extract_field(row_text, ["采购人", "招标人", "采购单位"]),
                agency=self._extract_field(row_text, ["代理机构", "采购代理机构"]),
                publish_date=self._extract_date(row_text),
                category=source.category,
                business_profile=source.business_profile,
                raw_text=row.get_text("\n", strip=True),
            )
            enriched = self._apply_relevance(source, tender)
            if enriched is not None:
                tenders.append(enriched)

        return len(rows), tenders

    def _select_first_non_empty(self, soup: BeautifulSoup, selectors: List[str]):
        for selector in selectors:
            rows = soup.select(selector)
            if rows:
                return rows
        return []

    def _extract_date(self, text: str) -> Optional[str]:
        match = re.search(r"\d{4}[-年/]\d{1,2}[-月/]\d{1,2}", text)
        if not match:
            return None
        return match.group(0).replace("年", "-").replace("月", "-").replace("日", "")

    def _extract_field(self, text: str, labels: List[str]) -> Optional[str]:
        for label in labels:
            match = re.search(rf"{label}\s*[:：]\s*([^|｜\s]+)", text)
            if match:
                return match.group(1).strip()
        return None

    def _apply_relevance(self, source: SourceConfig, tender: TenderIn) -> Optional[TenderIn]:
        text = " ".join(
            value
            for value in [
                tender.title,
                tender.summary,
                tender.buyer,
                tender.agency,
                tender.category,
                tender.raw_text,
            ]
            if value
        )
        score, matched = evaluate_relevance(
            text,
            include_keywords=source.include_keywords,
            exclude_keywords=source.exclude_keywords,
        )
        if score < source.min_relevance_score:
            return None

        data = tender.model_dump()
        data["relevance_score"] = score
        data["matched_keywords"] = ",".join(matched)
        data["business_profile"] = source.business_profile
        return TenderIn(**data)
