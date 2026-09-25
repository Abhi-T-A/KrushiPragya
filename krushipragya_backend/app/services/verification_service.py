"""Service implementing Trust Ladder, Community Corroboration, and Expert Verification workflows."""
from datetime import datetime, timezone
import logging
from typing import List, Optional
import uuid

from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.core.auth import AuthenticatedUser
from app.core.config import settings
from app.models.crop import Crop
from app.models.crop_report import CropReport
from app.models.crop_report_diagnosis import CropReportDiagnosis
from app.models.expert_verification import CommunityCorroboration, ExpertVerificationRequest
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.schemas.crop_report import CropReportDiagnosisRecordResponse, CropReportResponse
from app.schemas.verification import (
    AGREE_OBSERVATION_TYPES,
    DISAGREE_OBSERVATION_TYPES,
    STATUS_RANKS,
    CorroborationCreate,
    CorroborationListResponse,
    CorroborationResponse,
    CorroborationSubmissionResponse,
    CorroborationSummary,
    EligibleCropReportResponse,
    EligibleReportDiagnosisSummary,
    EligibleReportsListResponse,
    ExpertDecisionCreate,
    ExpertDecisionResponse,
    ExpertQueueItem,
    ExpertQueueListResponse,
    ExpertVerificationDetailResponse,
    ExpertVerificationRequestResponse,
    StatusHistoryEntry,
    VerificationRequestCreate,
    VerificationStatus,
    VerificationStatusResponse,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================


class VerificationError(Exception):
    """Base exception for verification domain errors."""


class ReportNotFoundError(VerificationError):
    """Raised when the specified CropReport does not exist."""


class ReportIneligibleError(VerificationError):
    """Raised when a CropReport does not meet prerequisites (e.g. no AI diagnosis)."""


class SelfCorroborationError(VerificationError):
    """Raised when a farmer attempts to corroborate their own crop report."""


class DuplicateCorroborationError(VerificationError):
    """Raised when a user attempts to corroborate the same report multiple times."""


class InvalidObservationTypeError(VerificationError):
    """Raised when an observation type is not recognized."""


class DuplicateVerificationRequestError(VerificationError):
    """Raised when an active expert verification request already exists for a report."""


class RequestNotFoundError(VerificationError):
    """Raised when an expert verification request is not found."""


class RequestAlreadyFinalizedError(VerificationError):
    """Raised when attempting to modify a finalized verification request."""


class UnauthorizedExpertError(VerificationError):
    """Raised when an expert attempts an action on a request assigned to another expert."""


class InvalidExpertDecisionError(VerificationError):
    """Raised when an invalid expert decision action is supplied."""


class UnauthorizedAccessError(VerificationError):
    """Raised when a user lacks ownership or role permissions for an operation."""


# ==============================================================================
# Core Helper Functions
# ==============================================================================


def is_agreeing_observation(observation_type: str) -> bool:
    """Check if an observation type represents confirmation/agreement."""
    return observation_type.strip().upper() in AGREE_OBSERVATION_TYPES


def is_disagreeing_observation(observation_type: str) -> bool:
    """Check if an observation type represents disagreement."""
    return observation_type.strip().upper() in DISAGREE_OBSERVATION_TYPES


def calculate_corroboration_summary(
    corroborations: List[CommunityCorroboration],
    current_status: str,
    min_required: Optional[int] = None,
) -> CorroborationSummary:
    """Compute corroboration summary counts, threshold status, and stage advancement."""
    if min_required is None:
        min_required = settings.MIN_CORROBORATIONS_FOR_VERIFICATION

    agreed = sum(1 for c in corroborations if is_agreeing_observation(c.observation_type))
    disagreed = sum(1 for c in corroborations if is_disagreeing_observation(c.observation_type))
    total = len(corroborations)

    threshold_satisfied = (agreed >= min_required) and (agreed > disagreed)
    is_corroborated = (
        STATUS_RANKS.get(current_status, 0) >= STATUS_RANKS[VerificationStatus.CORROBORATED.value]
    )

    return CorroborationSummary(
        total_count=total,
        agreed_count=agreed,
        disagreed_count=disagreed,
        min_required=min_required,
        threshold_satisfied=threshold_satisfied,
        is_corroborated=is_corroborated,
    )


def transition_crop_report_status(
    db: Session,
    report: CropReport,
    target_status: str,
) -> bool:
    """Transition crop report to a new verification status enforcing ladder rank invariants.

    Invariants:
    1. Status ranks: UNVERIFIED (0) < AI_ANALYSED (1) < CORROBORATED (2) < EXPERT_VERIFIED (3).
    2. Lower stage can NEVER overwrite a higher stage.
    3. Status transitions are deterministic and auditable.
    """
    curr_rank = STATUS_RANKS.get(report.status, 0)
    target_rank = STATUS_RANKS.get(target_status, 0)

    if target_rank <= curr_rank:
        logger.info(
            "Report %s status remains '%s' (target '%s' rank %d <= current rank %d)",
            report.id,
            report.status,
            target_status,
            target_rank,
            curr_rank,
        )
        return False

    old_status = report.status
    report.status = target_status
    report.updated_at = datetime.now(timezone.utc)
    db.add(report)
    logger.info(
        "Report %s transitioned verification ladder: %s -> %s (rank %d -> %d)",
        report.id,
        old_status,
        target_status,
        curr_rank,
        target_rank,
    )
    return True


# ==============================================================================
# Verification Ladder Service Implementation
# ==============================================================================


class VerificationService:
    """Service managing Trust Ladder transitions, Community Corroborations, and Expert Reviews."""

    # --------------------------------------------------------------------------
    # 1. Community Corroboration
    # --------------------------------------------------------------------------

    def submit_corroboration(
        self,
        db: Session,
        report_id: uuid.UUID,
        user: AuthenticatedUser,
        payload: CorroborationCreate,
    ) -> CorroborationSubmissionResponse:
        """Submit a community corroboration for an eligible crop report.

        Validations:
        - Report exists (404)
        - Report has an AI diagnosis (422)
        - Report owner cannot corroborate own report (403)
        - User cannot submit duplicate corroborations (409)
        - Observation type is recognized (422)

        Status Advancement:
        - If agreeing corroborations satisfy the threshold rule (>= min and > disagreed),
          advances report status from AI_ANALYSED -> CORROBORATED.
        """
        # 1. Fetch CropReport with relations
        report = (
            db.query(CropReport)
            .options(
                selectinload(CropReport.farmer_crop),
                selectinload(CropReport.diagnoses),
            )
            .filter(CropReport.id == report_id)
            .first()
        )
        if report is None:
            logger.warning("CropReport %s not found for corroboration", report_id)
            raise ReportNotFoundError(f"Crop report with ID '{report_id}' not found.")

        # 2. Check report eligibility (must have at least one AI diagnosis)
        if not report.diagnoses and report.status == VerificationStatus.UNVERIFIED.value:
            logger.warning("CropReport %s is UNVERIFIED; cannot corroborate", report_id)
            raise ReportIneligibleError(
                "Crop report must be diagnosed by AI before community corroboration."
            )

        # 3. Prevent self-corroboration by report owner
        owner_id = report.farmer_crop.farmer_id if report.farmer_crop else None
        if owner_id == user.id:
            logger.warning("Farmer %s attempted to corroborate own report %s", user.id, report_id)
            raise SelfCorroborationError("Report owners cannot corroborate their own crop reports.")

        # 4. Check for duplicate corroboration
        existing = (
            db.query(CommunityCorroboration)
            .filter(
                CommunityCorroboration.crop_report_id == report_id,
                CommunityCorroboration.community_member_id == user.id,
            )
            .first()
        )
        if existing is not None:
            logger.warning("User %s already corroborated report %s", user.id, report_id)
            raise DuplicateCorroborationError(
                "You have already submitted a corroboration for this crop report."
            )

        # 5. Resolve observation type and agreement boolean
        obs_type = payload.observation_type
        if obs_type:
            obs_type = obs_type.strip().upper()
        elif payload.agreed is not None:
            obs_type = "SAME_SYMPTOMS" if payload.agreed else "NOT_MATCHING"
        else:
            obs_type = "SAME_SYMPTOMS"

        valid_types = AGREE_OBSERVATION_TYPES | DISAGREE_OBSERVATION_TYPES
        if obs_type not in valid_types:
            raise InvalidObservationTypeError(
                f"Invalid observation_type '{obs_type}'. Allowed types: "
                f"{', '.join(sorted(valid_types))}"
            )

        is_agreed = obs_type in AGREE_OBSERVATION_TYPES

        # 6. Instantiate and persist CommunityCorroboration
        corroboration = CommunityCorroboration(
            id=uuid.uuid4(),
            crop_report_id=report.id,
            community_member_id=user.id,
            observation_type=obs_type,
            notes=payload.notes,
            village_id=payload.village_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(corroboration)
        db.flush()

        # 7. Evaluate corroboration rule including the new corroboration
        all_corroborations = (
            db.query(CommunityCorroboration)
            .filter(CommunityCorroboration.crop_report_id == report.id)
            .all()
        )
        summary = calculate_corroboration_summary(
            all_corroborations,
            report.status,
            min_required=settings.MIN_CORROBORATIONS_FOR_VERIFICATION,
        )

        # Advance AI_ANALYSED -> CORROBORATED if threshold met
        if summary.threshold_satisfied and report.status == VerificationStatus.AI_ANALYSED.value:
            transition_crop_report_status(db, report, VerificationStatus.CORROBORATED.value)
            summary.is_corroborated = True

        db.commit()
        db.refresh(corroboration)
        db.refresh(report)

        return CorroborationSubmissionResponse(
            corroboration=CorroborationResponse(
                id=corroboration.id,
                crop_report_id=corroboration.crop_report_id,
                community_member_id=corroboration.community_member_id,
                observation_type=corroboration.observation_type,
                is_agreed=is_agreed,
                notes=corroboration.notes,
                village_id=corroboration.village_id,
                created_at=corroboration.created_at,
            ),
            corroboration_summary=summary,
            report_status=report.status,
        )

    def list_corroborations(
        self,
        db: Session,
        report_id: uuid.UUID,
        user: AuthenticatedUser,
    ) -> CorroborationListResponse:
        """List all community corroborations and summary stats for a crop report."""
        report = db.get(CropReport, report_id)
        if report is None:
            raise ReportNotFoundError(f"Crop report with ID '{report_id}' not found.")

        corroborations = (
            db.query(CommunityCorroboration)
            .filter(CommunityCorroboration.crop_report_id == report_id)
            .order_by(desc(CommunityCorroboration.created_at))
            .all()
        )

        summary = calculate_corroboration_summary(corroborations, report.status)

        items = [
            CorroborationResponse(
                id=c.id,
                crop_report_id=c.crop_report_id,
                community_member_id=c.community_member_id,
                observation_type=c.observation_type,
                is_agreed=is_agreeing_observation(c.observation_type),
                notes=c.notes,
                village_id=c.village_id,
                created_at=c.created_at,
            )
            for c in corroborations
        ]

        return CorroborationListResponse(
            crop_report_id=report_id,
            corroboration_summary=summary,
            corroborations=items,
        )

    def list_eligible_reports(
        self,
        db: Session,
        user: AuthenticatedUser,
        village_id: Optional[str] = None,
        crop_code: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> EligibleReportsListResponse:
        """List crop reports ready for community review (AI_ANALYSED or CORROBORATED).

        Excludes reports submitted by the caller to prevent self-corroboration bias.
        """
        query = (
            db.query(CropReport)
            .options(
                selectinload(CropReport.farmer_crop).selectinload(FarmerCrop.crop),
                selectinload(CropReport.diagnoses),
            )
            .join(FarmerCrop, CropReport.farmer_crop_id == FarmerCrop.id)
            .filter(
                CropReport.status.in_([
                    VerificationStatus.AI_ANALYSED.value,
                    VerificationStatus.CORROBORATED.value,
                ]),
            )
        )

        # Exclude caller's own reports unless ADMIN
        if "ADMIN" not in user.roles:
            query = query.filter(FarmerCrop.farmer_id != user.id)

        if crop_code:
            query = query.join(Crop, FarmerCrop.crop_id == Crop.id).filter(Crop.code == crop_code.lower())

        total = query.count()
        reports = query.order_by(desc(CropReport.created_at)).offset(offset).limit(limit).all()

        items: List[EligibleCropReportResponse] = []
        for r in reports:
            crop_obj = r.farmer_crop.crop if r.farmer_crop else None
            c_name = getattr(crop_obj, "name_en", getattr(crop_obj, "name", "Unknown")) if crop_obj else "Unknown"
            c_code = getattr(crop_obj, "code", "unknown") if crop_obj else "unknown"

            latest_diag = r.diagnoses[0] if r.diagnoses else None
            diag_summary = None
            if latest_diag:
                diag_summary = EligibleReportDiagnosisSummary(
                    crop=latest_diag.crop,
                    predicted_class=latest_diag.predicted_class,
                    confidence=latest_diag.confidence,
                    model_name=latest_diag.model_name,
                    created_at=latest_diag.created_at,
                )

            corroborations = (
                db.query(CommunityCorroboration)
                .filter(CommunityCorroboration.crop_report_id == r.id)
                .all()
            )
            summary = calculate_corroboration_summary(corroborations, r.status)

            items.append(
                EligibleCropReportResponse(
                    report_id=r.id,
                    farmer_crop_id=r.farmer_crop_id,
                    crop_name=c_name,
                    crop_code=c_code,
                    notes=r.notes,
                    image_storage_path=r.image_storage_path,
                    image_filename=r.image_filename,
                    status=r.status,
                    created_at=r.created_at,
                    latest_diagnosis=diag_summary,
                    corroboration_summary=summary,
                )
            )

        return EligibleReportsListResponse(items=items, total=total)

    # --------------------------------------------------------------------------
    # 2. Expert Verification Requests
    # --------------------------------------------------------------------------

    def create_verification_request(
        self,
        db: Session,
        report_id: uuid.UUID,
        user: AuthenticatedUser,
        payload: VerificationRequestCreate,
    ) -> ExpertVerificationRequestResponse:
        """Create an expert verification request for an eligible crop report.

        Validations:
        - Report exists (404)
        - Report is diagnosed (422)
        - Caller is report owner or ADMIN (403)
        - No active verification request already exists (409)
        """
        report = (
            db.query(CropReport)
            .options(
                selectinload(CropReport.farmer_crop),
                selectinload(CropReport.diagnoses),
            )
            .filter(CropReport.id == report_id)
            .first()
        )
        if report is None:
            raise ReportNotFoundError(f"Crop report with ID '{report_id}' not found.")

        # Ownership validation
        owner_id = report.farmer_crop.farmer_id if report.farmer_crop else None
        if owner_id != user.id and "ADMIN" not in user.roles:
            logger.warning("User %s unauthorized to request verification for %s", user.id, report_id)
            raise UnauthorizedAccessError(
                "Only the farmer who owns this report or an administrator can request expert verification."
            )

        # Eligibility: must be diagnosed
        if not report.diagnoses and report.status == VerificationStatus.UNVERIFIED.value:
            raise ReportIneligibleError(
                "Crop report must be diagnosed by AI before requesting expert verification."
            )

        # Prevent duplicate active request
        active_request = (
            db.query(ExpertVerificationRequest)
            .filter(
                ExpertVerificationRequest.crop_report_id == report_id,
                ExpertVerificationRequest.status.in_(["PENDING", "ASSIGNED", "IN_REVIEW"]),
            )
            .first()
        )
        if active_request is not None:
            logger.warning("Active verification request already exists for report %s", report_id)
            raise DuplicateVerificationRequestError(
                "An active expert verification request already exists for this crop report."
            )

        # Route/assign if specified
        assigned_status = "ASSIGNED" if payload.expert_id else "PENDING"
        assigned_at = datetime.now(timezone.utc) if payload.expert_id else None

        req = ExpertVerificationRequest(
            id=uuid.uuid4(),
            crop_report_id=report.id,
            farmer_id=owner_id or user.id,
            expert_id=payload.expert_id,
            status=assigned_status,
            expert_notes=payload.notes,
            requested_at=datetime.now(timezone.utc),
            assigned_at=assigned_at,
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        logger.info(
            "Created expert verification request %s for report %s (status=%s, expert=%s)",
            req.id,
            report.id,
            req.status,
            req.expert_id,
        )
        return ExpertVerificationRequestResponse.model_validate(req)

    def get_verification_request_for_report(
        self,
        db: Session,
        report_id: uuid.UUID,
        user: AuthenticatedUser,
    ) -> ExpertVerificationRequestResponse:
        """Retrieve the latest expert verification request for a report with ownership enforcement."""
        report = (
            db.query(CropReport)
            .options(selectinload(CropReport.farmer_crop))
            .filter(CropReport.id == report_id)
            .first()
        )
        if report is None:
            raise ReportNotFoundError(f"Crop report with ID '{report_id}' not found.")

        owner_id = report.farmer_crop.farmer_id if report.farmer_crop else None
        if (
            owner_id != user.id
            and "ADMIN" not in user.roles
            and "AGRICULTURE_EXPERT" not in user.roles
        ):
            raise UnauthorizedAccessError("Access forbidden: You cannot view verification requests for this report.")

        req = (
            db.query(ExpertVerificationRequest)
            .filter(ExpertVerificationRequest.crop_report_id == report_id)
            .order_by(desc(ExpertVerificationRequest.requested_at))
            .first()
        )
        if req is None:
            raise RequestNotFoundError(f"No verification request found for crop report '{report_id}'.")

        return ExpertVerificationRequestResponse.model_validate(req)

    # --------------------------------------------------------------------------
    # 3. Expert Verification Queue & Clinical Review
    # --------------------------------------------------------------------------

    def list_expert_queue(
        self,
        db: Session,
        user: AuthenticatedUser,
        status: Optional[str] = None,
        crop_code: Optional[str] = None,
        assigned_to_me: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> ExpertQueueListResponse:
        """List expert verification requests with clinical summaries and triage details."""
        query = (
            db.query(ExpertVerificationRequest)
            .options(
                selectinload(ExpertVerificationRequest.crop_report)
                .selectinload(CropReport.farmer_crop)
                .selectinload(FarmerCrop.crop),
                selectinload(ExpertVerificationRequest.crop_report).selectinload(CropReport.diagnoses),
            )
        )

        if status:
            query = query.filter(ExpertVerificationRequest.status == status.strip().upper())
        if assigned_to_me:
            query = query.filter(ExpertVerificationRequest.expert_id == user.id)
        if crop_code:
            query = (
                query.join(CropReport, ExpertVerificationRequest.crop_report_id == CropReport.id)
                .join(FarmerCrop, CropReport.farmer_crop_id == FarmerCrop.id)
                .join(Crop, FarmerCrop.crop_id == Crop.id)
                .filter(Crop.code == crop_code.strip().lower())
            )

        total = query.count()
        requests = query.order_by(desc(ExpertVerificationRequest.requested_at)).offset(offset).limit(limit).all()

        items: List[ExpertQueueItem] = []
        for req in requests:
            r = req.crop_report
            crop_obj = r.farmer_crop.crop if (r and r.farmer_crop) else None
            c_name = getattr(crop_obj, "name_en", getattr(crop_obj, "name", "Unknown")) if crop_obj else "Unknown"
            c_code = getattr(crop_obj, "code", "unknown") if crop_obj else "unknown"

            latest_diag = r.diagnoses[0] if (r and r.diagnoses) else None
            diag_summary = None
            if latest_diag:
                diag_summary = EligibleReportDiagnosisSummary(
                    crop=latest_diag.crop,
                    predicted_class=latest_diag.predicted_class,
                    confidence=latest_diag.confidence,
                    model_name=latest_diag.model_name,
                    created_at=latest_diag.created_at,
                )

            corroborations = (
                db.query(CommunityCorroboration)
                .filter(CommunityCorroboration.crop_report_id == req.crop_report_id)
                .all()
            )
            summary = calculate_corroboration_summary(
                corroborations,
                r.status if r else "UNVERIFIED",
            )

            items.append(
                ExpertQueueItem(
                    id=req.id,
                    crop_report_id=req.crop_report_id,
                    farmer_id=req.farmer_id,
                    expert_id=req.expert_id,
                    status=req.status,
                    crop_code=c_code,
                    crop_name=c_name,
                    farmer_notes=r.notes if r else None,
                    image_storage_path=r.image_storage_path if r else None,
                    image_filename=r.image_filename if r else None,
                    latest_diagnosis=diag_summary,
                    corroboration_summary=summary,
                    requested_at=req.requested_at,
                    assigned_at=req.assigned_at,
                    completed_at=req.completed_at,
                )
            )

        return ExpertQueueListResponse(items=items, total=total)

    def get_expert_request_detail(
        self,
        db: Session,
        request_id: uuid.UUID,
        user: AuthenticatedUser,
    ) -> ExpertVerificationDetailResponse:
        """Fetch exhaustive clinical details for an expert reviewing a verification request."""
        req = (
            db.query(ExpertVerificationRequest)
            .options(
                selectinload(ExpertVerificationRequest.crop_report)
                .selectinload(CropReport.farmer_crop)
                .selectinload(FarmerCrop.crop),
                selectinload(ExpertVerificationRequest.crop_report).selectinload(CropReport.diagnoses),
                selectinload(ExpertVerificationRequest.farmer),
            )
            .filter(ExpertVerificationRequest.id == request_id)
            .first()
        )
        if req is None:
            raise RequestNotFoundError(f"Expert verification request with ID '{request_id}' not found.")

        r = req.crop_report
        if r is None:
            raise ReportNotFoundError(f"Associated crop report for request '{request_id}' not found.")

        crop_obj = r.farmer_crop.crop if r.farmer_crop else None
        c_name = getattr(crop_obj, "name_en", getattr(crop_obj, "name", "Unknown")) if crop_obj else "Unknown"
        c_code = getattr(crop_obj, "code", "unknown") if crop_obj else "unknown"

        farmer_name = req.farmer.full_name if req.farmer else None

        diagnoses_resp = [
            CropReportDiagnosisRecordResponse.model_validate(d)
            for d in (r.diagnoses or [])
        ]

        corroborations = (
            db.query(CommunityCorroboration)
            .filter(CommunityCorroboration.crop_report_id == req.crop_report_id)
            .order_by(desc(CommunityCorroboration.created_at))
            .all()
        )

        corroborations_resp = [
            CorroborationResponse(
                id=c.id,
                crop_report_id=c.crop_report_id,
                community_member_id=c.community_member_id,
                observation_type=c.observation_type,
                is_agreed=is_agreeing_observation(c.observation_type),
                notes=c.notes,
                village_id=c.village_id,
                created_at=c.created_at,
            )
            for c in corroborations
        ]

        summary = calculate_corroboration_summary(corroborations, r.status)

        return ExpertVerificationDetailResponse(
            request=ExpertVerificationRequestResponse.model_validate(req),
            report=CropReportResponse.model_validate(r),
            crop_code=c_code,
            crop_name=c_name,
            farmer_id=req.farmer_id,
            farmer_name=farmer_name,
            image_storage_path=r.image_storage_path,
            diagnoses=diagnoses_resp,
            corroborations=corroborations_resp,
            corroboration_summary=summary,
        )

    def assign_verification_request(
        self,
        db: Session,
        request_id: uuid.UUID,
        user: AuthenticatedUser,
        target_expert_id: Optional[uuid.UUID] = None,
    ) -> ExpertVerificationRequestResponse:
        """Assign or claim an expert verification request."""
        req = db.get(ExpertVerificationRequest, request_id)
        if req is None:
            raise RequestNotFoundError(f"Verification request with ID '{request_id}' not found.")

        if req.status in ["VERIFIED", "REJECTED"]:
            raise RequestAlreadyFinalizedError("Cannot reassign a finalized verification request.")

        # Non-admins can only claim for themselves
        if target_expert_id and target_expert_id != user.id and "ADMIN" not in user.roles:
            raise UnauthorizedAccessError("Only administrators can assign requests to other experts.")

        assignee = target_expert_id or user.id

        # Verify assignee profile exists
        assignee_profile = db.get(UserProfile, assignee)
        if assignee_profile is None:
            raise UnauthorizedAccessError(f"Expert user profile with ID '{assignee}' not found.")

        req.expert_id = assignee
        req.assigned_at = datetime.now(timezone.utc)
        req.status = "ASSIGNED"
        db.commit()
        db.refresh(req)

        logger.info("Request %s assigned to expert %s", req.id, assignee)
        return ExpertVerificationRequestResponse.model_validate(req)

    def submit_expert_decision(
        self,
        db: Session,
        request_id: uuid.UUID,
        user: AuthenticatedUser,
        payload: ExpertDecisionCreate,
    ) -> ExpertDecisionResponse:
        """Submit a clinical decision for an expert verification request.

        Validations:
        - Request exists (404)
        - Request is not already finalized unless ADMIN (409)
        - If request assigned to another expert, only that expert or ADMIN can decide (403)
        - Action is one of APPROVE, CONFIRM, CORRECT, REJECT, REQUEST_REVIEW, NEED_MORE_INFO (422)

        Status Advancement:
        - APPROVE/CONFIRM/CORRECT: transitions CropReport status to EXPERT_VERIFIED.
        - REJECT / NEED_MORE_INFO: does not advance crop report status (and never moves backwards).
        """
        req = (
            db.query(ExpertVerificationRequest)
            .options(
                selectinload(ExpertVerificationRequest.crop_report).selectinload(CropReport.diagnoses),
            )
            .filter(ExpertVerificationRequest.id == request_id)
            .first()
        )
        if req is None:
            raise RequestNotFoundError(f"Verification request with ID '{request_id}' not found.")

        report = req.crop_report
        if report is None:
            raise ReportNotFoundError(f"Crop report for request '{request_id}' not found.")

        # Finalized check
        if req.status in ["VERIFIED", "REJECTED"] and "ADMIN" not in user.roles:
            raise RequestAlreadyFinalizedError("Verification request has already been finalized.")

        # Assignment enforcement
        if req.expert_id and req.expert_id != user.id and "ADMIN" not in user.roles:
            raise UnauthorizedExpertError("This request is currently assigned to another expert.")

        # Auto-claim if unassigned
        if not req.expert_id:
            req.expert_id = user.id
            req.assigned_at = datetime.now(timezone.utc)

        decision = payload.decision.strip().upper()
        now = datetime.now(timezone.utc)
        ladder_advanced = False

        if decision in ["APPROVE", "CONFIRM", "CORRECT"]:
            req.status = "VERIFIED"
            req.action_type = "CORRECT" if decision == "CORRECT" else "CONFIRM"

            latest_diag = report.diagnoses[0] if report.diagnoses else None
            default_finding = latest_diag.predicted_class if latest_diag else "CONFIRMED_HEALTHY"
            req.finding = payload.finding or default_finding
            req.expert_notes = payload.expert_notes
            req.recommended_action = payload.recommended_action
            req.completed_at = now

            # Advance Trust Ladder to EXPERT_VERIFIED
            ladder_advanced = transition_crop_report_status(
                db,
                report,
                VerificationStatus.EXPERT_VERIFIED.value,
            )

        elif decision in ["REJECT", "REJECTED"]:
            req.status = "REJECTED"
            req.action_type = "REJECT"
            req.finding = payload.finding
            req.expert_notes = payload.expert_notes
            req.recommended_action = payload.recommended_action
            req.completed_at = now
            # Do NOT downgrade report status

        elif decision in ["REQUEST_REVIEW", "NEED_MORE_INFO"]:
            req.status = "NEED_MORE_INFO"
            req.action_type = "NEED_MORE_INFO"
            req.expert_notes = payload.expert_notes
            req.recommended_action = payload.recommended_action
            req.completed_at = None
            # Do NOT downgrade report status

        else:
            raise InvalidExpertDecisionError(
                f"Invalid decision '{payload.decision}'. Allowed: "
                "APPROVE, CONFIRM, CORRECT, REJECT, REQUEST_REVIEW, NEED_MORE_INFO"
            )

        db.commit()
        db.refresh(req)
        db.refresh(report)

        logger.info(
            "Expert %s finalized decision '%s' on request %s (new report status: %s)",
            user.id,
            decision,
            req.id,
            report.status,
        )

        return ExpertDecisionResponse(
            verification_request=ExpertVerificationRequestResponse.model_validate(req),
            new_report_status=report.status,
            ladder_advanced=ladder_advanced,
        )

    # --------------------------------------------------------------------------
    # 4. Full Trust Ladder Status & Audit History
    # --------------------------------------------------------------------------

    def get_verification_status(
        self,
        db: Session,
        report_id: uuid.UUID,
        user: AuthenticatedUser,
    ) -> VerificationStatusResponse:
        """Retrieve complete trust ladder status, latest diagnosis, corroborations, and history."""
        report = (
            db.query(CropReport)
            .options(
                selectinload(CropReport.farmer_crop),
                selectinload(CropReport.diagnoses),
            )
            .filter(CropReport.id == report_id)
            .first()
        )
        if report is None:
            raise ReportNotFoundError(f"Crop report with ID '{report_id}' not found.")

        owner_id = report.farmer_crop.farmer_id if report.farmer_crop else None

        # Ownership / privacy check: other farmers cannot access private report status
        is_owner = (owner_id == user.id)
        is_privileged = any(r in user.roles for r in ["ADMIN", "AGRICULTURE_EXPERT", "COMMUNITY_MEMBER"])
        if not is_owner and not is_privileged:
            raise UnauthorizedAccessError("Access forbidden: You cannot view verification details for this crop report.")

        latest_diag = report.diagnoses[0] if report.diagnoses else None
        diag_summary = None
        if latest_diag:
            diag_summary = EligibleReportDiagnosisSummary(
                crop=latest_diag.crop,
                predicted_class=latest_diag.predicted_class,
                confidence=latest_diag.confidence,
                model_name=latest_diag.model_name,
                created_at=latest_diag.created_at,
            )

        corroborations = (
            db.query(CommunityCorroboration)
            .filter(CommunityCorroboration.crop_report_id == report_id)
            .order_by(desc(CommunityCorroboration.created_at))
            .all()
        )
        corroboration_summary = calculate_corroboration_summary(
            corroborations,
            report.status,
        )

        latest_expert_req = (
            db.query(ExpertVerificationRequest)
            .filter(ExpertVerificationRequest.crop_report_id == report_id)
            .order_by(desc(ExpertVerificationRequest.requested_at))
            .first()
        )
        expert_resp = (
            ExpertVerificationRequestResponse.model_validate(latest_expert_req)
            if latest_expert_req
            else None
        )

        # Build chronological audit trail
        history: List[StatusHistoryEntry] = [
            StatusHistoryEntry(
                status=VerificationStatus.UNVERIFIED.value,
                rank=STATUS_RANKS[VerificationStatus.UNVERIFIED.value],
                timestamp=report.created_at,
                actor_role="FARMER",
                description="Crop observation submitted by farmer",
            )
        ]

        if latest_diag:
            history.append(
                StatusHistoryEntry(
                    status=VerificationStatus.AI_ANALYSED.value,
                    rank=STATUS_RANKS[VerificationStatus.AI_ANALYSED.value],
                    timestamp=latest_diag.created_at,
                    actor_role="AI_ENGINE",
                    description=(
                        f"AI diagnosis: {latest_diag.predicted_class} "
                        f"({latest_diag.confidence * 100:.1f}% confidence)"
                    ),
                )
            )

        if corroboration_summary.is_corroborated:
            # Find the corroboration that satisfied the threshold or report updated_at
            corrob_ts = report.updated_at
            if corroborations:
                sorted_c = sorted(corroborations, key=lambda c: c.created_at)
                agreed_running = 0
                for c in sorted_c:
                    if is_agreeing_observation(c.observation_type):
                        agreed_running += 1
                        if agreed_running >= settings.MIN_CORROBORATIONS_FOR_VERIFICATION:
                            corrob_ts = c.created_at
                            break

            history.append(
                StatusHistoryEntry(
                    status=VerificationStatus.CORROBORATED.value,
                    rank=STATUS_RANKS[VerificationStatus.CORROBORATED.value],
                    timestamp=corrob_ts,
                    actor_role="COMMUNITY_MEMBER",
                    description=(
                        f"Community consensus confirmed "
                        f"({corroboration_summary.agreed_count} agreeing corroborations)"
                    ),
                )
            )

        if report.status == VerificationStatus.EXPERT_VERIFIED.value and latest_expert_req:
            history.append(
                StatusHistoryEntry(
                    status=VerificationStatus.EXPERT_VERIFIED.value,
                    rank=STATUS_RANKS[VerificationStatus.EXPERT_VERIFIED.value],
                    timestamp=latest_expert_req.completed_at or report.updated_at,
                    actor_role="AGRICULTURE_EXPERT",
                    description=(
                        f"Expert verified: {latest_expert_req.finding or 'Confirmed'} "
                        f"(Decision: {latest_expert_req.action_type})"
                    ),
                )
            )

        curr_rank = STATUS_RANKS.get(report.status, 0)

        return VerificationStatusResponse(
            crop_report_id=report.id,
            verification_status=report.status,
            status_rank=curr_rank,
            is_ai_analysed=(curr_rank >= STATUS_RANKS[VerificationStatus.AI_ANALYSED.value]),
            is_corroborated=(curr_rank >= STATUS_RANKS[VerificationStatus.CORROBORATED.value]),
            is_expert_verified=(curr_rank >= STATUS_RANKS[VerificationStatus.EXPERT_VERIFIED.value]),
            latest_diagnosis=diag_summary,
            corroboration_summary=corroboration_summary,
            expert_verification=expert_resp,
            status_history=history,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )


# Singleton factory provider
_verification_service_instance: Optional[VerificationService] = None


def get_verification_service() -> VerificationService:
    """Dependency provider / singleton factory for VerificationService."""
    global _verification_service_instance
    if _verification_service_instance is None:
        _verification_service_instance = VerificationService()
    return _verification_service_instance
