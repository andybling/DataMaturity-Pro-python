"""Circuit de paiement manuel : virement, dépôt Mobile Money direct, facture.

Indispensable en pratique sur le marché B2B africain : beaucoup d'organisations
paient sur facture après bon de commande. La commande est créée en attente,
l'administrateur la valide depuis la console, ce qui déclenche l'accès au rapport.
"""

from __future__ import annotations

from app.config import settings
from app.models import Assessment, Order
from app.services.payments.base import PaymentError, PaymentEvent, PaymentSession


class ManualProvider:
    code = "manual"
    label = "Virement bancaire, Mobile Money direct ou facture"

    def supports(self, currency: str) -> bool:
        return True  # toujours disponible, quelle que soit la devise

    def create_session(
        self, order: Order, assessment: Assessment, *, success_url: str, cancel_url: str
    ) -> PaymentSession:
        return PaymentSession(
            provider=self.code,
            provider_reference=order.reference,
            instructions_url=f"/paiement/{order.public_id}/instructions",
            raw={"contact": settings.contact_email, "whatsapp": settings.whatsapp_url},
        )

    def parse_webhook(self, body: bytes, headers: dict) -> PaymentEvent:  # pragma: no cover
        raise PaymentError("Le circuit manuel ne reçoit pas de notification automatique.")
