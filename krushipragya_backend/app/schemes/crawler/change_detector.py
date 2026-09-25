"""Change detector comparing normalized scheme hashes and extracting field diffs."""
from dataclasses import dataclass
import logging
from typing import Any, Dict

from app.models.government import GovernmentScheme
from app.schemes.crawler.normalizer import NormalizedScheme

logger = logging.getLogger(__name__)


@dataclass
class ChangeDetectionResult:
    """Outcome of comparing existing scheme against crawled candidate."""
    is_changed: bool
    status: str  # "UNCHANGED", "UPDATED", "NEW"
    diff: Dict[str, Any]


class SchemeChangeDetector:
    """Detects whether official scheme content has meaningfully changed."""

    @staticmethod
    def detect_changes(
        existing: GovernmentScheme,
        candidate: NormalizedScheme,
    ) -> ChangeDetectionResult:
        """Compare content hashes and identify changed fields."""
        if not existing.content_hash:
            # Existing scheme had no hash computed yet; consider changed to establish baseline
            return ChangeDetectionResult(is_changed=True, status="UPDATED", diff={"content_hash": "baseline_established"})

        if existing.content_hash == candidate.content_hash:
            return ChangeDetectionResult(is_changed=False, status="UNCHANGED", diff={})

        diff = {}
        if existing.title != candidate.title:
            diff["title"] = {"old": existing.title, "new": candidate.title}
        if existing.benefits != candidate.benefits:
            diff["benefits"] = {"old": existing.benefits[:100], "new": candidate.benefits[:100]}
        if existing.eligibility != candidate.eligibility:
            diff["eligibility"] = {"old": existing.eligibility[:100], "new": candidate.eligibility[:100]}
        if existing.application_url != candidate.application_url:
            diff["application_url"] = {"old": existing.application_url, "new": candidate.application_url}

        logger.info(
            "Scheme '%s' (id=%s) content changed. Hash: %s -> %s",
            existing.title, existing.id, existing.content_hash[:8], candidate.content_hash[:8],
        )

        return ChangeDetectionResult(
            is_changed=True,
            status="UPDATED",
            diff=diff,
        )
