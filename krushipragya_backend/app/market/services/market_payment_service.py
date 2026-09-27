"""Marketplace Payment Service: Order creation, cryptographic verification, and order lifecycle.

Provider-agnostic payment processing supporting PayU and Razorpay.
"""
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.market.schemas.market import (
    PaymentOrderCreateRequest,
    PaymentOrderResponse,
    PaymentVerifyRequest,
    TransactionResponse,
)
from app.market.services.payment_provider import PaymentProvider, get_payment_provider
from app.models.crop import Crop
from app.models.marketplace import BuyerOffer, MarketplaceTransaction, ProduceListing
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)


class MarketPaymentService:
    """Service handling server-side marketplace transactions, payments, and verification."""

    def __init__(self, payment_provider: Optional[PaymentProvider] = None):
        self.provider = payment_provider or get_payment_provider()

    async def create_payment_order(
        self,
        db: Session,
        user_id: uuid.UUID,
        payload: PaymentOrderCreateRequest,
        user_roles: Optional[List[str]] = None,
    ) -> PaymentOrderResponse:
        """Create a server-side payment order for an accepted offer."""
        offer = db.get(BuyerOffer, payload.offer_id)
        if not offer:
            raise ValueError(f"Offer with ID '{payload.offer_id}' not found.")

        listing = db.get(ProduceListing, offer.listing_id)
        if not listing:
            raise ValueError("Produce listing associated with this offer not found.")

        is_buyer = (offer.buyer_id == user_id)
        is_farmer = (listing.farmer_id == user_id)
        is_admin = bool(user_roles and "ADMIN" in user_roles)

        if not (is_buyer or is_farmer or is_admin):
            raise PermissionError("Access forbidden: You do not own this offer.")

        if offer.status not in ("ACCEPTED", "COMPLETED"):
            raise ValueError(
                f"Cannot create payment order: Offer status is '{offer.status}'. Offer must be ACCEPTED first."
            )

        if listing.status in ("DELISTED", "CANCELLED"):
            raise ValueError(f"Cannot create payment order: Listing status is '{listing.status}'.")

        existing_paid = (
            db.query(MarketplaceTransaction)
            .filter(
                MarketplaceTransaction.offer_id == offer.id,
                MarketplaceTransaction.payment_status.in_(["PAYMENT_SUCCESS", "PAID"]),
            )
            .first()
        )
        if existing_paid:
            if payload.payment_mode == "DEMO":
                return PaymentOrderResponse(
                    transaction_id=existing_paid.id,
                    offer_id=existing_paid.offer_id,
                    listing_id=existing_paid.listing_id,
                    amount=existing_paid.amount,
                    currency=existing_paid.currency,
                    provider="demo",
                    gateway_order_id=existing_paid.gateway_order_id,
                    gateway_key_id=None,
                    gateway_configured=True,
                    payment_status=existing_paid.payment_status,
                    order_status=existing_paid.order_status,
                    checkout_data={"payment_mode": "DEMO", "status": "ALREADY_PAID"},
                    message_kn="ಈ ವಹಿವಾಟು ಈಗಾಗಲೇ ಯಶಸ್ವಿಯಾಗಿ ಪಾವತಿಸಲಾಗಿದೆ.",
                    message_en="This offer has already been paid.",
                )
            raise ValueError("This offer has already been paid.")

        # Calculate exact total
        total_amount = offer.offered_price * offer.quantity

        # Handle DEMO PAYMENT mode
        if payload.payment_mode == "DEMO":
            demo_order_id = f"demo_order_{uuid.uuid4().hex[:10]}"
            demo_pay_id = f"demo_pay_{uuid.uuid4().hex[:10]}"

            # Check if pending transaction exists
            tx = (
                db.query(MarketplaceTransaction)
                .filter(MarketplaceTransaction.offer_id == offer.id)
                .first()
            )
            if not tx:
                tx = MarketplaceTransaction(
                    id=uuid.uuid4(),
                    offer_id=offer.id,
                    listing_id=listing.id,
                    buyer_id=offer.buyer_id,
                    farmer_id=listing.farmer_id,
                    amount=total_amount,
                    currency="INR",
                    idempotency_key=payload.idempotency_key,
                    gateway_order_id=demo_order_id,
                    gateway_payment_id=demo_pay_id,
                    gateway_signature="DEMO_SIGNATURE_VERIFIED",
                    payment_status="PAYMENT_SUCCESS",
                    order_status="PAID",
                )
                db.add(tx)
            else:
                tx.payment_status = "PAYMENT_SUCCESS"
                tx.order_status = "PAID"
                tx.gateway_order_id = tx.gateway_order_id or demo_order_id
                tx.gateway_payment_id = demo_pay_id
                tx.gateway_signature = "DEMO_SIGNATURE_VERIFIED"
                tx.failure_reason = None

            # Mark listing as SOLD and offer as COMPLETED
            listing.status = "SOLD"
            offer.status = "COMPLETED"

            db.commit()
            db.refresh(tx)

            logger.info("Demo payment SUCCESS for transaction %s (Offer: %s)", tx.id, offer.id)
            return PaymentOrderResponse(
                transaction_id=tx.id,
                offer_id=tx.offer_id,
                listing_id=tx.listing_id,
                amount=tx.amount,
                currency=tx.currency,
                provider="demo",
                gateway_order_id=tx.gateway_order_id,
                gateway_key_id=None,
                gateway_configured=True,
                payment_status=tx.payment_status,
                order_status=tx.order_status,
                checkout_data={"payment_mode": "DEMO", "status": "SUCCESS"},
                message_kn=f"ಡೆಮೊ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ (₹{tx.amount}).",
                message_en=f"Demo payment successful (₹{tx.amount}).",
            )

        # For LIVE gateway payment, only buyer or admin can initiate payment
        if not is_buyer and not is_admin:
            raise PermissionError("Access forbidden: Only buyer can initiate online gateway checkout.")

        provider_name = getattr(self.provider, "provider_name", "payu")

        # Idempotency check: if an order with this key exists, return it
        if payload.idempotency_key:
            existing = (
                db.query(MarketplaceTransaction)
                .filter(MarketplaceTransaction.idempotency_key == payload.idempotency_key)
                .first()
            )
            if existing:
                logger.info("Returning existing transaction %s for idempotency key %s", existing.id, payload.idempotency_key)
                is_configured = self.provider.is_configured()
                return PaymentOrderResponse(
                    transaction_id=existing.id,
                    offer_id=existing.offer_id,
                    listing_id=existing.listing_id,
                    amount=existing.amount,
                    currency=existing.currency,
                    provider=provider_name,
                    gateway_order_id=existing.gateway_order_id,
                    gateway_key_id=getattr(self.provider, "merchant_key", getattr(self.provider, "key_id", None)) if is_configured else None,
                    gateway_configured=is_configured,
                    payment_status=existing.payment_status,
                    order_status=existing.order_status,
                    checkout_data=None,
                    message_kn="ಅಸ್ತಿತ್ವದಲ್ಲಿರುವ ವಹಿವಾಟು ಮರುಪಡೆಯಲಾಗಿದೆ." if is_configured else "ಪಾವತಿ ಸೇವೆ ಈಗ ಲಭ್ಯವಿಲ್ಲ",
                    message_en="Existing transaction retrieved." if is_configured else "Payment gateway is not currently configured.",
                )

        # Check if gateway is configured
        is_configured = self.provider.is_configured()
        gateway_order_id = None
        checkout_data = None

        if is_configured:
            try:
                receipt_str = f"kp_tx_{str(offer.id)[:8]}_{uuid.uuid4().hex[:6]}"
                crop = db.get(Crop, listing.crop_id)
                crop_name = crop.name_en if crop else "Produce Listing"

                buyer = db.get(UserProfile, offer.buyer_id)
                customer_info = {
                    "name": buyer.full_name if buyer else "Buyer",
                    "email": f"{buyer.phone or str(offer.buyer_id)}@krushipragya.in",
                    "phone": buyer.phone or "9876543210",
                }

                notes = {
                    "offer_id": str(offer.id),
                    "listing_id": str(listing.id),
                    "buyer_id": str(offer.buyer_id),
                    "farmer_id": str(listing.farmer_id),
                    "crop_name": crop_name,
                }
                gateway_resp = await self.provider.create_order(
                    amount=total_amount,
                    currency="INR",
                    receipt=receipt_str,
                    customer_info=customer_info,
                    notes=notes,
                )
                gateway_order_id = gateway_resp.get("id")
                checkout_data = gateway_resp.get("checkout_data")
            except Exception as exc:
                logger.error("Failed to create gateway order: %s", exc)
                is_configured = False

        tx = MarketplaceTransaction(
            id=uuid.uuid4(),
            offer_id=offer.id,
            listing_id=listing.id,
            buyer_id=offer.buyer_id,
            farmer_id=listing.farmer_id,
            amount=total_amount,
            currency="INR",
            idempotency_key=payload.idempotency_key,
            gateway_order_id=gateway_order_id,
            payment_status="PAYMENT_PENDING",
            order_status="PENDING_PAYMENT",
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        if checkout_data:
            checkout_data["checkout_url"] = f"/api/v1/market/payments/payu-checkout-form/{tx.id}"

        if not is_configured:
            return PaymentOrderResponse(
                transaction_id=tx.id,
                offer_id=tx.offer_id,
                listing_id=tx.listing_id,
                amount=tx.amount,
                currency="INR",
                provider=provider_name,
                gateway_order_id=None,
                gateway_key_id=None,
                gateway_configured=False,
                payment_status=tx.payment_status,
                order_status=tx.order_status,
                checkout_data=None,
                message_kn="ಪಾವತಿ ಸೇವೆ ಈಗ ಲಭ್ಯವಿಲ್ಲ",
                message_en="Online payment is currently unavailable.",
            )

        return PaymentOrderResponse(
            transaction_id=tx.id,
            offer_id=tx.offer_id,
            listing_id=tx.listing_id,
            amount=tx.amount,
            currency="INR",
            provider=provider_name,
            gateway_order_id=tx.gateway_order_id,
            gateway_key_id=getattr(self.provider, "merchant_key", getattr(self.provider, "key_id", None)),
            gateway_configured=True,
            payment_status=tx.payment_status,
            order_status=tx.order_status,
            checkout_data=checkout_data,
            message_kn="ಪಾವತಿ ಆದೇಶವನ್ನು ರಚಿಸಲಾಗಿದೆ. ದಯವಿಟ್ಟು ಮುಂದುವರಿಯಿರಿ.",
            message_en="Payment order created successfully.",
        )

    def verify_payment(
        self,
        db: Session,
        user_id: uuid.UUID,
        payload: PaymentVerifyRequest,
        user_roles: Optional[List[str]] = None,
    ) -> TransactionResponse:
        """Verify client-submitted payment signature strictly on the server."""
        tx = db.get(MarketplaceTransaction, payload.transaction_id)
        if not tx:
            raise ValueError(f"Transaction '{payload.transaction_id}' not found.")

        is_buyer = (tx.buyer_id == user_id)
        is_farmer = (tx.farmer_id == user_id)
        is_admin = bool(user_roles and "ADMIN" in user_roles)

        if not (is_buyer or is_farmer or is_admin):
            raise PermissionError("Access forbidden: You do not own this transaction.")

        # Idempotency: Already verified transactions cannot be transitioned again
        if tx.payment_status == "PAYMENT_SUCCESS":
            logger.info("Transaction %s is already verified as PAYMENT_SUCCESS.", tx.id)
            return self._format_transaction_response(db, tx)

        # Handle DEMO mode verification
        if payload.payment_mode == "DEMO" or (payload.raw_payload and payload.raw_payload.get("payment_mode") == "DEMO") or payload.payu_status == "DEMO_SUCCESS":
            tx.payment_status = "PAYMENT_SUCCESS"
            tx.order_status = "PAID"
            tx.gateway_payment_id = payload.payu_payment_id or f"demo_pay_{uuid.uuid4().hex[:10]}"
            tx.gateway_signature = "DEMO_SIGNATURE_VERIFIED"
            tx.failure_reason = None

            listing = db.get(ProduceListing, tx.listing_id)
            if listing:
                listing.status = "SOLD"

            offer = db.get(BuyerOffer, tx.offer_id)
            if offer:
                offer.status = "COMPLETED"

            db.commit()
            db.refresh(tx)
            logger.info("Demo payment verified for transaction %s", tx.id)
            return self._format_transaction_response(db, tx)

        if not self.provider.is_configured():
            tx.payment_status = "PAYMENT_FAILED"
            tx.failure_reason = "Payment provider not configured on server."
            db.commit()
            raise ValueError("Online payment is currently unavailable. (Gateway not configured)")

        provider_name = getattr(self.provider, "provider_name", "payu")

        # Cryptographically verify payment using active provider mechanism
        if provider_name == "payu":
            verification_data = payload.raw_payload or {
                "status": payload.payu_status or ("success" if payload.razorpay_signature or payload.payu_hash else "failure"),
                "txnid": payload.payu_txnid or tx.gateway_order_id or "",
                "amount": f"{tx.amount:.2f}",
                "productinfo": "Produce Listing",
                "firstname": "Buyer",
                "email": "buyer@krushipragya.in",
                "mihpayid": payload.payu_payment_id or payload.razorpay_payment_id or f"payu_{tx.gateway_order_id}",
                "hash": payload.payu_hash or payload.razorpay_signature or "",
            }
            verify_fn = getattr(self.provider, "verify_payment_hash", None)
            is_valid = verify_fn(verification_data) if verify_fn else False
            payment_id = payload.payu_payment_id or payload.razorpay_payment_id or verification_data.get("mihpayid")
            signature = payload.payu_hash or payload.razorpay_signature
        else:
            is_valid = self.provider.verify_payment_signature(
                order_id=payload.razorpay_order_id or tx.gateway_order_id or "",
                payment_id=payload.razorpay_payment_id or "",
                signature=payload.razorpay_signature or "",
            )
            payment_id = payload.razorpay_payment_id
            signature = payload.razorpay_signature

        if is_valid:
            tx.payment_status = "PAYMENT_SUCCESS"
            tx.order_status = "PAID"
            tx.gateway_payment_id = payment_id
            tx.gateway_signature = signature
            tx.failure_reason = None

            # Mark listing as SOLD and offer as COMPLETED
            listing = db.get(ProduceListing, tx.listing_id)
            if listing:
                listing.status = "SOLD"

            offer = db.get(BuyerOffer, tx.offer_id)
            if offer:
                offer.status = "COMPLETED"

            logger.info("Payment SUCCESS verified for transaction %s (Payment ID: %s)", tx.id, payment_id)
        else:
            tx.payment_status = "PAYMENT_FAILED"
            tx.failure_reason = "Cryptographic signature verification failed."
            logger.warning("Payment signature VERIFICATION FAILED for transaction %s", tx.id)

        db.commit()
        db.refresh(tx)
        return self._format_transaction_response(db, tx)

    def get_transaction(
        self,
        db: Session,
        user_id: uuid.UUID,
        transaction_id: uuid.UUID,
    ) -> TransactionResponse:
        """Retrieve transaction detail enforcing buyer or farmer ownership."""
        tx = db.get(MarketplaceTransaction, transaction_id)
        if not tx:
            raise ValueError(f"Transaction '{transaction_id}' not found.")

        if tx.buyer_id != user_id and tx.farmer_id != user_id:
            raise PermissionError("Access forbidden: You do not have permission to view this transaction.")

        return self._format_transaction_response(db, tx)

    def get_user_transactions(
        self,
        db: Session,
        user_id: uuid.UUID,
    ) -> List[TransactionResponse]:
        """Retrieve all transactions involving the user as buyer or farmer."""
        txs = (
            db.query(MarketplaceTransaction)
            .filter(
                (MarketplaceTransaction.buyer_id == user_id)
                | (MarketplaceTransaction.farmer_id == user_id)
            )
            .order_by(desc(MarketplaceTransaction.created_at))
            .all()
        )
        return [self._format_transaction_response(db, tx) for tx in txs]

    def _format_transaction_response(
        self,
        db: Session,
        tx: MarketplaceTransaction,
    ) -> TransactionResponse:
        """Format database transaction into structured response with crop, buyer, and farmer details."""
        listing = db.get(ProduceListing, tx.listing_id)
        offer = db.get(BuyerOffer, tx.offer_id)
        buyer = db.get(UserProfile, tx.buyer_id)
        farmer = db.get(UserProfile, tx.farmer_id)

        crop_name = None
        quantity = None
        unit = None
        unit_price = None

        if listing:
            crop = db.get(Crop, listing.crop_id)
            crop_name = crop.name_en if crop else None
            quantity = offer.quantity if offer else listing.quantity
            unit = listing.unit
            unit_price = offer.offered_price if offer else listing.expected_price

        # Contacts are authorized because this is a formal transaction
        buyer_phone = buyer.phone if buyer else None
        farmer_phone = farmer.phone if farmer else None

        return TransactionResponse(
            id=tx.id,
            offer_id=tx.offer_id,
            listing_id=tx.listing_id,
            crop_name=crop_name,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            buyer_id=tx.buyer_id,
            buyer_name=buyer.full_name if buyer else None,
            buyer_phone=buyer_phone,
            farmer_id=tx.farmer_id,
            farmer_name=farmer.full_name if farmer else None,
            farmer_phone=farmer_phone,
            amount=tx.amount,
            currency=tx.currency,
            gateway_order_id=tx.gateway_order_id,
            gateway_payment_id=tx.gateway_payment_id,
            payment_status=tx.payment_status,
            order_status=tx.order_status,
            failure_reason=tx.failure_reason,
            created_at=tx.created_at,
            updated_at=tx.updated_at,
        )

    def process_webhook_event(self, db: Session, event_data: dict) -> dict:
        """Idempotently process authoritative webhook event from payment gateway."""
        provider_name = getattr(self.provider, "provider_name", "payu")

        # PayU webhook / callback format
        if "txnid" in event_data or provider_name == "payu":
            txnid = event_data.get("txnid")
            if not txnid:
                return {"status": "ignored", "reason": "No txnid in event"}

            tx = (
                db.query(MarketplaceTransaction)
                .filter(MarketplaceTransaction.gateway_order_id == txnid)
                .first()
            )
            if not tx:
                return {"status": "ignored", "reason": f"No transaction found for txnid {txnid}"}

            # Idempotency check: if already PAID, do nothing
            if tx.payment_status == "PAYMENT_SUCCESS":
                return {"status": "already_processed", "transaction_id": str(tx.id)}

            verify_fn = getattr(self.provider, "verify_payment_hash", None)
            is_valid = verify_fn(event_data) if verify_fn else False
            if not is_valid:
                return {"status": "invalid_signature", "reason": "PayU hash verification failed"}

            status_str = str(event_data.get("status", "")).lower()
            if status_str in ("success", "captured", "paid"):
                tx.payment_status = "PAYMENT_SUCCESS"
                tx.order_status = "PAID"
                tx.gateway_payment_id = str(event_data.get("mihpayid") or event_data.get("payment_id") or "")
                tx.gateway_signature = event_data.get("hash")
                listing = db.get(ProduceListing, tx.listing_id)
                if listing:
                    listing.status = "SOLD"
                offer = db.get(BuyerOffer, tx.offer_id)
                if offer:
                    offer.status = "COMPLETED"
                db.commit()
                return {"status": "success", "transaction_id": str(tx.id)}
            else:
                tx.payment_status = "PAYMENT_FAILED"
                tx.failure_reason = event_data.get("error_Message") or event_data.get("unmappedstatus") or "Payment failed at PayU gateway"
                db.commit()
                return {"status": "failed", "transaction_id": str(tx.id)}

        # Razorpay webhook format
        event_type = event_data.get("event")
        payload = event_data.get("payload", {})
        payment_entity = payload.get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")

        if not order_id:
            return {"status": "ignored", "reason": "No order_id in event"}

        tx = (
            db.query(MarketplaceTransaction)
            .filter(MarketplaceTransaction.gateway_order_id == order_id)
            .first()
        )
        if not tx:
            return {"status": "ignored", "reason": f"No transaction found for order {order_id}"}

        # Idempotency check: if already PAID, do nothing
        if tx.payment_status == "PAYMENT_SUCCESS":
            return {"status": "already_processed", "transaction_id": str(tx.id)}

        if event_type in ("payment.captured", "order.paid"):
            tx.payment_status = "PAYMENT_SUCCESS"
            tx.order_status = "PAID"
            tx.gateway_payment_id = payment_id
            listing = db.get(ProduceListing, tx.listing_id)
            if listing:
                listing.status = "SOLD"
            offer = db.get(BuyerOffer, tx.offer_id)
            if offer:
                offer.status = "COMPLETED"
            db.commit()
            return {"status": "success", "transaction_id": str(tx.id)}
        elif event_type == "payment.failed":
            tx.payment_status = "PAYMENT_FAILED"
            tx.failure_reason = payment_entity.get("error_description", "Payment failed at gateway")
            db.commit()
            return {"status": "failed", "transaction_id": str(tx.id)}

        return {"status": "unhandled_event", "event": event_type}
