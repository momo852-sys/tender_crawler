from __future__ import annotations

from pathlib import Path
import traceback
from typing import List

from sqlalchemy.orm import Session

from tender_crawler.crawler import TenderCrawler, load_sources
from tender_crawler.dify_client import DifyClient
from tender_crawler.exporter import export_tenders_to_csv
from tender_crawler.repository import upsert_tender
from tender_crawler.repository import search_tenders
from tender_crawler.schemas import CrawlResult, WorkflowRequest, WorkflowResponse


def run_crawl(config_path: str, session: Session) -> List[CrawlResult]:
    crawler = TenderCrawler()
    sources = load_sources(Path(config_path))
    results: List[CrawlResult] = []

    for source in sources:
        try:
            result, items = crawler.crawl_source(source)
            for item in items:
                _, inserted = upsert_tender(session, item)
                if inserted:
                    result.inserted += 1
                else:
                    result.updated += 1
            session.commit()
            results.append(result)
        except Exception as exc:
            session.rollback()
            results.append(
                CrawlResult(
                    source=source.name,
                    found=0,
                    raw_found=0,
                    inserted=0,
                    updated=0,
                    errors=[f"{type(exc).__name__}: {exc!r}", traceback.format_exc(limit=3)],
                )
            )

    return results


def run_workflow(request: WorkflowRequest, session: Session) -> WorkflowResponse:
    crawl_results = run_crawl(request.config_path, session)
    candidates = search_tenders(
        session=session,
        keyword=request.keyword,
        min_relevance_score=request.min_relevance_score,
        limit=request.limit,
    )

    exported_csv = None
    if request.export_csv:
        exported_csv = str(export_tenders_to_csv(candidates))

    dify_uploaded = False
    dify_message = None
    if request.upload_to_dify and exported_csv:
        dify_message = DifyClient().upload_file_to_dataset(exported_csv)
        dify_uploaded = "not configured" not in dify_message.lower()

    return WorkflowResponse(
        crawl_results=crawl_results,
        exported_csv=exported_csv,
        dify_uploaded=dify_uploaded,
        dify_message=dify_message,
        total_candidates=len(candidates),
    )
