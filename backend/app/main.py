from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.database.connection import engine


app = FastAPI(
    title=settings.APP_NAME,
    description="Village-first AI Farm Intelligence Platform for Coastal & Malnad Karnataka",
    version=settings.APP_VERSION,
)


@app.get("/")
def root():
    return {
        "message": "KadalaMale API is running 🌱",
        "status": "healthy",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "kadalamale-backend",
    }


@app.get("/db-health")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "connection_failed",
            "error": str(e),
        }