"""Paiement par carte bancaire via Stripe Checkout (EUR, USD).

Stripe ne traite pas le franc CFA : les paiements en XOF passent par CinetPay
ou par le circuit manuel. La sélection est faite dans app/services/payments/__init__.py.
"""

from __future__ import annotations

from typing import Optional

from app.config import settings
from app.models import Assessment, Order
from app.services.payments.base import PaymentError, PaymentEvent, PaymentSession
from app.services.pricing import PLANS_BY_CODE

SUPPORTED = {"EUR", "USD"}


class StripeProvider:
    code = "stripe"
    label = "Carte bancaire (Visa / Mastercard)"

    def __init__(self, secret_key: Optional[str] = None, webhook_secret: Optional[str] = None):
        self.secret_key = secret_key if secret_key is not None else settings.stripe_secret_key
        self.webhook_secret = (
            webhook_secret if webhook_secret is not None else settings.stripe_webhook_secret
        )

    @property
    def enabled(self) -> bool:
        return bool(self.secret_key)

    def supports(self, currency: str) -> bool:
        return self.enabled and currency.upper() in SUPPORTED

    # -- initialisation ----------------------------------------------------
    def create_session(
        self, order: Order, assessment: Assessment, *, success_url: str, cancel_url: str
    ) -> PaymentSession:
        if not self.enabled:
            raise PaymentError("Le paiement par carte n'est pas configuré.")
        import stripe

        stripe.api_key = self.secret_key
        plan = PLANS_BY_CODE.get(order.plan_code)
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                client_reference_id=order.reference,
                customer_email=order.customer_email or assessment.contact_email or None,
                line_items=[
                    {
                        "quantity": 1,
                        "price_data": {
                            "currency": order.currency.lower(),
                            "unit_amount": order.amount_minor,
                            "product_data": {
                                "name": f"{settings.brand_name} — {plan.name if plan else order.plan_code}",
                                "description": (
                                    f"Rapport de maturité data — {assessment.company_name}"
                                ),
                            },
                        },
                    }
                ],
                metadata={
                    "order_reference": order.reference,
                    "assessment_public_id": assessment.public_id,
                    "plan_code": order.plan_code,
                    "company": assessment.company_name[:200],
                },
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except Exception as exc:  # pragma: no cover - dépend du réseau
            raise PaymentError("Stripe a refusé l'initialisation du paiement.") from exc

        return PaymentSession(
            provider=self.code,
            provider_reference=session.get("id", ""),
            redirect_url=session.get("url"),
            raw={"id": session.get("id"), "payment_status": session.get("payment_status")},
        )

    # -- webhook -----------------------------------------------------------
    def parse_webhook(self, body: bytes, headers: dict) -> PaymentEvent:
        import stripe

        signature = headers.get("stripe-signature") or headers.get("Stripe-Signature", "")
        if not self.webhook_secret:
            raise PaymentError("Webhook Stripe non configuré (STRIPE_WEBHOOK_SECRET manquant).")
        try:
            event = stripe.Webhook.construct_event(body, signature, self.webhook_secret)
        except Exception as exc:
            raise PaymentError("Signature de webhook Stripe invalide.") from exc

        obj = event["data"]["object"]
        event_type = event["type"]
        reference = (obj.get("metadata") or {}).get("order_reference") or obj.get(
            "client_reference_id", ""
        )

        status = "pending"
        if event_type == "checkout.session.completed" and obj.get("payment_status") == "paid":
            status = "paid"
        elif event_type in {"checkout.session.async_payment_failed", "payment_intent.payment_failed"}:
            status = "failed"
        elif event_type == "checkout.session.expired":
            status = "cancelled"

        return PaymentEvent(
            provider=self.code,
            order_reference=reference,
            status=status,
            provider_reference=obj.get("id", ""),
            amount_minor=obj.get("amount_total"),
            currency=(obj.get("currency") or "").upper(),
            raw={"type": event_type},
        )
