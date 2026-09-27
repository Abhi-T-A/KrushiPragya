"""Marketplace Payment API Endpoints: Order creation, server-side signature verification, and transactions."""
import logging
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse
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
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
) -> PaymentOrderResponse:
    """Create server-side payment order for buyer or farmer involved in the offer."""
    try:
        return await payment_service.create_payment_order(
            db=db,
            user_id=user.id,
            payload=payload,
            user_roles=user.roles,
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
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
) -> TransactionResponse:
    """Verify payment signature server-side; NEVER trust client claims blindly."""
    try:
        return payment_service.verify_payment(
            db=db,
            user_id=user.id,
            payload=payload,
            user_roles=user.roles,
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


@router.get(
    "/status/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get payment transaction status",
    description="Authoritative status endpoint for the payment transaction.",
)
def get_payment_status(
    transaction_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
) -> TransactionResponse:
    """Retrieve transaction status enforcing buyer/farmer access."""
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


@router.post(
    "/payu-callback",
    status_code=status.HTTP_200_OK,
    summary="PayU redirect callback endpoint",
    description="Handles redirect response from PayU Hosted Checkout.",
)
@router.get(
    "/payu-callback",
    status_code=status.HTTP_200_OK,
    summary="PayU redirect callback endpoint (GET fallback)",
)
async def payu_callback(
    request: Request,
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
):
    """Process PayU callback from browser redirection or webhook."""
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

    provider = payment_service.provider
    verify_fn = getattr(provider, "verify_payment_hash", None)
    if verify_fn and not verify_fn(event_data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PayU callback hash")

    res = payment_service.process_webhook_event(db=db, event_data=event_data)

    accept_header = request.headers.get("accept", "").lower()
    if "text/html" in accept_header:
        txnid = event_data.get("txnid", "")
        status_str = str(event_data.get("status", "")).lower()
        is_success = status_str in ("success", "captured", "paid")
        title_kn = "ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ" if is_success else "ಪಾವತಿ ವಿಫಲವಾಗಿದೆ"
        title_en = "Payment Successful" if is_success else "Payment Failed"
        theme_color = "#16A34A" if is_success else "#DC2626"
        deep_link = f"krushipragya://market/payment-complete?status={status_str}&txnid={txnid}"

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
    .btn {{ display: inline-block; background: #114B32; color: #FFFFFF; text-decoration: none; font-weight: 700; font-size: 15px; padding: 12px 24px; border-radius: 10px; margin-top: 12px; }}
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
    "/payu-checkout-form/{transaction_id}",
    response_class=HTMLResponse,
    summary="PayU auto-submitting POST checkout form",
)
def payu_checkout_form(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
    payment_service: MarketPaymentService = Depends(get_payment_service),
):
    from app.models.marketplace import MarketplaceTransaction, ProduceListing
    from app.models.crop import Crop
    from app.models.user_profile import UserProfile

    tx = db.get(MarketplaceTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    provider = payment_service.provider
    if not provider.is_configured() or getattr(provider, "provider_name", "") != "payu":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PayU provider is not configured")

    buyer = db.get(UserProfile, tx.buyer_id)
    listing = db.get(ProduceListing, tx.listing_id)
    crop_name = "Produce Listing"
    if listing:
        crop = db.get(Crop, listing.crop_id)
        if crop:
            crop_name = crop.name_en

    firstname = buyer.full_name if buyer else "Buyer"
    email = f"{buyer.phone or str(tx.buyer_id)}@krushipragya.in" if buyer else "buyer@krushipragya.in"
    phone = buyer.phone if buyer and buyer.phone else "9876543210"
    txnid = tx.gateway_order_id or f"kp_tx_{str(tx.id)[:8]}"

    payment_hash = provider.generate_hash(
        txnid=txnid,
        amount=tx.amount,
        productinfo=crop_name,
        firstname=firstname,
        email=email,
        udf1=str(tx.offer_id),
        udf2=str(tx.listing_id),
        udf3=str(tx.buyer_id),
        udf4=str(tx.farmer_id),
        udf5="",
    )

    surl = "https://krushipragya.in/api/v1/market/payments/payu-callback"
    furl = "https://krushipragya.in/api/v1/market/payments/payu-callback"
    amount_str = f"{tx.amount:.2f}"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>PayU Checkout - KrushiPragya</title>
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
    <input type="hidden" name="productinfo" value="{crop_name}" />
    <input type="hidden" name="firstname" value="{firstname}" />
    <input type="hidden" name="email" value="{email}" />
    <input type="hidden" name="phone" value="{phone}" />
    <input type="hidden" name="surl" value="{surl}" />
    <input type="hidden" name="furl" value="{furl}" />
    <input type="hidden" name="hash" value="{payment_hash}" />
    <input type="hidden" name="udf1" value="{str(tx.offer_id)}" />
    <input type="hidden" name="udf2" value="{str(tx.listing_id)}" />
    <input type="hidden" name="udf3" value="{str(tx.buyer_id)}" />
    <input type="hidden" name="udf4" value="{str(tx.farmer_id)}" />
    <input type="hidden" name="udf5" value="" />
    <noscript><input type="submit" value="Click here if not redirected automatically" /></noscript>
  </form>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=200)

