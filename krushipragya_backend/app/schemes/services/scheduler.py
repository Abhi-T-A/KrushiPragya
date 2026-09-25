"""Fixed 5-hour background scheduler for Government Schemes Intelligence Service."""
import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import SessionLocal
from app.models.government import SchemeCrawlRun
from app.schemes.services.orchestrator import SchemeCrawlOrchestrator

logger = logging.getLogger(__name__)


class SchemeScheduler:
    """Asynchronous background scheduler running scheme crawls every 5 hours."""

    def __init__(
        self,
        interval_hours: int = settings.SCHEME_CRAWL_INTERVAL_HOURS,
        enabled: bool = settings.SCHEME_CRAWLER_ENABLED,
    ):
        self.interval_hours = interval_hours
        self.enabled = enabled
        self._task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
        self.orchestrator = SchemeCrawlOrchestrator()

    def calculate_next_run(self, from_time: Optional[datetime] = None) -> datetime:
        """Calculate next scheduled run time based on fixed 5-hour interval."""
        base = from_time or datetime.now(timezone.utc)
        return base + timedelta(hours=self.interval_hours)

    async def _scheduler_loop(self) -> None:
        """Background loop executing crawls every 5 hours."""
        logger.info("SchemeScheduler background worker started (interval: %d hours)", self.interval_hours)
        self._next_run = self.calculate_next_run()

        while self._is_running and self.enabled:
            try:
                # Sleep in short increments to allow graceful shutdown
                now = datetime.now(timezone.utc)
                if self._next_run and now >= self._next_run:
                    logger.info("SchemeScheduler triggering scheduled 5-hour crawl run...")
                    self._last_run = now
                    self._next_run = self.calculate_next_run(now)

                    # Execute crawl inside isolated database session
                    db: Session = SessionLocal()
                    try:
                        await self.orchestrator.run_full_crawl(db)
                    finally:
                        db.close()

                await asyncio.sleep(10)  # Check tick every 10 seconds
            except asyncio.CancelledError:
                logger.info("SchemeScheduler loop received cancellation signal.")
                break
            except Exception as exc:
                logger.error("Unexpected error in SchemeScheduler loop: %s", exc, exc_info=True)
                await asyncio.sleep(60)

    def start(self) -> None:
        """Start the background scheduler task."""
        if not self.enabled:
            logger.info("SchemeScheduler is disabled by configuration (SCHEME_CRAWLER_ENABLED=False)")
            return

        if self._is_running:
            return

        self._is_running = True
        self._next_run = self.calculate_next_run()
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("SchemeScheduler started. First scheduled execution at %s", self._next_run.isoformat())

    def stop(self) -> None:
        """Stop background scheduler task cleanly."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("SchemeScheduler stopped.")

    def get_status(self, db: Session) -> Dict[str, Any]:
        """Return operational crawler and scheduler status."""
        last_run_record = db.execute(
            select(SchemeCrawlRun).order_by(desc(SchemeCrawlRun.started_at)).limit(1)
        ).scalar_one_or_none()

        status_str = "IDLE"
        schemes_found = 0
        schemes_created = 0
        schemes_updated = 0
        schemes_unchanged = 0
        failed = 0
        last_run_time = None

        if last_run_record:
            status_str = last_run_record.status
            schemes_found = last_run_record.schemes_found
            schemes_created = last_run_record.schemes_created
            schemes_updated = last_run_record.schemes_updated
            schemes_unchanged = last_run_record.schemes_unchanged
            failed = last_run_record.schemes_failed
            last_run_time = last_run_record.started_at.isoformat()

        return {
            "enabled": self.enabled,
            "interval_hours": self.interval_hours,
            "last_run": last_run_time or (self._last_run.isoformat() if self._last_run else None),
            "next_run": self._next_run.isoformat() if self._next_run else None,
            "status": status_str,
            "schemes_found": schemes_found,
            "schemes_created": schemes_created,
            "schemes_updated": schemes_updated,
            "schemes_unchanged": schemes_unchanged,
            "failed": failed,
        }


# Global singleton instance
scheme_scheduler = SchemeScheduler()


def get_scheme_scheduler() -> SchemeScheduler:
    """Dependency provider for SchemeScheduler."""
    return scheme_scheduler
