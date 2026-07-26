"""Paiement Mobile Money et carte via CinetPay (XOF).

CinetPay couvre Orange Money, MTN, Moov et Wave sur la zone UEMOA, ce qui en
fait le canal naturel pour les paiements en FCFA. La notification serveur est
volontairement re-vérifiée par un appel `/v2/payment/check` : c'est la seule
source de vérité, une notification seule n'étant pas une preuve de paiement.
"""

from __future__ import annotations

import json
from typing import Optional
from urllib.parse import parse_qs

import httpx

from app.config import settings
from app.models import Assessment, Order
from app.services.payments.base import PaymentError, PaymentEvent, PaymentSession

API_BASE = "https://api-checkout.cinetpay.com/v2"
SUPPORTED = {"XOF"}


class CinetPayProvider:
    code = "cinetpay"
    label = "Mobile Money (Orange, MTN, Moov, Wave) et carte"

    def __init__(
        self,
        api_key: Optional[str] = None,
        site_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        timeout: float = 20.0,
    ):
        self.api_key = api_key if api_key is not None else settings.cinetpay_api_key
        self.site_id = site_id if site_id is not None else settings.cinetpay_site_id
        self.secret_key = secret_key if secret_key is not None else settings.cinetpay_secret_key
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.site_id)

    def supports(self, currency: str) -> bool:
        return self.enabled and currency.upper() in SUPPORTED

    # -- initialisation ----------------------------------------------------
    def create_session(
        self, order: Order, assessment: Assessment, *, success_url: str, cancel_url: str
    ) -> PaymentSession:
        if not self.enabled:
            raise PaymentError("Le paiement Mobile Money n'est pas configuré.")

        payload = {
            "apikey": self.api_key,
            "site_id": self.site_id,
            "transaction_id": order.reference,
            "amount": int(order.amount_minor),  # XOF : pas de sous-unité
            "currency": "XOF",
            "description": f"Rapport maturite data - {assessment.company_name}"[:255],
            "customer_name": (assessment.contact_name or "Client")[:100],
            "customer_email": order.customer_email or assessment.contact_email,
            "customer_phone_number": assessment.contact_phone or "",
            "notify_url": f"{settings.base_url.rstrip('/')}/paiement/webhook/cinetpay",
            "return_url": success_url,
            "channels": "ALL",
            "metadata": json.dumps(
                {"assessment": assessment.public_id, "plan": order.plan_code}, ensure_ascii=False
            ),
            "lang": "fr",
        }
        try:
            response = httpx.post(f"{API_BASE}/payment", json=payload, timeout=self.timeout)
            data = response.json()
        except Exception as exc:  # pragma: no cover - dépend du réseau
            raise PaymentError("CinetPay est momentanément injoignable.") from exc

        if str(data.get("code")) != "201":
            raise PaymentError(
                f"CinetPay a refusé la transaction : {data.get('message', 'erreur inconnue')}"
            )

        body = data.get("data", {})
        return PaymentSession(
            provider=self.code,
            provider_reference=body.get("payment_token", ""),
            redirect_url=body.get("payment_url"),
            raw={"code": data.get("code"), "token": body.get("payment_token")},
        )

    # -- vérification ------------------------------------------------------
    def check_transaction(self, transaction_id: str) -> dict:
        """Interroge CinetPay sur l'état réel d'une transaction."""
        payload = {"apikey": self.api_key, "site_id": self.site_id, "transaction_id": transaction_id}
        try:
            response = httpx.post(f"{API_BASE}/payment/check", json=payload, timeout=self.timeout)
            return response.json()
        except Exception as exc:  # pragma: no cover - dépend du réseau
            raise PaymentError("Vérification CinetPay impossible.") from exc

    def parse_webhook(self, body: bytes, headers: dict) -> PaymentEvent:
        """CinetPay notifie en `application/x-www-form-urlencoded`.

        On extrait l'identifiant de transaction puis on re-vérifie systématiquement
        l'état auprès de l'API : la notification ne fait pas foi.
        """
        raw_text = body.decode("utf-8", errors="replace")
        try:
            fields = {k: v[0] for k, v in parse_qs(raw_text).items()}
        except Exception:
            fields = {}
        if not fields:
            try:
                fields = json.loads(raw_text or "{}")
            except ValueError:
                fields = {}

        transaction_id = fields.get("cpm_trans_id") or fields.get("transaction_id") or ""
        if not transaction_id:
            raise PaymentError("Notification CinetPay sans identifiant de transaction.")

        verification = self.check_transaction(transaction_id)
        data = verification.get("data", {})
        code = str(verification.get("code"))
        status_map = {"00": "paid", "600": "failed", "602": "failed", "623": "pending"}
        status = status_map.get(code, "failed" if code != "00" else "paid")

        return PaymentEvent(
            provider=self.code,
            order_reference=transaction_id,
            status=status,
            provider_reference=str(data.get("payment_token") or fields.get("cpm_payid", "")),
            amount_minor=int(float(data.get("amount", 0) or 0)),
            currency=(data.get("currency") or "XOF").upper(),
            raw={"code": code, "message": verification.get("message"), "method": data.get("payment_method")},
        )
