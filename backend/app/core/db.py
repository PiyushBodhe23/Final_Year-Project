"""SQLAlchemy engine and session factory for the PreventVital store."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import database_url


class Base(DeclarativeBase):
    """Declarative base for PreventVital tables."""


def _engine():
    url = database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


engine = _engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped session and always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
