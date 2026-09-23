from typing import Generator, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None


def normalize_database_url(url: str) -> str:
    """Ensure PostgreSQL URLs use the postgresql:// driver prefix."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def init_db_engine() -> Optional[Engine]:
    """Initialize SQLAlchemy engine and session factory if DATABASE_URL is configured."""
    global engine, SessionLocal
    if not settings.is_database_configured:
        return None

    normalized_url = normalize_database_url(settings.DATABASE_URL)
    engine = create_engine(normalized_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


# Initial attempt to create engine at import time
init_db_engine()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    global SessionLocal
    if SessionLocal is None:
        init_db_engine()

    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured. Please set DATABASE_URL in your environment or .env file.")

    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
