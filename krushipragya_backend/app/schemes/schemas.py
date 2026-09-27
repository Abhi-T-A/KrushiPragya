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


class SchemeFeeInfo(BaseModel):
    """Transparent fee structure model separating official and service fees."""
    model_config = ConfigDict(extra="ignore")

    fee_type: str = Field(
        default="UNKNOWN",
        description="FREE, OFFICIAL_FEE, SERVICE_FEE, OFFICIAL_PLUS_SERVICE_FEE, GOVERNMENT_BORNE, UNKNOWN",
    )
    payment_required: bool = Field(default=False, description="Whether online payment is required")
    official_fee: Optional[float] = Field(default=None, description="Official government fee (0 if free/borne by govt)")
    krushipragya_service_fee: Optional[float] = Field(default=None, description="KrushiPragya assistance fee")
    total_payable: Optional[float] = Field(default=None, description="Total amount payable strictly calculated on server")
    currency: str = Field(default="INR", description="Fee currency")
    fee_description: Optional[str] = Field(default=None, description="Fee description")
    fee_source: Optional[str] = Field(default=None, description="Source provenance of fee data")
    fee_last_verified: Optional[str] = Field(default=None, description="Last verified timestamp")
    is_verified: bool = Field(default=False, description="True if fee is verified from official source")
    notice_kn: str = Field(
        default="ಶುಲ್ಕಗಳನ್ನು ಪಾರದರ್ಶಕತೆಗಾಗಿ ಪ್ರತ್ಯೇಕವಾಗಿ ತೋರಿಸಲಾಗಿದೆ.",
        description="Kannada transparency disclosure",
    )
    notice_en: str = Field(
        default="Fees are displayed separately for transparency.",
        description="English transparency disclosure",
    )


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
    fee_info: Optional[SchemeFeeInfo] = None
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
    fee_info: Optional[SchemeFeeInfo] = None
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


# ==============================================================================
# Scheme Application & Payment Schemas
# ==============================================================================

class SchemeApplicationCreateRequest(BaseModel):
    """Request to create or initiate an application for a scheme."""
    model_config = ConfigDict(extra="ignore")

    application_notes: Optional[str] = Field(None, description="Optional notes or references from farmer")


class SchemeApplicationResponse(BaseModel):
    """Farmer scheme application details with workflow and payment status."""
    model_config = ConfigDict(extra="ignore")

    id: str
    scheme_id: str
    scheme_title: str
    scheme_title_kn: Optional[str] = None
    category: str
    farmer_id: str
    status: str = Field(..., description="DRAFT, READY_FOR_SUBMISSION, PAYMENT_PENDING, PAID, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED")
    payment_status: str = Field(..., description="NOT_REQUIRED, PENDING, PROOF_SUBMITTED, PENDING_VERIFICATION, PAID, FAILED, CANCELLED")
    fee_info: SchemeFeeInfo
    payment_transaction_id: Optional[str] = None
    application_notes: Optional[str] = None
    review_notes: Optional[str] = None
    can_submit: bool = Field(default=False, description="True if free or verified paid, ready for submission")
    submitted_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SchemePaymentInitiateResponse(BaseModel):
    """Payment order, PayU checkout payload, and PhonePe static QR fallback for scheme application."""
    model_config = ConfigDict(extra="ignore")

    transaction_id: str
    application_id: str
    scheme_id: str
    scheme_title: str
    scheme_title_kn: Optional[str] = None
    payment_method: str = "PHONEPE_STATIC_QR"
    provider: Optional[str] = "payu"
    gateway_order_id: Optional[str] = None
    checkout_data: Optional[Dict[str, Any]] = None
    payment_status: str
    official_fee: float
    service_fee: float
    total_amount: float
    currency: str = "INR"
    qr_data: Optional[Dict[str, Any]] = None
    fee_summary: Dict[str, Any]
    message_kn: str
    message_en: str


class PaymentProofSubmitRequest(BaseModel):
    """Farmer submission of bank UTR / reference number after PhonePe payment."""
    model_config = ConfigDict(extra="ignore")

    utr: str = Field(..., min_length=8, max_length=30, description="Bank UTR / UPI reference number")
    amount_paid: float = Field(..., description="Amount paid by the farmer, must match backend amount")
    notes: Optional[str] = None


class PaymentProofSubmitResponse(BaseModel):
    """Response returned upon submitting UTR for verification."""
    model_config = ConfigDict(extra="ignore")

    transaction_id: str
    application_id: str
    payment_reference: str
    payment_status: str
    application_status: str
    amount: float
    message_kn: str
    message_en: str


class PaymentVerifyRequest(BaseModel):
    """Authorized officer or admin verification request for submitted UTR."""
    model_config = ConfigDict(extra="ignore")

    action: str = Field(..., pattern="^(APPROVE|REJECT)$", description="'APPROVE' or 'REJECT'")
    notes: Optional[str] = None


class PaymentReceiptResponse(BaseModel):
    """Audited formal receipt for paid scheme applications."""
    model_config = ConfigDict(extra="ignore")

    receipt_id: str
    app_name: str = "KrushiPragya"
    scheme_name: str
    scheme_title_kn: Optional[str] = None
    application_id: str
    transaction_id: str
    farmer_id: str
    farmer_name: Optional[str] = None
    official_fee: float
    krushipragya_service_fee: float
    total_paid: float
    currency: str = "INR"
    payment_method: str = "PHONEPE_STATIC_QR"
    payment_reference: str
    payment_status: str
    paid_at: Optional[str] = None
    verified_at: Optional[str] = None
    transparency_notice_kn: str = "ಶುಲ್ಕಗಳನ್ನು ಪಾರದರ್ಶಕತೆಗಾಗಿ ಪ್ರತ್ಯೇಕವಾಗಿ ತೋರಿಸಲಾಗಿದೆ."
    transparency_notice_en: str = "Fees are displayed separately for transparency."

