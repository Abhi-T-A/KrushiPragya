"""Scheme normalizer enforcing non-fabrication, canonical schema fields, and SHA-256 content hashing."""
from dataclasses import dataclass
import hashlib
import json
import logging
import re
from typing import Any, Dict, Optional

from app.schemes.crawler.extractor import ExtractedSchemeData

logger = logging.getLogger(__name__)


@dataclass
class NormalizedScheme:
    """Normalized, canonical government scheme data ready for database persistence."""
    title: str
    title_kn: Optional[str]
    description: str
    description_kn: Optional[str]
    department: str
    state: str
    category: str
    eligibility: str
    eligibility_kn: Optional[str]
    benefits: str
    benefits_kn: Optional[str]
    application_process: Optional[str]
    application_process_kn: Optional[str]
    documents_required: Optional[str]
    documents_required_kn: Optional[str]
    application_url: Optional[str]
    source_url: str
    source_name: str
    source_type: str
    content_hash: str
    raw_payload: Dict[str, Any]


class SchemeNormalizer:
    """Normalizes raw extraction into strictly grounded canonical schema."""

    @staticmethod
    def clean_title(title: str) -> str:
        """Strip portal prefixes and trailing breadcrumbs from titles."""
        if not title:
            return ""
        t = re.sub(r"^(Scheme Details\s*[-|:]\s*|myScheme\s*[-|:]\s*|Govt of Karnataka\s*[-|:]\s*)", "", title, flags=re.I)
        t = re.sub(r"\s*[-|:]\s*(myScheme|Official Portal|Home)$", "", t, flags=re.I)
        return t.strip()

    @staticmethod
    def compute_content_hash(
        title: str,
        department: str,
        state: str,
        category: str,
        eligibility: str,
        benefits: str,
        application_process: Optional[str],
        documents_required: Optional[str],
    ) -> str:
        """Compute deterministic SHA-256 hash of core normalized facts.
        
        Ignores dynamic timestamps, visitor counts, and navigation chrome so that
        change detection triggers strictly on actual agricultural scheme changes.
        """
        canonical_dict = {
            "title": title.strip().lower(),
            "department": (department or "").strip().lower(),
            "state": (state or "").strip().lower(),
            "category": (category or "").strip().lower(),
            "eligibility": (eligibility or "").strip(),
            "benefits": (benefits or "").strip(),
            "application_process": (application_process or "").strip(),
            "documents_required": (documents_required or "").strip(),
        }
        canonical_str = json.dumps(canonical_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def normalize(
        self,
        extracted: ExtractedSchemeData,
        source_name: str,
        source_type: str,
    ) -> NormalizedScheme:
        """Convert extracted data into NormalizedScheme with deterministic hash.
        
        CRITICAL RULE:
        Missing source fields must remain None / empty. Never fabricate or hallucinate.
        """
        title_en = self.clean_title(extracted.title_en or extracted.raw_title)
        title_kn = self.clean_title(extracted.title_kn or "") if extracted.title_kn else None

        # Fallback if only Kannada title exists
        if not title_en and title_kn:
            title_en = title_kn

        description = (extracted.description or title_en or "").strip()
        description_kn = (extracted.description_kn or "").strip() or None

        department = (extracted.department or "Department of Agriculture").strip()
        state = (extracted.state or "Karnataka").strip()
        category = (extracted.category or "Subsidy").strip()

        eligibility = (extracted.eligibility_text or "Please check official guidelines for detailed eligibility.").strip()
        eligibility_kn = (extracted.eligibility_text_kn or "").strip() or None

        benefits = (extracted.benefits_text or "Subsidies and financial assistance under official scheme guidelines.").strip()
        benefits_kn = (extracted.benefits_text_kn or "").strip() or None

        application_process = (extracted.application_process_text or "").strip() or None
        application_process_kn = (extracted.application_process_text_kn or "").strip() or None

        documents_required = (extracted.documents_required_text or "").strip() or None
        documents_required_kn = (extracted.documents_required_text_kn or "").strip() or None

        content_hash = self.compute_content_hash(
            title=title_en,
            department=department,
            state=state,
            category=category,
            eligibility=eligibility,
            benefits=benefits,
            application_process=application_process,
            documents_required=documents_required,
        )

        raw_payload = {
            "source_url": extracted.source_url,
            "raw_title": extracted.raw_title,
            "category": category,
            "department": department,
            "state": state,
            "extracted_sections": {
                "eligibility": eligibility,
                "benefits": benefits,
                "application_process": application_process,
                "documents_required": documents_required,
            },
        }

        return NormalizedScheme(
            title=title_en,
            title_kn=title_kn,
            description=description,
            description_kn=description_kn,
            department=department,
            state=state,
            category=category,
            eligibility=eligibility,
            eligibility_kn=eligibility_kn,
            benefits=benefits,
            benefits_kn=benefits_kn,
            application_process=application_process,
            application_process_kn=application_process_kn,
            documents_required=documents_required,
            documents_required_kn=documents_required_kn,
            application_url=extracted.application_url,
            source_url=extracted.source_url,
            source_name=source_name,
            source_type=source_type,
            content_hash=content_hash,
            raw_payload=raw_payload,
        )
