"""Provider-agnostic Payment Provider abstraction for secure, server-side marketplace transactions.

Supports:
- PayU Hosted Checkout / Web API with server-side SHA-512 request hash and reverse response hash verification.
- Razorpay gateway integration with HMAC-SHA256 signature verification (maintained but inactive by default).
"""
from abc import ABC, abstractmethod
from decimal import Decimal
import hashlib
import hmac
import logging
from typing import Any, Dict, Optional
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


class PaymentProvider(ABC):
    """Abstract interface for payment gateway providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Normalized provider identifier (e.g. 'payu', 'razorpay')."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials are fully configured."""
        pass

    @abstractmethod
    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        receipt: str,
        customer_info: Optional[Dict[str, Any]] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a payment order / transaction request at the payment gateway."""
        pass

    @abstractmethod
    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Cryptographically verify payment signature from client."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        body: bytes,
        signature: str,
    ) -> bool:
        """Verify webhook signature from gateway server."""
        pass


class PayUPaymentProvider(PaymentProvider):
    """PayU Hosted Checkout / Web API payment provider implementation."""

    def __init__(
        self,
        merchant_key: Optional[str] = None,
        merchant_salt: Optional[str] = None,
        environment: Optional[str] = None,
    ):
        self.merchant_key = merchant_key or settings.PAYU_MERCHANT_KEY
        self.merchant_salt = merchant_salt or settings.PAYU_MERCHANT_SALT
        self.environment = (environment or settings.PAYU_ENVIRONMENT or "test").lower()

    @property
    def provider_name(self) -> str:
        return "payu"

    def is_configured(self) -> bool:
        """Return True only if PayU merchant key and salt are configured."""
        return bool(self.merchant_key and self.merchant_salt)

    @property
    def action_url(self) -> str:
        """PayU payment post URL based on environment."""
        if self.environment == "production":
            return "https://secure.payu.in/_payment"
        return "https://test.payu.in/_payment"

    def generate_hash(
        self,
        txnid: str,
        amount: Decimal,
        productinfo: str,
        firstname: str,
        email: str,
        udf1: str = "",
        udf2: str = "",
        udf3: str = "",
        udf4: str = "",
        udf5: str = "",
    ) -> str:
        """Generate PayU SHA-512 payment request hash.

        Formula:
        sha512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||SALT)
        """
        if not self.is_configured() or not self.merchant_salt or not self.merchant_key:
            raise RuntimeError("PayU provider is not configured with merchant key and salt.")

        amount_str = f"{amount:.2f}"
        hash_string = (
            f"{self.merchant_key}|{txnid}|{amount_str}|{productinfo}|{firstname}|{email}|"
            f"{udf1}|{udf2}|{udf3}|{udf4}|{udf5}||||||{self.merchant_salt}"
        )
        return hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()

    def verify_payment_hash(self, data: Dict[str, Any]) -> bool:
        """Verify PayU payment response / callback / webhook hash.

        Formula:
        If additionalCharges:
          sha512(additionalCharges|SALT|status||||||udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key)
        Else:
          sha512(SALT|status||||||udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key)
        """
        if not self.is_configured() or not self.merchant_salt or not self.merchant_key:
            return False

        received_hash = data.get("hash")
        if not received_hash:
            return False

        status = data.get("status", "")
        txnid = data.get("txnid", "")
        raw_amount = data.get("amount", "")
        try:
            amount_str = f"{float(raw_amount):.2f}"
        except (ValueError, TypeError):
            amount_str = str(raw_amount)

        productinfo = data.get("productinfo", "")
        firstname = data.get("firstname", "")
        email = data.get("email", "")
        udf1 = data.get("udf1", "")
        udf2 = data.get("udf2", "")
        udf3 = data.get("udf3", "")
        udf4 = data.get("udf4", "")
        udf5 = data.get("udf5", "")
        additional_charges = data.get("additionalCharges")

        if additional_charges:
            hash_string = (
                f"{additional_charges}|{self.merchant_salt}|{status}||||||"
                f"{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|{email}|{firstname}|{productinfo}|{amount_str}|{txnid}|{self.merchant_key}"
            )
        else:
            hash_string = (
                f"{self.merchant_salt}|{status}||||||"
                f"{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|{email}|{firstname}|{productinfo}|{amount_str}|{txnid}|{self.merchant_key}"
            )

        expected_hash = hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()
        return hmac.compare_digest(expected_hash, received_hash.lower())

    def generate_response_hash(
        self,
        txnid: str,
        amount: Any,
        productinfo: str,
        firstname: str,
        email: str,
        status: str = "success",
        udf1: str = "",
        udf2: str = "",
        udf3: str = "",
        udf4: str = "",
        udf5: str = "",
        additional_charges: Optional[str] = None,
    ) -> str:
        """Generate expected response hash matching PayU reverse hash formula."""
        if not self.merchant_salt or not self.merchant_key:
            raise RuntimeError("PayU provider is not configured.")

        try:
            amount_str = f"{float(amount):.2f}"
        except (ValueError, TypeError):
            amount_str = str(amount)

        if additional_charges:
            hash_string = (
                f"{additional_charges}|{self.merchant_salt}|{status}||||||"
                f"{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|{email}|{firstname}|{productinfo}|{amount_str}|{txnid}|{self.merchant_key}"
            )
        else:
            hash_string = (
                f"{self.merchant_salt}|{status}||||||"
                f"{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|{email}|{firstname}|{productinfo}|{amount_str}|{txnid}|{self.merchant_key}"
            )

        return hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()

    async def create_order(
        self,
        amount: Decimal,
        currency: str = "INR",
        receipt: str = "",
        customer_info: Optional[Dict[str, Any]] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create PayU checkout order payload without exposing merchant salt."""
        if not self.is_configured():
            raise RuntimeError("PayU payment provider is not configured.")

        cust = customer_info or {}
        txnid = receipt or f"tx_{uuid.uuid4().hex[:16]}"
        productinfo = (notes or {}).get("crop_name") or "Produce Listing Purchase"
        firstname = cust.get("name") or "Buyer"
        email = cust.get("email") or "buyer@krushipragya.in"
        phone = cust.get("phone") or "9876543210"

        udf1 = str((notes or {}).get("offer_id", ""))
        udf2 = str((notes or {}).get("listing_id", ""))
        udf3 = str((notes or {}).get("buyer_id", ""))
        udf4 = str((notes or {}).get("farmer_id", ""))
        udf5 = ""

        amount_str = f"{amount:.2f}"
        payment_hash = self.generate_hash(
            txnid=txnid,
            amount=amount,
            productinfo=productinfo,
            firstname=firstname,
            email=email,
            udf1=udf1,
            udf2=udf2,
            udf3=udf3,
            udf4=udf4,
            udf5=udf5,
        )

        checkout_data = {
            "action_url": self.action_url,
            "params": {
                "key": self.merchant_key,
                "txnid": txnid,
                "amount": amount_str,
                "productinfo": productinfo,
                "firstname": firstname,
                "email": email,
                "phone": phone,
                "surl": "https://krushipragya.in/api/v1/market/payments/payu-callback",
                "furl": "https://krushipragya.in/api/v1/market/payments/payu-callback",
                "hash": payment_hash,
                "udf1": udf1,
                "udf2": udf2,
                "udf3": udf3,
                "udf4": udf4,
                "udf5": udf5,
            },
        }

        return {
            "id": txnid,
            "provider": "payu",
            "checkout_data": checkout_data,
        }

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verify PayU signature using hash data dictionary."""
        # Generic signature verification delegation for PayU
        return self.verify_payment_hash({
            "txnid": order_id,
            "mihpayid": payment_id,
            "hash": signature,
            "status": "success",
        })

    def verify_webhook_signature(
        self,
        body: bytes,
        signature: str,
    ) -> bool:
        """Verify PayU webhook signature."""
        import json
        try:
            data = json.loads(body.decode("utf-8"))
            return self.verify_payment_hash(data)
        except Exception:
            return False


class RazorpayPaymentProvider(PaymentProvider):
    """Production Razorpay payment provider implementation (available but inactive)."""

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET

    @property
    def provider_name(self) -> str:
        return "razorpay"

    def is_configured(self) -> bool:
        """Return True if Razorpay key and secret are configured."""
        return bool(self.key_id and self.key_secret)

    async def create_order(
        self,
        amount: Decimal,
        currency: str = "INR",
        receipt: str = "",
        customer_info: Optional[Dict[str, Any]] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create order in Razorpay (amount in paise)."""
        if not self.is_configured():
            raise RuntimeError("Razorpay payment provider is not configured.")

        amount_paise = int(amount * 100)
        payload = {
            "amount": amount_paise,
            "currency": currency.upper(),
            "receipt": receipt[:40] if receipt else "kp_receipt",
            "notes": notes or {},
            "payment_capture": 1,
        }

        import httpx
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.razorpay.com/v1/orders",
                auth=(self.key_id, self.key_secret),
                json=payload,
            )
            if resp.status_code not in (200, 201):
                logger.error("Razorpay order creation failed: %s %s", resp.status_code, resp.text)
                raise RuntimeError(f"Razorpay order creation error: {resp.text}")
            res_json = resp.json()
            res_json["provider"] = "razorpay"
            return res_json

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verify Razorpay payment signature using HMAC-SHA256."""
        if not self.is_configured() or not self.key_secret:
            logger.warning("Cannot verify signature: Razorpay secret not configured.")
            return False

        msg = f"{order_id}|{payment_id}".encode("utf-8")
        expected_sig = hmac.new(
            self.key_secret.encode("utf-8"),
            msg,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature)

    def verify_webhook_signature(
        self,
        body: bytes,
        signature: str,
    ) -> bool:
        """Verify Razorpay webhook signature."""
        secret = self.webhook_secret or self.key_secret
        if not secret:
            return False

        expected_sig = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature)


def get_payment_provider() -> PaymentProvider:
    """Dependency provider returning the configured PaymentProvider."""
    provider_name = (settings.PAYMENT_PROVIDER or "payu").strip().lower()
    if provider_name == "razorpay":
        return RazorpayPaymentProvider()
    return PayUPaymentProvider()
