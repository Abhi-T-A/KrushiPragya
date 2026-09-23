import logging
from typing import Optional
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db, init_db_engine, SessionLocal
from app.schemas.health import HealthResponse, DatabaseHealthResponse

logger = logging.getLogger(settings.APP_NAME)

router = APIRouter(prefix="/health", tags=["Health"])


def get_health_check_db() -> Optional[Session]:
    """Dependency for health check that handles unconfigured or unreachable DB gracefully."""
    if not settings.is_database_configured:
        return None
    try:
        global SessionLocal
        if SessionLocal is None:
            init_db_engine()
        if SessionLocal is None:
            return None
        db = SessionLocal()
        return db
    except Exception as exc:
        logger.warning("Could not establish database session: %s", type(exc).__name__)
        return None


@router.get(
    "",
    response_model=HealthResponse,
    summary="Application Health Check",
    description="Returns the operational status, service name, and version of KrushiPragya.",
    status_code=status.HTTP_200_OK,
)
def get_health() -> HealthResponse:
    """Return application operational status."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
    )


@router.get(
    "/database",
    response_model=DatabaseHealthResponse,
    summary="Database Connectivity Health Check",
    description="Validates database connectivity using a lightweight query (SELECT 1).",
    responses={
        200: {
            "model": DatabaseHealthResponse,
            "description": "Database is connected and healthy",
        },
        503: {
            "model": DatabaseHealthResponse,
            "description": "Database is disconnected or unconfigured",
        },
    },
)
def get_database_health() -> JSONResponse:
    """Check database connectivity with a lightweight SELECT 1 query."""
    if not settings.is_database_configured:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected"},
        )

    db: Optional[Session] = get_health_check_db()
    if db is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected"},
        )

    try:
        db.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "healthy", "database": "connected"},
        )
    except Exception as exc:
        logger.error("Database ping failed: %s", type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected"},
        )
    finally:
        db.close()
