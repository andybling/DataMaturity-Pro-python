"""Contrat commun aux fournisseurs de paiement."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol

from app.models import Assessment, Order


@dataclass
class PaymentSession:
    """Résultat de l'initialisation d'un paiement."""

    provider: str
    provider_reference: str
    redirect_url: Optional[str] = None      # page de paiement externe
    instructions_url: Optional[str] = None  # page interne d'instructions (paiement manuel)
    raw: dict = field(default_factory=dict)


@dataclass
class PaymentEvent:
    """Événement normalisé issu d'un webhook fournisseur."""

    provider: str
    order_reference: str
    status: str                # paid | failed | cancelled | pending
    provider_reference: str = ""
    amount_minor: Optional[int] = None
    currency: str = ""
    raw: dict = field(default_factory=dict)


class PaymentError(RuntimeError):
    """Erreur fonctionnelle remontée à l'utilisateur sans détail technique."""


class PaymentProvider(Protocol):
    code: str
    label: str

    def supports(self, currency: str) -> bool: ...

    def create_session(
        self, order: Order, assessment: Assessment, *, success_url: str, cancel_url: str
    ) -> PaymentSession: ...

    def parse_webhook(self, body: bytes, headers: dict) -> PaymentEvent: ...
