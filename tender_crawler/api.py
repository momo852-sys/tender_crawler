from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy.orm import Session

from tender_crawler.db import get_session, init_db
from tender_crawler.repository import search_tenders
from tender_crawler.schemas import (
    CrawlRequest,
    CrawlResult,
    ExternalKnowledgeRecord,
    ExternalKnowledgeRetrievalRequest,
    ExternalKnowledgeRetrievalResponse,
    TenderOut,
    WorkflowRequest,
    WorkflowResponse,
)
from tender_crawler.service import run_crawl, run_workflow
from tender_crawler.settings import get_settings

app = FastAPI(title="Tender Crawler Agent", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def require_token(authorization: Optional[str] = Header(default=None)) -> None:
    settings = get_settings()
    if settings.api_token == "change-me":
        return
    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid API token")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/tenders/search", response_model=List[TenderOut])
def search(
    keyword: Optional[str] = Query(default=None),
    province: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    min_relevance_score: Optional[int] = Query(default=None, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> List[TenderOut]:
    return search_tenders(
        session=session,
        keyword=keyword,
        province=province,
        city=city,
        category=category,
        min_relevance_score=min_relevance_score,
        limit=limit,
    )


@app.post(
    "/crawl/run",
    response_model=List[CrawlResult],
    dependencies=[Depends(require_token)],
)
def crawl(request: CrawlRequest, session: Session = Depends(get_session)) -> List[CrawlResult]:
    return run_crawl(request.config_path, session)


@app.post(
    "/workflow/run",
    response_model=WorkflowResponse,
    dependencies=[Depends(require_token)],
)
def workflow(
    request: WorkflowRequest,
    session: Session = Depends(get_session),
) -> WorkflowResponse:
    return run_workflow(request, session)


@app.post(
    "/external-knowledge/retrieval",
    response_model=ExternalKnowledgeRetrievalResponse,
    dependencies=[Depends(require_token)],
)
@app.post(
    "/retrieval",
    response_model=ExternalKnowledgeRetrievalResponse,
    dependencies=[Depends(require_token)],
)
def external_knowledge_retrieval(
    request: ExternalKnowledgeRetrievalRequest,
    session: Session = Depends(get_session),
) -> ExternalKnowledgeRetrievalResponse:
    settings = get_settings()
    if settings.dify_dataset_id and request.knowledge_id != settings.dify_dataset_id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    tenders = search_tenders(
        session=session,
        keyword=request.query,
        min_relevance_score=0,
        limit=max(request.retrieval_setting.top_k, 1),
    )

    records: List[ExternalKnowledgeRecord] = []
    for tender in tenders:
        score = _score_tender_for_external_knowledge(tender.relevance_score)
        if score < request.retrieval_setting.score_threshold:
            continue

        records.append(
            ExternalKnowledgeRecord(
                content=_format_tender_content(tender),
                score=score,
                title=tender.title,
                metadata=_clean_metadata(
                    {
                        "id": tender.id,
                        "source": tender.source,
                        "source_url": tender.source_url,
                        "province": tender.province,
                        "city": tender.city,
                        "category": tender.category,
                        "matched_keywords": tender.matched_keywords,
                        "relevance_score": tender.relevance_score,
                    }
                ),
            )
        )

    return ExternalKnowledgeRetrievalResponse(records=records)


def _score_tender_for_external_knowledge(relevance_score: int) -> float:
    return min(1.0, max(0.1, relevance_score / 10))


def _format_tender_content(tender) -> str:
    return "\n".join(
        part
        for part in [
            f"项目名称：{tender.title}",
            f"来源：{tender.source}",
            f"公告链接：{tender.source_url}",
            f"地区：{tender.province or ''} {tender.city or ''}".strip(),
            f"采购人：{tender.buyer or ''}",
            f"代理机构：{tender.agency or ''}",
            f"预算：{tender.budget or ''}",
            f"发布时间：{tender.publish_date or ''}",
            f"截止时间：{tender.deadline or ''}",
            f"分类：{tender.category or ''}",
            f"匹配关键词：{tender.matched_keywords or ''}",
            f"相关度评分：{tender.relevance_score}",
            f"摘要：{tender.summary or ''}",
        ]
        if part
    )


def _clean_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in metadata.items() if value is not None}
