from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from tender_crawler.models import Tender
from tender_crawler.schemas import TenderIn


def upsert_tender(session: Session, item: TenderIn) -> Tuple[Tender, bool]:
    stmt = select(Tender).where(
        Tender.source == item.source,
        Tender.source_url == item.source_url,
    )
    existing = session.scalar(stmt)
    if existing is None:
        tender = Tender(**item.model_dump())
        session.add(tender)
        session.flush()
        return tender, True

    for key, value in item.model_dump().items():
        setattr(existing, key, value)
    session.flush()
    return existing, False


def search_tenders(
    session: Session,
    keyword: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    min_relevance_score: Optional[int] = None,
    limit: int = 20,
) -> List[Tender]:
    stmt = select(Tender).order_by(
        Tender.relevance_score.desc(),
        Tender.publish_date.desc(),
        Tender.id.desc(),
    )

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Tender.title.like(pattern),
                Tender.summary.like(pattern),
                Tender.raw_text.like(pattern),
                Tender.buyer.like(pattern),
                Tender.category.like(pattern),
                Tender.matched_keywords.like(pattern),
            )
        )
    if province:
        stmt = stmt.where(Tender.province == province)
    if city:
        stmt = stmt.where(Tender.city == city)
    if category:
        stmt = stmt.where(Tender.category == category)
    if min_relevance_score is not None:
        stmt = stmt.where(Tender.relevance_score >= min_relevance_score)

    return list(session.scalars(stmt.limit(limit)))
