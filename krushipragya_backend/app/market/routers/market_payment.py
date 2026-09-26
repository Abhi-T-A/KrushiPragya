"""Marketplace Payment API Endpoints: Order creation, server-side signature verification, and transactions."""
import logging
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_current_user, require_buyer
from app.database.connection import get_db
from app.market.schemas.market import (
    PaymentOrderCreateRequest,
    PaymentOrderResponse,
    PaymentVerifyRequest,
    TransactionResponse,
)
from app.market.services.market_payment_service import MarketPaymentService
from app.market.services.payment_provider import get_payment_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market/payments", tags=["Marketplace Payments"])


def get_payment_service() -> MarketPaymentService:
    return MarketPaymentService()


@router.post(
    "/create-order",
    response_model=PaymentOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create server-side payment order for an accepted offer",
    description="Initiates a secure payment transaction at the payment gateway for an accepted buyer offer.",
)
async def create_payment_order(
    payload: PaymentOrderCreateRequest,
    buyer_user: AuthenticatedUser = Depends(require_buyer),
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
) -> PaymentOrderResponse:
    """Create server-side payment order enforcing buyer role and offer ownership."""
    try:
        return await payment_service.create_payment_order(
            db=db,
            buyer_id=buyer_user.id,
            payload=payload,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/verify",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify payment signature server-side",
    description="Cryptographically verifies payment signature received from checkout and updates transaction status.",
)
def verify_payment(
    payload: PaymentVerifyRequest,
    buyer_user: AuthenticatedUser = Depends(require_buyer),
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
) -> TransactionResponse:
    """Verify payment signature server-side; NEVER trust client claims blindly."""
    try:
        return payment_service.verify_payment(
            db=db,
            buyer_id=buyer_user.id,
            payload=payload,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get transaction details",
    description="Retrieves transaction details enforcing that caller is either the buyer or the seller.",
)
def get_transaction(
    transaction_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
) -> TransactionResponse:
    """Retrieve transaction details enforcing buyer/farmer access."""
    try:
        return payment_service.get_transaction(
            db=db,
            user_id=user.id,
            transaction_id=transaction_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/my-transactions",
    response_model=List[TransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="List transactions for the authenticated user",
    description="Retrieves all orders and transactions where the caller is either buyer or seller.",
)
def get_my_transactions(
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
) -> List[TransactionResponse]:
    """Retrieve user's transactions as buyer or farmer."""
    return payment_service.get_user_transactions(db=db, user_id=user.id)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Gateway webhook handler",
    description="Authoritative webhook endpoint for PayU and Razorpay gateway events.",
)
async def gateway_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
) -> dict:
    """Handle authoritative webhook events from PayU or Razorpay."""
    body = await request.body()
    content_type = request.headers.get("content-type", "").lower()

    event_data = {}
    if "application/json" in content_type:
        try:
            import json
            event_data = json.loads(body.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")
    else:
        # Form urlencoded (PayU standard)
        try:
            from urllib.parse import parse_qs
            parsed = parse_qs(body.decode("utf-8"))
            event_data = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        except Exception:
            try:
                import json
                event_data = json.loads(body.decode("utf-8"))
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported webhook payload format")

    provider = payment_service.provider

    # Razorpay verification if signature header present
    if x_razorpay_signature:
        if not provider.verify_webhook_signature(body, x_razorpay_signature):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")
    else:
        # PayU hash verification
        verify_fn = getattr(provider, "verify_payment_hash", None)
        if verify_fn and not verify_fn(event_data):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PayU webhook signature/hash")

    return payment_service.process_webhook_event(db=db, event_data=event_data)


@router.post(
    "/payu-callback",
    status_code=status.HTTP_200_OK,
    summary="PayU redirect callback endpoint",
    description="Handles redirect response from PayU Hosted Checkout.",
)
async def payu_callback(
    request: Request,
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
) -> dict:
    """Process PayU callback from browser redirection."""
    body = await request.body()
    try:
        from urllib.parse import parse_qs
        parsed = parse_qs(body.decode("utf-8"))
        event_data = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
    except Exception:
        import json
        event_data = json.loads(body.decode("utf-8"))

    provider = payment_service.provider
    verify_fn = getattr(provider, "verify_payment_hash", None)
    if verify_fn and not verify_fn(event_data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PayU callback hash")

    return payment_service.process_webhook_event(db=db, event_data=event_data)

