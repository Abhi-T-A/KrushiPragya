"""Deterministic HTML content extractor for Government Scheme portals.

Strips boilerplates, extracts core semantic sections (Overview, Eligibility,
Benefits, Application Steps, Required Documents) in English and Kannada,
and extracts official portal application links.
"""
from dataclasses import dataclass, field
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.schemes.crawler.security import sanitize_text

logger = logging.getLogger(__name__)

# Section matching patterns (English & Kannada)
SECTION_KEYWORDS = {
    "eligibility": [
        "eligibility", "who can apply", "criteria", "eligible", "beneficiary",
        "ಅರ್ಹತೆ", "ಅರ್ಹತೆಗಳು", "ಫಲಾನುಭವಿ", "ಮಾನದಂಡ",
    ],
    "benefits": [
        "benefit", "benefits", "assistance", "subsidy", "incentive", "coverage", "grant",
        "ಪ್ರಯೋಜನ", "ಪ್ರಯೋಜನಗಳು", "ಸಹಾಯಧನ", "ಆರ್ಥಿಕ ನೆರವು",
    ],
    "application_process": [
        "application process", "how to apply", "process", "procedure", "steps to apply",
        "ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ವಿಧಾನ", "ಅರ್ಜಿ ಸಲ್ಲಿಕೆ", "ವಿಧಾನ", "ನೋಂದಣಿ",
    ],
    "documents_required": [
        "documents required", "document", "documents", "mandatory documents", "checklist",
        "ದಾಖಲೆಗಳು", "ಅಗತ್ಯ ದಾಖಲೆಗಳು", "ಬೇಕಾಗುವ ದಾಖಲೆಗಳು",
    ],
    "department": [
        "department", "ministry", "issuing authority", "nodal agency",
        "ಇಲಾಖೆ", "ಸಚಿವಾಲಯ",
    ],
}


@dataclass
class ExtractedSchemeData:
    """Raw structured data extracted deterministically from a scheme page."""
    source_url: str
    raw_title: str
    title_en: Optional[str] = None
    title_kn: Optional[str] = None
    description: Optional[str] = None
    description_kn: Optional[str] = None
    department: Optional[str] = None
    state: Optional[str] = "Karnataka"
    category: Optional[str] = "Subsidy"
    eligibility_text: Optional[str] = None
    eligibility_text_kn: Optional[str] = None
    benefits_text: Optional[str] = None
    benefits_text_kn: Optional[str] = None
    application_process_text: Optional[str] = None
    application_process_text_kn: Optional[str] = None
    documents_required_text: Optional[str] = None
    documents_required_text_kn: Optional[str] = None
    application_url: Optional[str] = None
    discovered_links: List[str] = field(default_factory=list)
    has_kannada_content: bool = False


class SchemeExtractor:
    """Parser extracting official agricultural scheme details from HTML."""

    @staticmethod
    def is_kannada(text: str) -> bool:
        """Check if a string contains Kannada Unicode characters."""
        if not text:
            return False
        return bool(re.search(r"[\u0C80-\u0CFF]", text))

    def extract(self, html_content: str, base_url: str) -> ExtractedSchemeData:
        """Extract structured scheme sections and outbound links from raw HTML."""
        if not html_content or not html_content.strip():
            return ExtractedSchemeData(source_url=base_url, raw_title="")

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Collect outbound links for crawler discovery before pruning
        discovered_links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
                full_link = urljoin(base_url, href)
                discovered_links.append(full_link)

        # 2. Extract official application link before stripping interactive elements
        application_url = None
        for a_tag in soup.find_all("a", href=True):
            text_link = a_tag.get_text().strip().lower()
            href = a_tag["href"].strip()
            if any(k in text_link for k in ["apply online", "apply here", "portal", "registration", "ಅರ್ಜಿ ಸಲ್ಲಿಸಿ", "ಲಾಗಿನ್"]):
                candidate = urljoin(base_url, href)
                parsed = urlparse(candidate)
                if parsed.scheme in ("http", "https"):
                    application_url = candidate
                    break

        # 3. Strip non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "button"]):
            tag.decompose()

        # 4. Extract Title
        title_tag = soup.find("h1") or soup.find("h2") or soup.find("title")
        raw_title = sanitize_text(title_tag.get_text()) if title_tag else ""
        if not raw_title:
            meta_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "title"})
            if meta_title and meta_title.get("content"):
                raw_title = sanitize_text(meta_title["content"])

        # Detect language of title
        title_en = None
        title_kn = None
        if self.is_kannada(raw_title):
            title_kn = raw_title
        else:
            title_en = raw_title

        # Check for secondary bilingual title in h2/subheading
        subheadings = soup.find_all(["h2", "h3", "p"], class_=re.compile(r"subtitle|subheading|kannada|title", re.I))
        for sh in subheadings:
            sh_text = sanitize_text(sh.get_text())
            if self.is_kannada(sh_text) and not title_kn:
                title_kn = sh_text
            elif not self.is_kannada(sh_text) and not title_en and len(sh_text) > 5:
                title_en = sh_text

        # 5. Extract Structured Sections
        sections: Dict[str, List[str]] = {
            "eligibility": [],
            "benefits": [],
            "application_process": [],
            "documents_required": [],
            "department": [],
            "overview": [],
        }

        # Scan heading-driven content blocks
        current_section = "overview"
        elements = soup.find_all(["h2", "h3", "h4", "p", "ul", "ol", "div"])

        for elem in elements:
            text = sanitize_text(elem.get_text())
            if not text or len(text) < 3:
                continue

            # Check if this element represents a section header
            if elem.name in ("h2", "h3", "h4") or (elem.name == "p" and len(text) < 60 and (":" in text or text.isupper())):
                low_text = text.lower()
                matched = False
                for sec_name, keywords in SECTION_KEYWORDS.items():
                    if any(kw in low_text for kw in keywords):
                        current_section = sec_name
                        matched = True
                        break
                if matched:
                    continue

            # Collect content under current section
            if elem.name in ("p", "ul", "ol", "div"):
                # Avoid collecting parent containers if children were already processed
                if elem.name == "div" and elem.find(["p", "ul", "ol"]):
                    continue
                if text not in sections[current_section]:
                    sections[current_section].append(text)

        # 6. Aggregate and assign language-specific outputs
        def join_sec(sec_key: str) -> str:
            items = sections.get(sec_key, [])
            return "\n".join(items).strip()

        overview_text = join_sec("overview")
        elig_text = join_sec("eligibility")
        ben_text = join_sec("benefits")
        proc_text = join_sec("application_process")
        doc_text = join_sec("documents_required")
        dept_text = join_sec("department")

        desc_en = overview_text if not self.is_kannada(overview_text) else None
        desc_kn = overview_text if self.is_kannada(overview_text) else None

        elig_en = elig_text if not self.is_kannada(elig_text) else None
        elig_kn = elig_text if self.is_kannada(elig_text) else None

        ben_en = ben_text if not self.is_kannada(ben_text) else None
        ben_kn = ben_text if self.is_kannada(ben_text) else None

        proc_en = proc_text if not self.is_kannada(proc_text) else None
        proc_kn = proc_text if self.is_kannada(proc_text) else None

        doc_en = doc_text if not self.is_kannada(doc_text) else None
        doc_kn = doc_text if self.is_kannada(doc_text) else None

        # Clean Department
        dept_clean = None
        if dept_text:
            # Extract first line or concise department string
            first_dept = dept_text.split("\n")[0].strip()
            if len(first_dept) < 150:
                dept_clean = first_dept

        # Classify scheme category based on text
        full_page_text = f"{raw_title} {overview_text} {ben_text}".lower()
        category = "Subsidy"
        if "insurance" in full_page_text or "ವಿಮೆ" in full_page_text:
            category = "Insurance"
        elif "equipment" in full_page_text or "machinery" in full_page_text or "ಯಂತ್ರ" in full_page_text:
            category = "Equipment"
        elif "irrigation" in full_page_text or "drip" in full_page_text or "ನೀರಾವರಿ" in full_page_text:
            category = "Irrigation"
        elif "loan" in full_page_text or "credit" in full_page_text or "ಸಾಲ" in full_page_text:
            category = "Loan / Credit"
        elif "pension" in full_page_text or "relief" in full_page_text or "ಪರಿಹಾರ" in full_page_text:
            category = "Relief / Pension"

        has_kn = any([
            self.is_kannada(raw_title),
            self.is_kannada(overview_text),
            self.is_kannada(ben_text),
            self.is_kannada(elig_text),
        ])

        return ExtractedSchemeData(
            source_url=base_url,
            raw_title=raw_title,
            title_en=title_en or raw_title,
            title_kn=title_kn,
            description=desc_en or overview_text or raw_title,
            description_kn=desc_kn,
            department=dept_clean or "Department of Agriculture",
            state="Karnataka",
            category=category,
            eligibility_text=elig_en or elig_text,
            eligibility_text_kn=elig_kn,
            benefits_text=ben_en or ben_text,
            benefits_text_kn=ben_kn,
            application_process_text=proc_en or proc_text,
            application_process_text_kn=proc_kn,
            documents_required_text=doc_en or doc_text,
            documents_required_text_kn=doc_kn,
            application_url=application_url,
            discovered_links=list(set(discovered_links)),
            has_kannada_content=has_kn,
        )
