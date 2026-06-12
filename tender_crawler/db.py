from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from tender_crawler.models import Base
from tender_crawler.settings import get_settings


def _ensure_sqlite_parent(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    raw_path = database_url.replace("sqlite:///", "", 1)
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)


def get_engine():
    settings = get_settings()
    _ensure_sqlite_parent(settings.database_url)
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, connect_args=connect_args)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    if engine.dialect.name != "sqlite":
        return

    required_columns = {
        "business_profile": "VARCHAR(120)",
        "matched_keywords": "TEXT",
        "relevance_score": "INTEGER DEFAULT 0 NOT NULL",
    }
    inspector = inspect(engine)
    if "tenders" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("tenders")}
    with engine.begin() as connection:
        for name, ddl_type in required_columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE tenders ADD COLUMN {name} {ddl_type}"))


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "init":
        init_db()
        print("Database initialized.")
        return
    print("Usage: python -m tender_crawler.db init")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
