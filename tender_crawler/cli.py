from __future__ import annotations

import argparse
from typing import Optional

from tender_crawler.db import SessionLocal, init_db
from tender_crawler.repository import search_tenders, upsert_tender
from tender_crawler.schemas import TenderIn
from tender_crawler.service import run_crawl


def seed_sample() -> None:
    init_db()
    sample = TenderIn(
        source="sample",
        source_url="https://example.com/tenders/001",
        title="示例：某道路施工项目招标公告",
        summary="用于验证 Dify 检索链路的样例数据。",
        province="示例省份",
        city="示例城市",
        buyer="示例采购单位",
        budget="1000万元",
        publish_date="2026-06-11",
        deadline="2026-06-30",
        category="工程招标",
        business_profile="beijing_guangheng_accounting_firm",
        matched_keywords="审计,财务决算",
        relevance_score=7,
        raw_text="某道路施工项目招标公告，预算 1000 万元，投标截止 2026-06-30。",
    )
    with SessionLocal() as session:
        _, inserted = upsert_tender(session, sample)
        session.commit()
    print("Inserted sample tender." if inserted else "Updated sample tender.")


def crawl(config: str) -> None:
    init_db()
    with SessionLocal() as session:
        results = run_crawl(config, session)
    for result in results:
        print(result.model_dump())


def search(keyword: Optional[str], limit: int, min_relevance_score: Optional[int]) -> None:
    init_db()
    with SessionLocal() as session:
        tenders = search_tenders(
            session,
            keyword=keyword,
            limit=limit,
            min_relevance_score=min_relevance_score,
        )
    for tender in tenders:
        print(
            f"[{tender.id}] score={tender.relevance_score} "
            f"keywords={tender.matched_keywords or '-'} | {tender.title} | {tender.source_url}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Tender crawler command line")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("seed-sample")

    crawl_parser = subparsers.add_parser("crawl")
    crawl_parser.add_argument("--config", default="configs/sources.example.yaml")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--keyword", default=None)
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--min-relevance-score", type=int, default=None)

    args = parser.parse_args()
    if args.command == "seed-sample":
        seed_sample()
    elif args.command == "crawl":
        crawl(args.config)
    elif args.command == "search":
        search(args.keyword, args.limit, args.min_relevance_score)


if __name__ == "__main__":
    main()
