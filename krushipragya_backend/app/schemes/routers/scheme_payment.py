"""Router for Government Scheme Applications and PhonePe Static QR Payments."""
import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
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


@router.post(
    "/payments/payu-callback",
    status_code=status.HTTP_200_OK,
    summary="PayU redirect callback for government scheme payment",
    description="Handles browser redirection / webhook callback from PayU Hosted Checkout for scheme fees.",
)
@router.get(
    "/payments/payu-callback",
    status_code=status.HTTP_200_OK,
    summary="PayU redirect callback (GET fallback)",
)
async def scheme_payu_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """Process PayU callback for scheme application fees with reverse hash verification."""
    if request.method == "POST":
        body = await request.body()
        try:
            from urllib.parse import parse_qs
            parsed = parse_qs(body.decode("utf-8"))
            event_data = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        except Exception:
            import json
            try:
                event_data = json.loads(body.decode("utf-8"))
            except Exception:
                event_data = {}
    else:
        event_data = dict(request.query_params)

    from app.market.services.payment_provider import get_payment_provider
    provider = get_payment_provider()
    verify_fn = getattr(provider, "verify_payment_hash", None)
    if verify_fn and not verify_fn(event_data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PayU callback hash")

    res = SchemePaymentService.process_payu_callback(db=db, event_data=event_data)

    accept_header = request.headers.get("accept", "").lower()
    if "text/html" in accept_header:
        txnid = event_data.get("txnid", "")
        status_str = str(event_data.get("status", "")).lower()
        is_success = status_str in ("success", "captured", "paid")
        title_kn = "ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ" if is_success else "ಪಾವತಿ ವಿಫಲವಾಗಿದೆ"
        title_en = "Payment Successful" if is_success else "Payment Failed"
        theme_color = "#16A34A" if is_success else "#DC2626"
        deep_link = f"krushipragya://schemes/payment-complete?status={status_str}&txnid={txnid}"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title_en}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="2;url={deep_link}">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #F9FAFB; margin: 0; padding: 40px 16px; display: flex; justify-content: center; }}
    .card {{ background: #FFFFFF; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); padding: 32px 24px; max-width: 420px; width: 100%; text-align: center; }}
    .status-title {{ color: {theme_color}; font-size: 20px; font-weight: 700; margin: 12px 0 4px; }}
    .status-sub {{ color: #4B5563; font-size: 14px; margin: 0 0 16px; }}
    .meta-box {{ background: #F3F4F6; border-radius: 10px; padding: 12px; margin: 16px 0; font-size: 13px; color: #374151; }}
    .btn {{ display: inline-block; background: #16A34A; color: #FFFFFF; text-decoration: none; font-weight: 700; font-size: 15px; padding: 12px 24px; border-radius: 10px; margin-top: 12px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="status-title">{title_kn}</div>
    <div class="status-sub">{title_en}</div>
    <div class="meta-box">Transaction ID: <strong>{txnid}</strong></div>
    <a href="{deep_link}" class="btn">ಆ್ಯಪ್‌ಗೆ ಹಿಂತಿರುಗಿ (Return to App)</a>
  </div>
  <script>
    setTimeout(function() {{
      window.location.href = "{deep_link}";
    }}, 1200);
  </script>
</body>
</html>"""
        return HTMLResponse(content=html_content, status_code=200)

    return res


@router.get(
    "/payments/status/{transaction_id}",
    status_code=status.HTTP_200_OK,
    summary="Get scheme payment transaction status",
    description="Authoritatively returns the state of a scheme payment transaction.",
)
def get_scheme_payment_status(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve transaction state enforcing farmer ownership."""
    from app.models.government import PaymentTransaction
    tx = db.get(PaymentTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment transaction not found.")

    if tx.farmer_id != current_user.id and not current_user.has_role("ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")

    return {
        "transaction_id": str(tx.id),
        "application_id": str(tx.application_id) if tx.application_id else None,
        "farmer_id": str(tx.farmer_id),
        "amount": float(tx.total_amount),
        "currency": tx.currency,
        "provider": tx.provider or "payu",
        "merchant_transaction_id": tx.merchant_transaction_id,
        "provider_transaction_id": tx.provider_transaction_id,
        "payment_status": tx.payment_status,
        "failure_reason": tx.failure_reason,
        "paid_at": tx.paid_at.isoformat() if tx.paid_at else None,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
        "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
    }


@router.get(
    "/applications/{application_id}/payment/status",
    status_code=status.HTTP_200_OK,
    summary="Get payment status by application ID",
)
def get_application_payment_status(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get payment status for a specific application."""
    from app.models.government import SchemeApplication, PaymentTransaction
    app = db.get(SchemeApplication, application_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    if app.farmer_id != current_user.id and not current_user.has_role("ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")

    tx = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.application_id == application_id)
        .order_by(PaymentTransaction.created_at.desc())
        .first()
    )

    return {
        "application_id": str(app.id),
        "application_status": app.status,
        "payment_status": app.payment_status,
        "transaction_id": str(tx.id) if tx else None,
        "amount": float(tx.total_amount) if tx else None,
        "provider": tx.provider if tx else "payu",
        "merchant_transaction_id": tx.merchant_transaction_id if tx else None,
        "provider_transaction_id": tx.provider_transaction_id if tx else None,
        "failure_reason": tx.failure_reason if tx else None,
    }


@router.post(
    "/applications/{application_id}/payment/payu-verify",
    status_code=status.HTTP_200_OK,
    summary="Verify PayU payment response server-side",
)
def verify_scheme_payu_payment(
    application_id: uuid.UUID,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Authoritatively verify PayU payment response from client."""
    try:
        return SchemePaymentService.verify_payu_payment(
            db=db,
            farmer_id=current_user.id,
            application_id=application_id,
            payload=payload,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/payments/payu-checkout-form/{transaction_id}",
    response_class=HTMLResponse,
    summary="PayU auto-submitting POST checkout form for scheme application",
)
def scheme_payu_checkout_form(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Renders PayU auto-submitting form for scheme application payment."""
    from app.models.government import PaymentTransaction, GovernmentScheme, SchemeApplication
    from app.models.user_profile import UserProfile
    from app.market.services.payment_provider import get_payment_provider

    tx = db.get(PaymentTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment transaction not found")

    provider = get_payment_provider()
    if not provider.is_configured() or getattr(provider, "provider_name", "") != "payu":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PayU provider is not configured")

    scheme = db.get(GovernmentScheme, tx.scheme_id) if tx.scheme_id else None
    farmer = db.get(UserProfile, tx.farmer_id)
    scheme_title = scheme.title if scheme else "Government Scheme Application"

    firstname = farmer.full_name if farmer and farmer.full_name else "Farmer"
    email = f"{farmer.phone or str(tx.farmer_id)}@krushipragya.in" if farmer else "farmer@krushipragya.in"
    phone = farmer.phone if farmer and farmer.phone else "9876543210"
    txnid = tx.merchant_transaction_id or f"kp_scheme_{str(tx.id)[:8]}"

    payment_hash = provider.generate_hash(
        txnid=txnid,
        amount=tx.total_amount,
        productinfo=scheme_title[:30],
        firstname=firstname,
        email=email,
        udf1=str(tx.application_id or ""),
        udf2=str(tx.scheme_id or ""),
        udf3=str(tx.farmer_id or ""),
        udf4="SCHEME_APPLICATION",
        udf5="",
    )

    surl = "https://krushipragya.in/api/v1/schemes/payments/payu-callback"
    furl = "https://krushipragya.in/api/v1/schemes/payments/payu-callback"
    amount_str = f"{tx.total_amount:.2f}"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>PayU Scheme Payment - KrushiPragya</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: sans-serif; text-align: center; padding-top: 50px; background: #F9FAFB; }}
    .loader {{ font-size: 16px; color: #374151; }}
  </style>
</head>
<body onload="document.forms[0].submit()">
  <div class="loader">
    <p>Connecting to PayU secure payment gateway...</p>
    <p>ದಯವಿಟ್ಟು ನಿರೀಕ್ಷಿಸಿ, PayU ಗೇಟ್‌ವೇಗೆ ಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ...</p>
  </div>
  <form method="post" action="{provider.action_url}">
    <input type="hidden" name="key" value="{provider.merchant_key}" />
    <input type="hidden" name="txnid" value="{txnid}" />
    <input type="hidden" name="amount" value="{amount_str}" />
    <input type="hidden" name="productinfo" value="{scheme_title[:30]}" />
    <input type="hidden" name="firstname" value="{firstname}" />
    <input type="hidden" name="email" value="{email}" />
    <input type="hidden" name="phone" value="{phone}" />
    <input type="hidden" name="surl" value="{surl}" />
    <input type="hidden" name="furl" value="{furl}" />
    <input type="hidden" name="hash" value="{payment_hash}" />
    <input type="hidden" name="udf1" value="{str(tx.application_id or '')}" />
    <input type="hidden" name="udf2" value="{str(tx.scheme_id or '')}" />
    <input type="hidden" name="udf3" value="{str(tx.farmer_id or '')}" />
    <input type="hidden" name="udf4" value="SCHEME_APPLICATION" />
    <input type="hidden" name="udf5" value="" />
    <noscript><input type="submit" value="Click here if not redirected automatically" /></noscript>
  </form>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=200)
