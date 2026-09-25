"""API endpoints for Verification Ladder, Community Corroboration, and Agriculture Expert Verification."""
import logging
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import (
    AuthenticatedUser,
    get_current_user,
    require_expert,
    require_role,
    verify_farmer_access,
)
from app.database.connection import get_db
from app.schemas.verification import (
    CorroborationCreate,
    CorroborationListResponse,
    CorroborationSubmissionResponse,
    EligibleReportsListResponse,
    ExpertDecisionCreate,
    ExpertDecisionResponse,
    ExpertQueueListResponse,
    ExpertVerificationDetailResponse,
    ExpertVerificationRequestResponse,
    VerificationRequestCreate,
    VerificationStatusResponse,
)
from app.services.verification_service import (
    DuplicateCorroborationError,
    DuplicateVerificationRequestError,
    InvalidExpertDecisionError,
    InvalidObservationTypeError,
    ReportIneligibleError,
    ReportNotFoundError,
    RequestAlreadyFinalizedError,
    RequestNotFoundError,
    SelfCorroborationError,
    UnauthorizedAccessError,
    UnauthorizedExpertError,
    VerificationService,
    get_verification_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Verification & Community Corroboration"])

# Role dependencies
require_community_or_farmer = require_role("COMMUNITY_MEMBER", "FARMER")
require_farmer_or_admin = require_role("FARMER", "ADMIN")


# ==============================================================================
# 1. Community Corroboration Endpoints
# ==============================================================================


@router.post(
    "/crop-reports/{report_id}/corroborations",
    response_model=CorroborationSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit community corroboration",
    description=(
        "Submits a peer observation agreeing or disagreeing with the AI diagnosis on an eligible crop report. "
        "Advances status from AI_ANALYSED to CORROBORATED once consensus threshold is met."
    ),
)
def submit_corroboration(
    report_id: uuid.UUID,
    payload: CorroborationCreate,
    auth_user: AuthenticatedUser = Depends(require_community_or_farmer),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> CorroborationSubmissionResponse:
    """Submit community corroboration for an eligible crop report."""
    try:
        return service.submit_corroboration(
            db=db,
            report_id=report_id,
            user=auth_user,
            payload=payload,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ReportIneligibleError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except SelfCorroborationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except DuplicateCorroborationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except InvalidObservationTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/crop-reports/{report_id}/corroborations",
    response_model=CorroborationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List corroborations for report",
    description="Returns all community corroborations and aggregated agreement metrics for a crop report.",
)
def list_corroborations(
    report_id: uuid.UUID,
    auth_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> CorroborationListResponse:
    """List all corroborations for a crop report."""
    try:
        return service.list_corroborations(
            db=db,
            report_id=report_id,
            user=auth_user,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/community/eligible-crop-reports",
    response_model=EligibleReportsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List crop reports eligible for community corroboration",
    description=(
        "Returns reports currently at AI_ANALYSED or CORROBORATED status, excluding the caller's own reports."
    ),
)
@router.get(
    "/crop-reports/eligible-for-corroboration",
    response_model=EligibleReportsListResponse,
    include_in_schema=False,
)
def list_eligible_reports(
    village_id: Optional[str] = Query(default=None, description="Optional village context filter"),
    crop_code: Optional[str] = Query(default=None, description="Optional crop catalog code filter"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    auth_user: AuthenticatedUser = Depends(require_community_or_farmer),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> EligibleReportsListResponse:
    """List crop reports ready for community review."""
    return service.list_eligible_reports(
        db=db,
        user=auth_user,
        village_id=village_id,
        crop_code=crop_code,
        limit=limit,
        offset=offset,
    )


# ==============================================================================
# 2. Expert Verification Request Endpoints
# ==============================================================================


@router.post(
    "/crop-reports/{report_id}/verification-request",
    response_model=ExpertVerificationRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request Agriculture Expert verification",
    description=(
        "Creates a verification request routed to agriculture experts. "
        "Caller must be the report owner or an administrator."
    ),
)
def create_verification_request(
    report_id: uuid.UUID,
    payload: VerificationRequestCreate = VerificationRequestCreate(),
    auth_user: AuthenticatedUser = Depends(require_farmer_or_admin),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> ExpertVerificationRequestResponse:
    """Request expert verification for a diagnosed crop report."""
    try:
        return service.create_verification_request(
            db=db,
            report_id=report_id,
            user=auth_user,
            payload=payload,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UnauthorizedAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ReportIneligibleError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except DuplicateVerificationRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/farmers/{farmer_id}/crop-reports/{report_id}/verification-request",
    response_model=ExpertVerificationRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request expert verification (Farmer scoped route)",
    description="Farmer-scoped route alias for creating an expert verification request.",
)
def create_farmer_verification_request(
    farmer_id: uuid.UUID,
    report_id: uuid.UUID,
    payload: VerificationRequestCreate = VerificationRequestCreate(),
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> ExpertVerificationRequestResponse:
    """Farmer-scoped route to request expert verification."""
    try:
        return service.create_verification_request(
            db=db,
            report_id=report_id,
            user=auth_user,
            payload=payload,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UnauthorizedAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ReportIneligibleError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except DuplicateVerificationRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/crop-reports/{report_id}/verification-request",
    response_model=ExpertVerificationRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get verification request for report",
    description="Retrieves the latest expert verification request associated with the crop report.",
)
def get_verification_request(
    report_id: uuid.UUID,
    auth_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> ExpertVerificationRequestResponse:
    """Retrieve expert verification request for a report."""
    try:
        return service.get_verification_request_for_report(
            db=db,
            report_id=report_id,
            user=auth_user,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UnauthorizedAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


# ==============================================================================
# 3. Expert Verification Queue & Review Endpoints
# ==============================================================================


@router.get(
    "/expert/verifications",
    response_model=ExpertQueueListResponse,
    status_code=status.HTTP_200_OK,
    summary="List expert verification queue",
    description="Returns incoming verification requests for Agriculture Experts with clinical summaries.",
)
@router.get(
    "/expert/queue",
    response_model=ExpertQueueListResponse,
    include_in_schema=False,
)
def list_expert_queue(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (e.g. PENDING, ASSIGNED)"),
    crop_code: Optional[str] = Query(default=None, description="Filter by crop catalog code"),
    assigned_to_me: bool = Query(default=False, description="Filter to requests assigned to caller"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    auth_user: AuthenticatedUser = Depends(require_expert),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> ExpertQueueListResponse:
    """List verification queue for agriculture experts."""
    return service.list_expert_queue(
        db=db,
        user=auth_user,
        status=status_filter,
        crop_code=crop_code,
        assigned_to_me=assigned_to_me,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/expert/verifications/{request_id}",
    response_model=ExpertVerificationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get expert verification request detail",
    description=(
        "Retrieves detailed review package for an expert: report image, full AI diagnosis, "
        "and community corroboration evidence."
    ),
)
def get_expert_verification_detail(
    request_id: uuid.UUID,
    auth_user: AuthenticatedUser = Depends(require_expert),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> ExpertVerificationDetailResponse:
    """Get full clinical detail for an expert verification request."""
    try:
        return service.get_expert_request_detail(
            db=db,
            request_id=request_id,
            user=auth_user,
        )
    except RequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/expert/verifications/{request_id}/assign",
    response_model=ExpertVerificationRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign or claim verification request",
    description="Assigns or claims an expert verification request for the authenticated expert.",
)
def assign_verification_request(
    request_id: uuid.UUID,
    expert_id: Optional[uuid.UUID] = Query(default=None, description="Optional target expert UUID (ADMIN only)"),
    auth_user: AuthenticatedUser = Depends(require_expert),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> ExpertVerificationRequestResponse:
    """Claim or assign verification request."""
    try:
        return service.assign_verification_request(
            db=db,
            request_id=request_id,
            user=auth_user,
            target_expert_id=expert_id,
        )
    except RequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RequestAlreadyFinalizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except UnauthorizedAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post(
    "/expert/verifications/{request_id}/decision",
    response_model=ExpertDecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit expert clinical decision",
    description=(
        "Submits an expert verification decision (APPROVE, REJECT, REQUEST_REVIEW). "
        "Approving advances the crop report to EXPERT_VERIFIED."
    ),
)
def submit_expert_decision(
    request_id: uuid.UUID,
    payload: ExpertDecisionCreate,
    auth_user: AuthenticatedUser = Depends(require_expert),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> ExpertDecisionResponse:
    """Submit expert verification decision."""
    try:
        return service.submit_expert_decision(
            db=db,
            request_id=request_id,
            user=auth_user,
            payload=payload,
        )
    except RequestNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RequestAlreadyFinalizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except UnauthorizedExpertError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InvalidExpertDecisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ==============================================================================
# 4. Trust Ladder Verification Status & History Endpoint
# ==============================================================================


@router.get(
    "/crop-reports/{report_id}/verification-status",
    response_model=VerificationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get complete trust ladder status and history",
    description=(
        "Returns the complete verification ladder status, AI diagnosis, corroboration metrics, "
        "expert findings, and auditable stage transition history."
    ),
)
def get_verification_status(
    report_id: uuid.UUID,
    auth_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: VerificationService = Depends(get_verification_service),
) -> VerificationStatusResponse:
    """Retrieve full trust ladder status and audit history."""
    try:
        return service.get_verification_status(
            db=db,
            report_id=report_id,
            user=auth_user,
        )
    except ReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UnauthorizedAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
