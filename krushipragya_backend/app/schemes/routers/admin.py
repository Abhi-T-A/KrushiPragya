"""Admin crawler control and monitoring endpoints."""
import logging
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_role
from app.database.connection import get_db
from app.schemes.schemas import CrawlerStatusResponse, CrawlRunResponse
from app.schemes.services.orchestrator import SchemeCrawlOrchestrator
from app.schemes.services.scheduler import get_scheme_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/schemes/crawler", tags=["Admin Scheme Crawler"])


@router.get(
    "/status",
    response_model=CrawlerStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get 5-hour crawler operational status, metrics, and last run stats",
)
def get_crawler_status(
    db: Session = Depends(get_db),
    scheduler=Depends(get_scheme_scheduler),
) -> CrawlerStatusResponse:
    """Return operational status and metrics of the automated 5-hour scheme crawler."""
    stat = scheduler.get_status(db)
    return CrawlerStatusResponse(**stat)


@router.post(
    "/run",
    response_model=CrawlRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger immediate manual crawl of official government sources",
)
async def trigger_crawler_run(
    source_id: Optional[uuid.UUID] = Query(None, description="Optional specific source ID to crawl"),
    db: Session = Depends(get_db),
) -> CrawlRunResponse:
    """Trigger an immediate crawl run on approved official sources."""
    orchestrator = SchemeCrawlOrchestrator()
    crawl_run = await orchestrator.run_full_crawl(db=db, source_id=source_id)

    return CrawlRunResponse(
        id=str(crawl_run.id),
        started_at=crawl_run.started_at.isoformat(),
        completed_at=crawl_run.completed_at.isoformat() if crawl_run.completed_at else None,
        status=crawl_run.status,
        pages_crawled=crawl_run.pages_crawled,
        schemes_found=crawl_run.schemes_found,
        schemes_created=crawl_run.schemes_created,
        schemes_updated=crawl_run.schemes_updated,
        schemes_unchanged=crawl_run.schemes_unchanged,
        schemes_failed=crawl_run.schemes_failed,
        error_message=crawl_run.error_message,
    )
