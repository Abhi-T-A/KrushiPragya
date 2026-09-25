"""Crawl orchestrator executing the 5-hour automated scheme ingestion pipeline."""
from datetime import datetime, timezone
import json
import logging
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.government import (
    GovernmentScheme,
    SchemeCrawlRun,
    SchemeSource,
    SchemeSourceDocument,
)
from app.schemes.crawler.change_detector import SchemeChangeDetector
from app.schemes.crawler.deduplicator import SchemeDeduplicator
from app.schemes.crawler.extractor import SchemeExtractor
from app.schemes.crawler.fetcher import SchemeFetcher
from app.schemes.crawler.normalizer import SchemeNormalizer
from app.schemes.crawler.security import is_safe_url
from app.schemes.services.source_registry import SchemeSourceRegistry

logger = logging.getLogger(__name__)


class SchemeCrawlOrchestrator:
    """Orchestrates crawling of approved official sources, extraction, deduplication, and storage."""

    def __init__(
        self,
        fetcher: Optional[SchemeFetcher] = None,
        extractor: Optional[SchemeExtractor] = None,
        normalizer: Optional[SchemeNormalizer] = None,
        deduplicator: Optional[SchemeDeduplicator] = None,
        change_detector: Optional[SchemeChangeDetector] = None,
    ):
        self.fetcher = fetcher or SchemeFetcher()
        self.extractor = extractor or SchemeExtractor()
        self.normalizer = normalizer or SchemeNormalizer()
        self.deduplicator = deduplicator or SchemeDeduplicator()
        self.change_detector = change_detector or SchemeChangeDetector()

    async def crawl_source(
        self,
        db: Session,
        source: SchemeSource,
        crawl_run: SchemeCrawlRun,
        max_pages: int = settings.SCHEME_MAX_PAGES_PER_SOURCE,
    ) -> None:
        """Crawl an individual approved source up to max_pages."""
        allowed_domains = SchemeSourceRegistry.get_allowed_domains_for_source(source)
        visited_urls = set()
        queue = [source.base_url]
        crawl_run.pages_discovered += 1

        logger.info("Starting crawl for source '%s' at %s", source.name, source.base_url)

        while queue and len(visited_urls) < max_pages:
            url = queue.pop(0)
            if url in visited_urls:
                continue
            visited_urls.add(url)

            # Fetch page safely
            fetch_res = await self.fetcher.fetch(url, allowed_domains)
            crawl_run.pages_crawled += 1

            if not fetch_res.is_success:
                logger.warning("Failed to fetch %s from %s: %s", url, source.name, fetch_res.error)
                crawl_run.schemes_failed += 1
                if not crawl_run.error_message:
                    crawl_run.error_message = f"Error fetching {url}: {fetch_res.error}"
                continue

            # Extract structured sections
            extracted = self.extractor.extract(fetch_res.content, url)

            # Enqueue newly discovered safe links from this source
            for link in extracted.discovered_links:
                if link not in visited_urls and link not in queue and len(queue) + len(visited_urls) < max_pages:
                    safe_link, _ = is_safe_url(link, allowed_domains)
                    if safe_link:
                        queue.append(link)
                        crawl_run.pages_discovered += 1

            # Check if this page contains sufficient content to be a scheme
            if not extracted.raw_title or len(extracted.raw_title) < 4:
                continue

            crawl_run.schemes_found += 1

            # Normalize data
            normalized = self.normalizer.normalize(
                extracted=extracted,
                source_name=source.name,
                source_type=source.source_type,
            )

            # Deduplicate against existing records
            existing = self.deduplicator.find_existing_scheme(db, normalized)
            now = datetime.now(timezone.utc)
            target_scheme: Optional[GovernmentScheme] = None

            if existing:
                # Change detection
                change_res = self.change_detector.detect_changes(existing, normalized)
                if change_res.is_changed:
                    # Update existing scheme
                    existing.title = normalized.title
                    if normalized.title_kn:
                        existing.title_kn = normalized.title_kn
                    existing.description = normalized.description
                    if normalized.description_kn:
                        existing.description_kn = normalized.description_kn
                    existing.department = normalized.department
                    existing.state = normalized.state
                    existing.category = normalized.category
                    existing.eligibility = normalized.eligibility
                    if normalized.eligibility_kn:
                        existing.eligibility_kn = normalized.eligibility_kn
                    existing.benefits = normalized.benefits
                    if normalized.benefits_kn:
                        existing.benefits_kn = normalized.benefits_kn
                    if normalized.application_process:
                        existing.application_process = normalized.application_process
                    if normalized.application_process_kn:
                        existing.application_process_kn = normalized.application_process_kn
                    if normalized.documents_required:
                        existing.documents_required = normalized.documents_required
                    if normalized.documents_required_kn:
                        existing.documents_required_kn = normalized.documents_required_kn
                    if normalized.application_url:
                        existing.application_url = normalized.application_url
                    existing.content_hash = normalized.content_hash
                    existing.last_crawled_at = now
                    existing.last_verified_at = now
                    existing.source_last_seen_at = now
                    existing.crawler_status = "UPDATED"
                    crawl_run.schemes_updated += 1
                else:
                    # Unchanged scheme
                    existing.last_crawled_at = now
                    existing.last_verified_at = now
                    existing.source_last_seen_at = now
                    existing.crawler_status = "VERIFIED"
                    crawl_run.schemes_unchanged += 1
                target_scheme = existing
            else:
                # Create brand new scheme
                new_scheme = GovernmentScheme(
                    id=uuid.uuid4(),
                    title=normalized.title,
                    title_kn=normalized.title_kn,
                    description=normalized.description,
                    description_kn=normalized.description_kn,
                    department=normalized.department,
                    state=normalized.state,
                    category=normalized.category,
                    eligibility=normalized.eligibility,
                    eligibility_kn=normalized.eligibility_kn,
                    benefits=normalized.benefits,
                    benefits_kn=normalized.benefits_kn,
                    application_process=normalized.application_process,
                    application_process_kn=normalized.application_process_kn,
                    documents_required=normalized.documents_required,
                    documents_required_kn=normalized.documents_required_kn,
                    application_url=normalized.application_url,
                    source_url=normalized.source_url,
                    source_name=normalized.source_name,
                    source_type=normalized.source_type,
                    source_last_seen_at=now,
                    content_hash=normalized.content_hash,
                    last_crawled_at=now,
                    last_verified_at=now,
                    crawler_status="VERIFIED",
                    status="ACTIVE",
                )
                db.add(new_scheme)
                crawl_run.schemes_created += 1
                target_scheme = new_scheme

            db.flush()

            # Record provenance document (without heavy raw HTML)
            source_doc = SchemeSourceDocument(
                id=uuid.uuid4(),
                scheme_id=target_scheme.id if target_scheme else None,
                source_id=source.id,
                source_url=url,
                content_hash=normalized.content_hash,
                raw_title=extracted.raw_title[:500],
                extracted_content=json.dumps(normalized.raw_payload, ensure_ascii=False),
                http_status=fetch_res.status_code,
                fetched_at=now,
                parser_version="1.0.0",
            )
            db.add(source_doc)

        db.commit()
        logger.info(
            "Completed source '%s': crawled=%d, found=%d, created=%d, updated=%d, unchanged=%d",
            source.name, crawl_run.pages_crawled, crawl_run.schemes_found,
            crawl_run.schemes_created, crawl_run.schemes_updated, crawl_run.schemes_unchanged,
        )

    async def run_full_crawl(
        self,
        db: Session,
        source_id: Optional[uuid.UUID] = None,
    ) -> SchemeCrawlRun:
        """Execute complete crawl across all enabled sources or a specific source."""
        # Ensure default sources are present
        SchemeSourceRegistry.ensure_default_sources(db)

        # Create master crawl run record
        crawl_run = SchemeCrawlRun(
            id=uuid.uuid4(),
            source_id=source_id,
            started_at=datetime.now(timezone.utc),
            status="RUNNING",
        )
        db.add(crawl_run)
        db.commit()
        db.refresh(crawl_run)

        try:
            if source_id:
                sources = [db.get(SchemeSource, source_id)]
                sources = [s for s in sources if s is not None and s.enabled]
            else:
                sources = SchemeSourceRegistry.get_enabled_sources(db)

            for src in sources:
                try:
                    await self.crawl_source(db, src, crawl_run)
                except Exception as src_exc:
                    logger.error("Exception during crawl of source %s: %s", src.name, src_exc, exc_info=True)
                    crawl_run.schemes_failed += 1
                    crawl_run.error_message = str(src_exc)

            crawl_run.completed_at = datetime.now(timezone.utc)
            if crawl_run.schemes_failed > 0 and crawl_run.schemes_found == 0:
                crawl_run.status = "FAILED"
            elif crawl_run.schemes_failed > 0:
                crawl_run.status = "PARTIAL"
            else:
                crawl_run.status = "SUCCESS"

        except Exception as exc:
            logger.error("Fatal crawl run exception: %s", exc, exc_info=True)
            crawl_run.completed_at = datetime.now(timezone.utc)
            crawl_run.status = "FAILED"
            crawl_run.error_message = str(exc)

        db.commit()
        db.refresh(crawl_run)
        return crawl_run
