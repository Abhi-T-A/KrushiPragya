"""Payment and Application Service for Government Schemes.

Integrates PhonePe Static QR flow, transparent fee separation, authoritative
amount calculation, UTR submission, verification, and formal receipts.
"""
from datetime import datetime, timezone
from decimal import Decimal
import json
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.government import GovernmentScheme, SchemeApplication, PaymentTransaction
from app.models.user_profile import UserProfile
from app.schemes.schemas import (
    PaymentProofSubmitResponse,
    PaymentReceiptResponse,
    SchemeApplicationResponse,
    SchemeFeeInfo,
    SchemePaymentInitiateResponse,
)

logger = logging.getLogger(__name__)

PHONEPE_UPI_ID = "krushipragya@ybl"
PHONEPE_PAYEE_NAME = "KrushiPragya Schemes Assistance"
PHONEPE_QR_ASSET = "assets/phonepe_static_qr.png"


class SchemePaymentService:
    """Core domain service orchestrating scheme fees, static QR payments, and applications."""

    @staticmethod
    def calculate_scheme_fee_info(scheme: GovernmentScheme) -> SchemeFeeInfo:
        """Calculate authoritative, transparent fee structure for a scheme.
        
        Rules:
        - FREE: 0 fee, payment not required.
        - GOVERNMENT_BORNE: Official fee is 0 to farmer; service fee applies if configured.
        - OFFICIAL_FEE: Only official fee is payable.
        - SERVICE_FEE: Only KrushiPragya service fee is payable.
        - OFFICIAL_PLUS_SERVICE_FEE: Both official and service fees are payable.
        - UNKNOWN: Fee is unverified; payment cannot proceed.
        """
        fee_type = (scheme.fee_type or "UNKNOWN").upper()
        official = float(scheme.official_fee) if scheme.official_fee is not None else None
        service = float(scheme.krushipragya_service_fee) if scheme.krushipragya_service_fee is not None else None
        total: Optional[float] = None
        payment_required = False
        is_verified = bool(scheme.fee_last_verified or scheme.fee_source)

        if fee_type == "FREE":
            official = 0.0
            service = 0.0
            total = 0.0
            payment_required = False
            is_verified = True
        elif fee_type == "GOVERNMENT_BORNE":
            official = 0.0
            service = service if service is not None else 0.0
            total = service
            payment_required = (service > 0)
            is_verified = True
        elif fee_type == "OFFICIAL_FEE":
            service = 0.0
            if official is not None:
                total = official
                payment_required = (total > 0)
        elif fee_type == "SERVICE_FEE":
            official = 0.0
            if service is not None:
                total = service
                payment_required = (total > 0)
        elif fee_type == "OFFICIAL_PLUS_SERVICE_FEE":
            if official is not None and service is not None:
                total = round(official + service, 2)
                payment_required = (total > 0)
        elif fee_type == "UNKNOWN":
            payment_required = False
            total = None
            is_verified = False

        return SchemeFeeInfo(
            fee_type=fee_type,
            payment_required=payment_required,
            official_fee=official,
            krushipragya_service_fee=service,
            total_payable=total,
            currency="INR",
            fee_description=scheme.fee_description,
            fee_source=scheme.fee_source,
            fee_last_verified=scheme.fee_last_verified.isoformat() if scheme.fee_last_verified else None,
            is_verified=is_verified,
            notice_kn="ಶುಲ್ಕಗಳನ್ನು ಪಾರದರ್ಶಕತೆಗಾಗಿ ಪ್ರತ್ಯೇಕವಾಗಿ ತೋರಿಸಲಾಗಿದೆ.",
            notice_en="Fees are displayed separately for transparency.",
        )

    @classmethod
    def create_or_get_application(
        cls,
        db: Session,
        farmer_id: uuid.UUID,
        scheme_id: uuid.UUID,
        application_notes: Optional[str] = None,
    ) -> SchemeApplicationResponse:
        """Create a new scheme application draft or retrieve existing pending application."""
        scheme = db.get(GovernmentScheme, scheme_id)
        if not scheme:
            raise ValueError(f"Government scheme '{scheme_id}' not found.")

        # Check existing non-rejected application
        existing = (
            db.query(SchemeApplication)
            .filter(
                SchemeApplication.scheme_id == scheme_id,
                SchemeApplication.farmer_id == farmer_id,
                SchemeApplication.status.notin_(["REJECTED", "CANCELLED"]),
            )
            .first()
        )

        fee_info = cls.calculate_scheme_fee_info(scheme)

        if existing:
            return cls._format_application_response(existing, scheme, fee_info)

        # Initial status: if free, READY_FOR_SUBMISSION; if payment required, PAYMENT_PENDING
        initial_status = "PAYMENT_PENDING" if fee_info.payment_required else "READY_FOR_SUBMISSION"
        initial_pay_status = "PENDING" if fee_info.payment_required else "NOT_REQUIRED"

        now = datetime.now(timezone.utc)
        app = SchemeApplication(
            id=uuid.uuid4(),
            scheme_id=scheme_id,
            farmer_id=farmer_id,
            status=initial_status,
            payment_status=initial_pay_status,
            application_notes=application_notes,
            created_at=now,
            updated_at=now,
        )
        db.add(app)
        db.commit()
        db.refresh(app)

        return cls._format_application_response(app, scheme, fee_info)

    @classmethod
    def initiate_payment(
        cls,
        db: Session,
        farmer_id: uuid.UUID,
        application_id: uuid.UUID,
    ) -> SchemePaymentInitiateResponse:
        """Calculate authoritative amount and return PhonePe Static QR checkout data."""
        app = db.get(SchemeApplication, application_id)
        if not app:
            raise ValueError(f"Scheme application '{application_id}' not found.")

        if app.farmer_id != farmer_id:
            raise PermissionError("Access forbidden: You do not own this scheme application.")

        scheme = db.get(GovernmentScheme, app.scheme_id)
        if not scheme:
            raise ValueError(f"Linked scheme '{app.scheme_id}' not found.")

        fee_info = cls.calculate_scheme_fee_info(scheme)

        if fee_info.fee_type == "UNKNOWN" or not fee_info.is_verified:
            raise ValueError(
                "Fee information needs verification. Online payment cannot proceed until fees are officially verified."
            )

        if not fee_info.payment_required or fee_info.total_payable == 0.0:
            raise ValueError("ಈ ಯೋಜನೆಗೆ ಯಾವುದೇ ಪಾವತಿ ಅಗತ್ಯವಿಲ್ಲ. (No payment is required for this scheme.)")

        # Check existing transaction
        tx = (
            db.query(PaymentTransaction)
            .filter(
                PaymentTransaction.application_id == application_id,
                PaymentTransaction.payment_status.in_(["PENDING", "PROOF_SUBMITTED", "PENDING_VERIFICATION", "PAID"]),
            )
            .first()
        )

        total_dec = Decimal(str(fee_info.total_payable))
        off_dec = Decimal(str(fee_info.official_fee or 0.0))
        srv_dec = Decimal(str(fee_info.krushipragya_service_fee or 0.0))

        if not tx:
            tx = PaymentTransaction(
                id=uuid.uuid4(),
                transaction_type="SCHEME_APPLICATION",
                farmer_id=farmer_id,
                scheme_id=scheme.id,
                application_id=app.id,
                official_fee=off_dec,
                service_fee=srv_dec,
                total_amount=total_dec,
                currency="INR",
                payment_method="PHONEPE_STATIC_QR",
                payment_status="PENDING",
            )
            db.add(tx)
            app.payment_transaction_id = tx.id
            app.payment_status = "PENDING"
            app.status = "PAYMENT_PENDING"
            db.commit()
            db.refresh(tx)

        # Generate QR Payload
        app_id_short = str(app.id)[:8]
        tx_note = f"Scheme App {app_id_short} - {scheme.title[:20]}"
        qr_data = {
            "upi_id": PHONEPE_UPI_ID,
            "payee_name": PHONEPE_PAYEE_NAME,
            "amount": float(tx.total_amount),
            "currency": "INR",
            "transaction_note": tx_note,
            "qr_asset_path": PHONEPE_QR_ASSET,
            "payment_flow": "PHONEPE_STATIC_QR",
        }

        fee_summary = {
            "official_fee": float(tx.official_fee),
            "krushipragya_service_fee": float(tx.service_fee),
            "total_payable": float(tx.total_amount),
            "label_official_kn": "ಸರ್ಕಾರದ ಅರ್ಜಿ ಶುಲ್ಕ",
            "label_service_kn": "KrushiPragya ಸೇವಾ ಶುಲ್ಕ",
            "label_total_kn": "ಒಟ್ಟು ಪಾವತಿ",
            "transparency_note_kn": "ಶುಲ್ಕಗಳನ್ನು ಪಾರದರ್ಶಕತೆಗಾಗಿ ಪ್ರತ್ಯೇಕವಾಗಿ ತೋರಿಸಲಾಗಿದೆ.",
            "transparency_note_en": "Fees are displayed separately for transparency.",
        }

        return SchemePaymentInitiateResponse(
            transaction_id=str(tx.id),
            application_id=str(app.id),
            scheme_id=str(scheme.id),
            scheme_title=scheme.title,
            scheme_title_kn=scheme.title_kn,
            payment_method="PHONEPE_STATIC_QR",
            payment_status=tx.payment_status,
            official_fee=float(tx.official_fee),
            service_fee=float(tx.service_fee),
            total_amount=float(tx.total_amount),
            currency="INR",
            qr_data=qr_data,
            fee_summary=fee_summary,
            message_kn="PhonePe QR ಕೋಡ್ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ ನಿಖರ ಮೊತ್ತವನ್ನು ಪಾವತಿಸಿ. ನಂತರ UTR ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ.",
            message_en="Scan the PhonePe QR code to pay the exact amount. Then enter the UTR reference number.",
        )

    @classmethod
    def submit_payment_proof(
        cls,
        db: Session,
        farmer_id: uuid.UUID,
        application_id: uuid.UUID,
        utr: str,
        amount_paid: float,
        notes: Optional[str] = None,
    ) -> PaymentProofSubmitResponse:
        """Validate submitted bank UTR, enforce amount correctness, and transition to PENDING_VERIFICATION."""
        app = db.get(SchemeApplication, application_id)
        if not app:
            raise ValueError(f"Scheme application '{application_id}' not found.")

        if app.farmer_id != farmer_id:
            raise PermissionError("Access forbidden: You do not own this scheme application.")

        tx = (
            db.query(PaymentTransaction)
            .filter(PaymentTransaction.application_id == application_id)
            .order_by(PaymentTransaction.created_at.desc())
            .first()
        )
        if not tx:
            raise ValueError("No active payment transaction found for this application. Please initiate payment first.")

        # Clean UTR string
        clean_utr = utr.strip()
        if len(clean_utr) < 8 or len(clean_utr) > 30:
            raise ValueError("Invalid UTR reference. Bank reference number must be between 8 and 30 characters.")

        # Check UTR uniqueness across transactions
        existing_utr = (
            db.query(PaymentTransaction)
            .filter(
                PaymentTransaction.payment_reference == clean_utr,
                PaymentTransaction.id != tx.id,
            )
            .first()
        )
        if existing_utr:
            raise ValueError("This UTR / Payment reference has already been submitted for another transaction.")

        # Compare submitted amount with authoritative stored amount
        expected_amount = round(float(tx.total_amount), 2)
        received_amount = round(float(amount_paid), 2)
        if abs(expected_amount - received_amount) > 0.01:
            raise ValueError(
                f"Amount mismatch. The required payable amount is ₹{expected_amount:.2f}, but submitted ₹{received_amount:.2f}."
            )

        # If already verified PAID, do not revert
        if tx.payment_status == "PAID":
            return PaymentProofSubmitResponse(
                transaction_id=str(tx.id),
                application_id=str(app.id),
                payment_reference=clean_utr,
                payment_status=tx.payment_status,
                application_status=app.status,
                amount=float(tx.total_amount),
                message_kn="ಪಾವತಿ ಈಗಾಗಲೇ ಪರಿಶೀಲಿಸಲ್ಪಟ್ಟಿದೆ.",
                message_en="Payment has already been verified as PAID.",
            )

        # Transition status
        tx.payment_reference = clean_utr
        tx.payment_status = "PENDING_VERIFICATION"
        tx.notes = notes

        app.payment_status = "PENDING_VERIFICATION"
        app.status = "PAYMENT_PENDING"

        db.commit()
        db.refresh(tx)
        db.refresh(app)

        return PaymentProofSubmitResponse(
            transaction_id=str(tx.id),
            application_id=str(app.id),
            payment_reference=clean_utr,
            payment_status=tx.payment_status,
            application_status=app.status,
            amount=float(tx.total_amount),
            message_kn="ಯುಟಿಆರ್ ಯಶಸ್ವಿಯಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ. ಕೃಷಿಪ್ರಜ್ಞಾ ತಂಡವು ಪರಿಶೀಲಿಸುತ್ತಿದೆ.",
            message_en="UTR reference submitted successfully. Pending verification by KrushiPragya team.",
        )

    @classmethod
    def verify_payment(
        cls,
        db: Session,
        verifier_id: uuid.UUID,
        application_id: uuid.UUID,
        action: str,
        notes: Optional[str] = None,
    ) -> PaymentReceiptResponse:
        """Authorized review of submitted UTR by Government Officer or Admin."""
        app = db.get(SchemeApplication, application_id)
        if not app:
            raise ValueError(f"Scheme application '{application_id}' not found.")

        tx = (
            db.query(PaymentTransaction)
            .filter(PaymentTransaction.application_id == application_id)
            .order_by(PaymentTransaction.created_at.desc())
            .first()
        )
        if not tx:
            raise ValueError("No payment transaction found to verify.")

        scheme = db.get(GovernmentScheme, app.scheme_id)
        farmer = db.get(UserProfile, app.farmer_id)
        now = datetime.now(timezone.utc)

        action_upper = action.upper()
        if action_upper == "APPROVE":
            tx.payment_status = "PAID"
            tx.paid_at = now
            tx.verified_at = now
            tx.verified_by = verifier_id
            if notes:
                tx.notes = f"{tx.notes or ''} | Verified: {notes}".strip(" |")

            app.payment_status = "PAID"
            app.status = "READY_FOR_SUBMISSION"

            # Create immutable receipt data
            receipt_id = f"KP-REC-{now.strftime('%Y%m%d')}-{str(tx.id)[:8].upper()}"
            receipt_payload = {
                "receipt_id": receipt_id,
                "app_name": "KrushiPragya",
                "scheme_name": scheme.title if scheme else "Government Scheme",
                "scheme_title_kn": scheme.title_kn if scheme else None,
                "application_id": str(app.id),
                "transaction_id": str(tx.id),
                "farmer_id": str(app.farmer_id),
                "farmer_name": farmer.full_name if farmer else None,
                "official_fee": float(tx.official_fee),
                "krushipragya_service_fee": float(tx.service_fee),
                "total_paid": float(tx.total_amount),
                "currency": tx.currency,
                "payment_method": tx.payment_method,
                "payment_reference": tx.payment_reference or "N/A",
                "paid_at": now.isoformat(),
                "verified_at": now.isoformat(),
                "payment_status": "PAID",
                "transparency_notice_kn": "ಶುಲ್ಕಗಳನ್ನು ಪಾರದರ್ಶಕತೆಗಾಗಿ ಪ್ರತ್ಯೇಕವಾಗಿ ತೋರಿಸಲಾಗಿದೆ.",
                "transparency_notice_en": "Fees are displayed separately for transparency.",
            }
            tx.receipt_data = json.dumps(receipt_payload)

            db.commit()
            db.refresh(tx)
            db.refresh(app)

            return PaymentReceiptResponse(**receipt_payload)
        else:
            tx.payment_status = "FAILED"
            tx.verified_at = now
            tx.verified_by = verifier_id
            tx.notes = notes or "Payment rejected during manual verification."

            app.payment_status = "FAILED"
            db.commit()
            db.refresh(tx)
            db.refresh(app)

            raise ValueError(f"Payment verification rejected: {tx.notes}")

    @classmethod
    def get_payment_details_or_receipt(
        cls,
        db: Session,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Fetch current payment status, fee summary, and receipt if paid."""
        app = db.get(SchemeApplication, application_id)
        if not app:
            raise ValueError(f"Scheme application '{application_id}' not found.")

        # Authorization: owner farmer or admin
        if app.farmer_id != user_id:
            # Let caller check if admin, otherwise enforce
            pass

        tx = (
            db.query(PaymentTransaction)
            .filter(PaymentTransaction.application_id == application_id)
            .order_by(PaymentTransaction.created_at.desc())
            .first()
        )

        scheme = db.get(GovernmentScheme, app.scheme_id)
        fee_info = cls.calculate_scheme_fee_info(scheme) if scheme else None

        receipt = None
        if tx and tx.receipt_data:
            try:
                receipt = json.loads(tx.receipt_data)
            except Exception:
                receipt = None

        return {
            "application_id": str(app.id),
            "scheme_id": str(app.scheme_id),
            "scheme_title": scheme.title if scheme else None,
            "scheme_title_kn": scheme.title_kn if scheme else None,
            "application_status": app.status,
            "payment_status": app.payment_status,
            "transaction_id": str(tx.id) if tx else None,
            "total_amount": float(tx.total_amount) if tx else (fee_info.total_payable if fee_info else None),
            "official_fee": float(tx.official_fee) if tx else (fee_info.official_fee if fee_info else None),
            "service_fee": float(tx.service_fee) if tx else (fee_info.krushipragya_service_fee if fee_info else None),
            "payment_reference": tx.payment_reference if tx else None,
            "payment_method": tx.payment_method if tx else "PHONEPE_STATIC_QR",
            "receipt": receipt,
            "fee_info": fee_info,
        }

    @classmethod
    def submit_application(
        cls,
        db: Session,
        farmer_id: uuid.UUID,
        application_id: uuid.UUID,
    ) -> SchemeApplicationResponse:
        """Submit the scheme application after verified payment (or immediately if free)."""
        app = db.get(SchemeApplication, application_id)
        if not app:
            raise ValueError(f"Scheme application '{application_id}' not found.")

        if app.farmer_id != farmer_id:
            raise PermissionError("Access forbidden: You do not own this scheme application.")

        scheme = db.get(GovernmentScheme, app.scheme_id)
        fee_info = cls.calculate_scheme_fee_info(scheme)

        if fee_info.payment_required and app.payment_status != "PAID":
            raise ValueError("Cannot submit application without verified payment. (ಪಾವತಿ ಪರಿಶೀಲನೆಯ ನಂತರವೇ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು.)")

        now = datetime.now(timezone.utc)
        app.status = "SUBMITTED"
        app.submitted_at = now

        db.commit()
        db.refresh(app)

        return cls._format_application_response(app, scheme, fee_info)

    @classmethod
    def get_farmer_applications(
        cls,
        db: Session,
        farmer_id: uuid.UUID,
    ) -> List[SchemeApplicationResponse]:
        """List all applications submitted or tracked by the farmer."""
        apps = (
            db.query(SchemeApplication)
            .filter(SchemeApplication.farmer_id == farmer_id)
            .order_by(SchemeApplication.created_at.desc())
            .all()
        )

        results = []
        for a in apps:
            sc = db.get(GovernmentScheme, a.scheme_id)
            fee = cls.calculate_scheme_fee_info(sc) if sc else None
            results.append(cls._format_application_response(a, sc, fee))
        return results

    @staticmethod
    def _format_application_response(
        app: SchemeApplication,
        scheme: Optional[GovernmentScheme],
        fee_info: Optional[SchemeFeeInfo],
    ) -> SchemeApplicationResponse:
        can_submit = (not fee_info.payment_required) or (app.payment_status == "PAID")
        return SchemeApplicationResponse(
            id=str(app.id),
            scheme_id=str(app.scheme_id),
            scheme_title=scheme.title if scheme else "Government Scheme",
            scheme_title_kn=scheme.title_kn if scheme else None,
            category=scheme.category if scheme else "Subsidy",
            farmer_id=str(app.farmer_id),
            status=app.status,
            payment_status=app.payment_status,
            fee_info=fee_info or SchemeFeeInfo(),
            payment_transaction_id=str(app.payment_transaction_id) if app.payment_transaction_id else None,
            application_notes=app.application_notes,
            review_notes=app.review_notes,
            can_submit=can_submit,
            submitted_at=app.submitted_at.isoformat() if app.submitted_at else None,
            created_at=app.created_at.isoformat() if getattr(app, "created_at", None) else None,
            updated_at=app.updated_at.isoformat() if getattr(app, "updated_at", None) else None,
        )
