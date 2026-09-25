"""Pydantic schemas for Verification Ladder, Community Corroboration, and Expert Verification."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.crop_report import CropReportDiagnosisRecordResponse, CropReportResponse


class VerificationStatus(str, Enum):
    """Trust Ladder verification statuses."""

    UNVERIFIED = "UNVERIFIED"
    AI_ANALYSED = "AI_ANALYSED"
    CORROBORATED = "CORROBORATED"
    EXPERT_VERIFIED = "EXPERT_VERIFIED"


STATUS_RANKS: Dict[str, int] = {
    VerificationStatus.UNVERIFIED.value: 0,
    VerificationStatus.AI_ANALYSED.value: 1,
    VerificationStatus.CORROBORATED.value: 2,
    VerificationStatus.EXPERT_VERIFIED.value: 3,
}


class ObservationType(str, Enum):
    """Observation types for community corroboration."""

    SAME_SYMPTOMS = "SAME_SYMPTOMS"
    SEEN_NEARBY = "SEEN_NEARBY"
    NOT_MATCHING = "NOT_MATCHING"
    AGREE = "AGREE"
    DISAGREE = "DISAGREE"


AGREE_OBSERVATION_TYPES = {
    ObservationType.SAME_SYMPTOMS.value,
    ObservationType.SEEN_NEARBY.value,
    ObservationType.AGREE.value,
    "CONFIRM",
}

DISAGREE_OBSERVATION_TYPES = {
    ObservationType.NOT_MATCHING.value,
    ObservationType.DISAGREE.value,
    "DIFFERENT_SYMPTOMS",
}


class ExpertDecisionAction(str, Enum):
    """Allowed expert decision actions."""

    APPROVE = "APPROVE"
    CONFIRM = "CONFIRM"
    CORRECT = "CORRECT"
    REJECT = "REJECT"
    REQUEST_REVIEW = "REQUEST_REVIEW"
    NEED_MORE_INFO = "NEED_MORE_INFO"


class ExpertRequestStatus(str, Enum):
    """Status lifecycle for expert verification requests."""

    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_REVIEW = "IN_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    NEED_MORE_INFO = "NEED_MORE_INFO"


# ==============================================================================
# Community Corroboration Schemas
# ==============================================================================


class CorroborationCreate(BaseModel):
    """Schema for submitting a community corroboration."""

    observation_type: Optional[str] = Field(
        default=None,
        description="Observation type: SAME_SYMPTOMS, SEEN_NEARBY, NOT_MATCHING, AGREE, DISAGREE",
    )
    agreed: Optional[bool] = Field(
        default=None,
        description="Whether user agrees with the AI diagnosis (True/False). If provided, sets default observation_type",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional observation note or comment",
    )
    village_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional village context ID",
    )


class CorroborationResponse(BaseModel):
    """Schema representing an individual community corroboration."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    crop_report_id: uuid.UUID
    community_member_id: uuid.UUID
    observation_type: str
    is_agreed: bool
    notes: Optional[str] = None
    village_id: Optional[str] = None
    created_at: datetime


class CorroborationSummary(BaseModel):
    """Aggregated corroboration statistics for a crop report."""

    total_count: int = Field(default=0, description="Total corroborations submitted")
    agreed_count: int = Field(default=0, description="Count of corroborations confirming diagnosis")
    disagreed_count: int = Field(default=0, description="Count of corroborations disagreeing")
    min_required: int = Field(default=2, description="Configured minimum agreeing count required")
    threshold_satisfied: bool = Field(
        default=False,
        description="Whether corroboration threshold criteria (agree >= min and agree > disagree) is met",
    )
    is_corroborated: bool = Field(
        default=False,
        description="Whether report has reached or passed CORROBORATED stage",
    )


class CorroborationSubmissionResponse(BaseModel):
    """Response returned upon successful corroboration submission."""

    corroboration: CorroborationResponse
    corroboration_summary: CorroborationSummary
    report_status: str


class CorroborationListResponse(BaseModel):
    """List of corroborations with summary stats for a report."""

    crop_report_id: uuid.UUID
    corroboration_summary: CorroborationSummary
    corroborations: List[CorroborationResponse]


# ==============================================================================
# Eligible Crop Reports for Corroboration
# ==============================================================================


class EligibleReportDiagnosisSummary(BaseModel):
    """Top-1 AI diagnosis summary for crop report listings."""

    crop: str
    predicted_class: str
    confidence: float
    model_name: Optional[str] = None
    created_at: datetime


class EligibleCropReportResponse(BaseModel):
    """Summary of a crop report eligible for community corroboration."""

    report_id: uuid.UUID
    farmer_crop_id: uuid.UUID
    crop_name: str
    crop_code: str
    notes: Optional[str] = None
    image_storage_path: Optional[str] = None
    image_filename: Optional[str] = None
    status: str
    created_at: datetime
    latest_diagnosis: Optional[EligibleReportDiagnosisSummary] = None
    corroboration_summary: CorroborationSummary


class EligibleReportsListResponse(BaseModel):
    """List of crop reports eligible for community review."""

    items: List[EligibleCropReportResponse]
    total: int


# ==============================================================================
# Expert Verification Schemas
# ==============================================================================


class VerificationRequestCreate(BaseModel):
    """Schema to create an expert verification request."""

    expert_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional assigned Agriculture Expert UUID",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional notes from requesting farmer",
    )


class ExpertVerificationRequestResponse(BaseModel):
    """Schema representing an expert verification request."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    crop_report_id: uuid.UUID
    farmer_id: uuid.UUID
    expert_id: Optional[uuid.UUID] = None
    status: str
    action_type: Optional[str] = None
    finding: Optional[str] = None
    expert_notes: Optional[str] = None
    recommended_action: Optional[str] = None
    requested_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExpertDecisionCreate(BaseModel):
    """Schema for expert review decision submission."""

    decision: str = Field(
        ...,
        description="Decision: APPROVE, CONFIRM, CORRECT, REJECT, REQUEST_REVIEW, NEED_MORE_INFO",
    )
    finding: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Confirmed or corrected condition/disease label",
    )
    expert_notes: Optional[str] = Field(
        default=None,
        description="Expert clinical observations or explanation",
    )
    recommended_action: Optional[str] = Field(
        default=None,
        description="Treatment, remedy, or action advice for the farmer",
    )


class ExpertDecisionResponse(BaseModel):
    """Response returned upon submitting an expert verification decision."""

    verification_request: ExpertVerificationRequestResponse
    new_report_status: str
    ladder_advanced: bool


class ExpertQueueItem(BaseModel):
    """Item in the Agriculture Expert verification queue."""

    id: uuid.UUID
    crop_report_id: uuid.UUID
    farmer_id: uuid.UUID
    expert_id: Optional[uuid.UUID] = None
    status: str
    crop_code: str
    crop_name: str
    farmer_notes: Optional[str] = None
    image_storage_path: Optional[str] = None
    image_filename: Optional[str] = None
    latest_diagnosis: Optional[EligibleReportDiagnosisSummary] = None
    corroboration_summary: CorroborationSummary
    requested_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExpertQueueListResponse(BaseModel):
    """Paginated list of expert verification queue items."""

    items: List[ExpertQueueItem]
    total: int


class ExpertVerificationDetailResponse(BaseModel):
    """Comprehensive detail view for an expert reviewing a verification request."""

    request: ExpertVerificationRequestResponse
    report: CropReportResponse
    crop_code: str
    crop_name: str
    farmer_id: uuid.UUID
    farmer_name: Optional[str] = None
    image_storage_path: Optional[str] = None
    diagnoses: List[CropReportDiagnosisRecordResponse] = []
    corroborations: List[CorroborationResponse] = []
    corroboration_summary: CorroborationSummary


# ==============================================================================
# Full Trust Ladder Status & Audit History
# ==============================================================================


class StatusHistoryEntry(BaseModel):
    """Audit entry documenting a stage transition on the trust ladder."""

    status: str
    rank: int
    timestamp: datetime
    actor_role: str
    description: str


class VerificationStatusResponse(BaseModel):
    """Complete frontend-friendly trust ladder verification payload."""

    crop_report_id: uuid.UUID
    verification_status: str
    status_rank: int
    is_ai_analysed: bool
    is_corroborated: bool
    is_expert_verified: bool
    latest_diagnosis: Optional[EligibleReportDiagnosisSummary] = None
    corroboration_summary: CorroborationSummary
    expert_verification: Optional[ExpertVerificationRequestResponse] = None
    status_history: List[StatusHistoryEntry] = []
    created_at: datetime
    updated_at: datetime
