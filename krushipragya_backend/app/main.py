from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.weather import router as weather_router
from app.api.v1.disease import router as disease_router
from app.api.v1.farmer import router as farmer_router
from app.api.v1.farmer_crop import router as farmer_crop_router
from app.api.v1.crop_report import router as crop_report_router
from app.api.v1.crop_report_diagnosis import router as crop_report_diagnosis_router
from app.core.config import settings
from app.core.logging import setup_logging

# Initialize logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting up %s (v%s) in [%s] mode...", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    # Perform any startup verification or connection pool warming here if needed
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="KrushiPragya - AI-Powered Agriculture Platform Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all global exception handler returning structured JSON."""
    logger.error("Unhandled exception processing %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An internal server error occurred.",
            "path": request.url.path,
        },
    )


# Register API v1 Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(weather_router, prefix="/api/v1")
app.include_router(disease_router, prefix="/api/v1")
app.include_router(farmer_router, prefix="/api/v1")
app.include_router(farmer_crop_router, prefix="/api/v1")
app.include_router(crop_report_router, prefix="/api/v1")
app.include_router(crop_report_diagnosis_router, prefix="/api/v1")


