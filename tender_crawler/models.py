from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Tender(Base):
    __tablename__ = "tenders"
    __table_args__ = (
        UniqueConstraint("source", "source_url", name="uq_tender_source_url"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    province: Mapped[Optional[str]] = mapped_column(String(80), index=True)
    city: Mapped[Optional[str]] = mapped_column(String(80), index=True)
    buyer: Mapped[Optional[str]] = mapped_column(String(200))
    agency: Mapped[Optional[str]] = mapped_column(String(200))
    budget: Mapped[Optional[str]] = mapped_column(String(120))
    publish_date: Mapped[Optional[str]] = mapped_column(String(40), index=True)
    deadline: Mapped[Optional[str]] = mapped_column(String(40), index=True)
    category: Mapped[Optional[str]] = mapped_column(String(120), index=True)
    business_profile: Mapped[Optional[str]] = mapped_column(String(120), index=True)
    matched_keywords: Mapped[Optional[str]] = mapped_column(Text)
    relevance_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
