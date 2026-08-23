# ---------------------------------------------------------------------------
# SQLAlchemy engine/session setup.
#
# `Base` is imported by every model in app/models/*; Alembic's env.py points
# its autogenerate target at Base.metadata, so a new model only needs to be
# imported somewhere Alembic loads to be picked up (see alembic/env.py).
# ---------------------------------------------------------------------------

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a request-scoped DB session, always closed after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
