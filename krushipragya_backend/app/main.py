from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.weather import router as weather_router
from app.api.v1.disease import router as disease_router
from app.api.v1.farmer import router as farmer_router, villages_router
from app.api.v1.auth import router as auth_router
from app.api.v1.farmer_crop import router as farmer_crop_router
from app.api.v1.crop_report import router as crop_report_router
from app.api.v1.crop_report_diagnosis import router as crop_report_diagnosis_router
from app.api.v1.farmer_advisory import router as farmer_advisory_router
from app.market.routers.market_public import router as market_public_router
from app.market.routers.farmer_market import router as farmer_market_router
from app.market.routers.buyer_market import router as buyer_market_router
from app.market.routers.market_payment import router as market_payment_router
from app.schemes.routers.schemes import router as schemes_router
from app.schemes.routers.scheme_payment import router as scheme_payment_router
from app.schemes.routers.admin import router as admin_schemes_router
from app.api.v1.verification import router as verification_router
from app.core.config import settings
from app.core.logging import setup_logging

# Initialize logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting up %s (v%s) in [%s] mode...", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    # Preload and warm up all 7 disease classification models into memory
    try:
        from app.services.disease_detection_service import get_disease_detection_service
        disease_service = get_disease_detection_service()
        disease_service.preload_all_models()
    except Exception as exc:
        logger.warning("Non-fatal issue during disease model startup preloading: %s", exc)

    # Start 5-hour background SchemeScheduler
    try:
        from app.schemes.services.scheduler import scheme_scheduler
        scheme_scheduler.start()
    except Exception as exc:
        logger.warning("Non-fatal issue starting scheme scheduler: %s", exc)

    yield

    # Clean shutdown of SchemeScheduler
    try:
        from app.schemes.services.scheduler import scheme_scheduler
        scheme_scheduler.stop()
    except Exception:
        pass

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
app.include_router(disease_router, prefix="/api")
app.include_router(farmer_router, prefix="/api/v1")
app.include_router(farmer_crop_router, prefix="/api/v1")
app.include_router(crop_report_router, prefix="/api/v1")
app.include_router(crop_report_diagnosis_router, prefix="/api/v1")
app.include_router(farmer_advisory_router, prefix="/api/v1")
app.include_router(farmer_market_router, prefix="/api/v1")
app.include_router(buyer_market_router, prefix="/api/v1")
app.include_router(market_payment_router, prefix="/api/v1")
app.include_router(market_public_router, prefix="/api/v1")
app.include_router(scheme_payment_router, prefix="/api/v1")
app.include_router(schemes_router, prefix="/api/v1")
app.include_router(admin_schemes_router, prefix="/api/v1")
app.include_router(verification_router, prefix="/api/v1")
app.include_router(villages_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


