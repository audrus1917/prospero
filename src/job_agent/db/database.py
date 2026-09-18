"""Configure the database engine and request-scoped sessions."""

from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from job_agent.config.settings import get_settings


def build_engine(database_url: str) -> Engine:
    """Build an engine for the supplied SQLAlchemy URL."""
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


engine = build_engine(get_settings().database_url)


def get_session() -> Generator[Session, None, None]:
    """Yield a request-scoped database session."""
    with Session(engine) as session:
        yield session
