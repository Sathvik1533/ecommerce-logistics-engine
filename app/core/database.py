from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Engine configuration tailored for MySQL 8.x:
# - pool_pre_ping=True: Validates connection health prior to checkout, preventing
#   stale "MySQL server has gone away" errors.
# - pool_recycle: Recycles connections before MySQL server's wait_timeout drops them.
# - pool_size & max_overflow: Governs concurrency limits against MySQL ceiling.
engine = create_engine(
    url=settings.sync_database_url,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.x domain models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a transactional SQLAlchemy session.

    Transaction Boundary Notes:
    - Autocommit is disabled: callers must explicitly commit (`db.commit()`) or rollback.
    - If an unhandled exception occurs inside the route handler, the session rolls back
      before closing to prevent partial / corrupt transactional state.
    - Concurrency Warning: For features requiring race-condition immunity (such as
      atomic inventory reservation), callers should execute `SELECT ... FOR UPDATE`
      within the transaction boundary before updating quantities.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
