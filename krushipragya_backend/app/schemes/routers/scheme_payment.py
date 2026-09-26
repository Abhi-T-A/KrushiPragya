"""Router for Government Scheme Applications and PhonePe Static QR Payments."""
import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_current_user, require_role
from app.database.connection import get_db
from app.schemes.schemas import (
    PaymentProofSubmitRequest,
    PaymentProofSubmitResponse,
    PaymentReceiptResponse,
    PaymentVerifyRequest,
    SchemeApplicationCreateRequest,
    SchemeApplicationResponse,
    SchemePaymentInitiateResponse,
)
from app.schemes.services.scheme_payment_service import SchemePaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schemes", tags=["Government Scheme Payments & Applications"])


@router.post(
    "/{scheme_id}/apply",
    response_model=SchemeApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or draft a scheme application",
    description="Farmer initiates an application for a specific government scheme with fee resolution.",
)
def apply_for_scheme(
    scheme_id: uuid.UUID,
    payload: Optional[SchemeApplicationCreateRequest] = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SchemeApplicationResponse:
    """Initiate a scheme application draft for the authenticated farmer."""
    notes = payload.application_notes if payload else None
    try:
        return SchemePaymentService.create_or_get_application(
            db=db,
            farmer_id=current_user.id,
            scheme_id=scheme_id,
            application_notes=notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/my-applications",
    response_model=List[SchemeApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="List farmer's scheme applications",
    description="Retrieve all scheme applications submitted or tracked by the current farmer.",
)
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[SchemeApplicationResponse]:
    """List farmer's scheme applications."""
    return SchemePaymentService.get_farmer_applications(db=db, farmer_id=current_user.id)


@router.get(
    "/applications/{application_id}",
    response_model=SchemeApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get scheme application details",
)
def get_application_detail(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SchemeApplicationResponse:
    """Get single scheme application details enforcing ownership."""
    details = SchemePaymentService.get_payment_details_or_receipt(
        db=db,
        user_id=current_user.id,
        application_id=application_id,
    )
    # Re-fetch application
    from app.models.government import SchemeApplication, GovernmentScheme
    app = db.get(SchemeApplication, application_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    if app.farmer_id != current_user.id and not current_user.has_role("ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")

    scheme = db.get(GovernmentScheme, app.scheme_id)
    fee_info = SchemePaymentService.calculate_scheme_fee_info(scheme) if scheme else None
    return SchemePaymentService._format_application_response(app, scheme, fee_info)


@router.post(
    "/applications/{application_id}/payment",
    response_model=SchemePaymentInitiateResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate PhonePe Static QR payment for a scheme application",
    description="Authoritatively calculates official + service fee and generates PhonePe QR data.",
)
def initiate_application_payment(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SchemePaymentInitiateResponse:
    """Initiate PhonePe Static QR payment flow."""
    try:
        return SchemePaymentService.initiate_payment(
            db=db,
            farmer_id=current_user.id,
            application_id=application_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/applications/{application_id}/payment/submit-proof",
    response_model=PaymentProofSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit bank UTR / payment proof",
    description="Farmer submits 12-digit UTR after PhonePe payment; server verifies uniqueness and amount match.",
)
def submit_payment_proof(
    application_id: uuid.UUID,
    payload: PaymentProofSubmitRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PaymentProofSubmitResponse:
    """Submit bank UTR reference for verification."""
    try:
        return SchemePaymentService.submit_payment_proof(
            db=db,
            farmer_id=current_user.id,
            application_id=application_id,
            utr=payload.utr,
            amount_paid=payload.amount_paid,
            notes=payload.notes,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/applications/{application_id}/payment",
    status_code=status.HTTP_200_OK,
    summary="Get payment status, fee summary, and receipt",
)
def get_application_payment(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get payment status and receipt."""
    try:
        res = SchemePaymentService.get_payment_details_or_receipt(
            db=db,
            user_id=current_user.id,
            application_id=application_id,
        )
        return res
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/applications/{application_id}/payment/verify",
    response_model=PaymentReceiptResponse,
    status_code=status.HTTP_200_OK,
    summary="Authorized verification of payment UTR",
    description="Government Officer or Admin verifies UTR against bank account, transitioning status to PAID.",
)
def verify_payment(
    application_id: uuid.UUID,
    payload: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("ADMIN", "GOVERNMENT_OFFICER")),
) -> PaymentReceiptResponse:
    """Authorized manual verification of submitted UTR."""
    try:
        return SchemePaymentService.verify_payment(
            db=db,
            verifier_id=current_user.id,
            application_id=application_id,
            action=payload.action,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/applications/{application_id}/submit",
    response_model=SchemeApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit scheme application",
    description="Formal submission of scheme application after verified payment (or immediately if free).",
)
def submit_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SchemeApplicationResponse:
    """Submit verified application."""
    try:
        return SchemePaymentService.submit_application(
            db=db,
            farmer_id=current_user.id,
            application_id=application_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
