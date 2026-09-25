"""Pydantic schemas for Government Schemes Intelligence Service."""
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class SchemeSourceInfo(BaseModel):
    """Provenance information for official government source."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Official issuing source or portal name")
    url: Optional[str] = Field(None, description="Official webpage URL")
    last_verified_at: Optional[str] = Field(None, description="ISO timestamp of last verified crawl")
    source_type: Optional[str] = Field(None, description="MYSCHEME, CENTRAL_PORTAL, STATE_DEPT")
    crawler_status: Optional[str] = Field(default="VERIFIED", description="VERIFIED, UPDATED, or SOURCE_TEMPORARILY_UNAVAILABLE")


class RelatedSchemeItem(BaseModel):
    """Brief summary of a related scheme."""
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    category: str
    department: Optional[str] = None


class SchemeListItemResponse(BaseModel):
    """Schema for item in scheme list view matching reference screen."""
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str = Field(..., description="Display title (Kannada-first when language is kn)")
    title_en: str
    title_kn: Optional[str] = None
    description: str
    department: str
    state: str
    category: str
    benefits_summary: str
    application_url: Optional[str] = None
    is_read: bool = Field(default=False, description="Whether the current authenticated farmer has read this scheme")
    is_saved: bool = Field(default=False, description="Whether the farmer has bookmarked/saved this scheme")
    source: SchemeSourceInfo
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SchemeListResponse(BaseModel):
    """Paginated response containing list of government schemes."""
    model_config = ConfigDict(extra="ignore")

    items: List[SchemeListItemResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class SchemeDetailResponse(BaseModel):
    """Full detail response schema matching reference scheme detail screen."""
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    title_en: str
    title_kn: Optional[str] = None
    description: str
    department: str
    state: str
    category: str
    status: str
    eligibility: List[str]
    benefits: List[str]
    application_process: List[str]
    documents_required: List[str]
    application_url: Optional[str] = None
    is_read: bool = False
    is_saved: bool = False
    source: SchemeSourceInfo
    related_schemes: List[RelatedSchemeItem] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CrawlerStatusResponse(BaseModel):
    """Status response for the 5-hour automated crawler."""
    model_config = ConfigDict(extra="ignore")

    enabled: bool
    interval_hours: int
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    status: str
    schemes_found: int
    schemes_created: int
    schemes_updated: int
    schemes_unchanged: int
    failed: int


class CrawlRunResponse(BaseModel):
    """Response returned upon triggering a crawl execution."""
    model_config = ConfigDict(extra="ignore")

    id: str
    started_at: str
    completed_at: Optional[str] = None
    status: str
    pages_crawled: int
    schemes_found: int
    schemes_created: int
    schemes_updated: int
    schemes_unchanged: int
    schemes_failed: int
    error_message: Optional[str] = None


class UserActionResponse(BaseModel):
    """Response returned for read/save actions."""
    model_config = ConfigDict(extra="ignore")

    success: bool
    message: str
