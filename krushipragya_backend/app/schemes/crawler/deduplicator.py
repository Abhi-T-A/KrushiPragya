"""Deduplication service matching crawled schemes against existing database records."""
import logging
import re
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.government import GovernmentScheme
from app.schemes.crawler.normalizer import NormalizedScheme

logger = logging.getLogger(__name__)


def clean_title_tokens(title: str) -> str:
    """Normalize title for fuzzy token matching."""
    t = title.lower()
    # Strip common noise keywords
    noise = ["pradhan", "mantri", "yojana", "scheme", "karnataka", "government", "govt", "of", "the", "and"]
    for word in noise:
        t = re.sub(rf"\b{word}\b", "", t)
    # Strip punctuation and collapse whitespace
    t = re.sub(r"[^\w\s]", "", t)
    return " ".join(t.split())


class SchemeDeduplicator:
    """Finds existing scheme matching a newly crawled candidate."""

    @staticmethod
    def find_existing_scheme(
        db: Session,
        candidate: NormalizedScheme,
    ) -> Optional[GovernmentScheme]:
        """Find existing scheme by canonical source URL or normalized title + department."""
        # 1. Exact Source URL match (highest confidence)
        if candidate.source_url:
            query = select(GovernmentScheme).where(
                GovernmentScheme.source_url == candidate.source_url
            )
            existing = db.execute(query).scalar_one_or_none()
            if existing:
                return existing

        # 2. Exact Title match in same department
        query_title = select(GovernmentScheme).where(
            GovernmentScheme.title.ilike(candidate.title),
            GovernmentScheme.department == candidate.department,
        )
        existing_title = db.execute(query_title).scalars().first()
        if existing_title:
            return existing_title

        # 3. Normalized Token match
        cand_tokens = clean_title_tokens(candidate.title)
        if len(cand_tokens) > 5:
            schemes = db.execute(
                select(GovernmentScheme).where(
                    GovernmentScheme.department == candidate.department,
                    GovernmentScheme.state == candidate.state,
                )
            ).scalars().all()

            for s in schemes:
                s_tokens = clean_title_tokens(s.title)
                if s_tokens and (s_tokens == cand_tokens or cand_tokens in s_tokens or s_tokens in cand_tokens):
                    logger.debug("Deduplication matched '%s' with existing id=%s", candidate.title, s.id)
                    return s

        return None
