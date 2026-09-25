"""Source registry service managing allowlisted official government sources."""
import json
import logging
from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.government import SchemeSource

logger = logging.getLogger(__name__)

# Default official government sources
DEFAULT_OFFICIAL_SOURCES = [
    {
        "name": "myScheme Portal (Central & State Scheme Discovery)",
        "base_url": "https://www.myscheme.gov.in",
        "domain_allowlist": ["myscheme.gov.in", "*.myscheme.gov.in", "search.myscheme.gov.in"],
        "source_type": "MYSCHEME",
        "crawl_priority": 2,
        "enabled": True,
    },
    {
        "name": "PM-KISAN Official Portal (Dept of Agriculture & Farmers Welfare)",
        "base_url": "https://pmkisan.gov.in",
        "domain_allowlist": ["pmkisan.gov.in", "*.pmkisan.gov.in"],
        "source_type": "CENTRAL_PORTAL",
        "crawl_priority": 1,
        "enabled": True,
    },
    {
        "name": "Karnataka Agriculture Department (Raitha Mitra)",
        "base_url": "https://raitamitra.karnataka.gov.in",
        "domain_allowlist": ["raitamitra.karnataka.gov.in", "agri.karnataka.gov.in", "*.karnataka.gov.in"],
        "source_type": "STATE_DEPT",
        "crawl_priority": 1,
        "enabled": True,
    },
]


class SchemeSourceRegistry:
    """Registry maintaining approved government scheme domains and seeds."""

    @staticmethod
    def ensure_default_sources(db: Session) -> List[SchemeSource]:
        """Ensure the approved official sources are seeded in database."""
        existing_sources = db.execute(select(SchemeSource)).scalars().all()
        existing_urls = {s.base_url for s in existing_sources}

        created = []
        for def_src in DEFAULT_OFFICIAL_SOURCES:
            if def_src["base_url"] not in existing_urls:
                src = SchemeSource(
                    id=uuid.uuid4(),
                    name=def_src["name"],
                    base_url=def_src["base_url"],
                    domain_allowlist=json.dumps(def_src["domain_allowlist"]),
                    source_type=def_src["source_type"],
                    crawl_priority=def_src["crawl_priority"],
                    enabled=def_src["enabled"],
                )
                db.add(src)
                created.append(src)

        if created:
            db.commit()
            for c in created:
                db.refresh(c)
            logger.info("Seeded %d default official scheme sources", len(created))

        return db.execute(select(SchemeSource).order_by(SchemeSource.crawl_priority)).scalars().all()

    @staticmethod
    def get_enabled_sources(db: Session) -> List[SchemeSource]:
        """Return all active, enabled sources."""
        return db.execute(
            select(SchemeSource).where(SchemeSource.enabled == True).order_by(SchemeSource.crawl_priority)
        ).scalars().all()

    @staticmethod
    def get_allowed_domains_for_source(source: SchemeSource) -> List[str]:
        """Parse JSON domain allowlist for a source."""
        try:
            domains = json.loads(source.domain_allowlist)
            if isinstance(domains, list):
                return domains
        except Exception:
            pass
        return [source.base_url]
