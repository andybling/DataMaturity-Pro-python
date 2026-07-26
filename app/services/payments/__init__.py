"""Sélection du fournisseur de paiement selon la devise et la configuration."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.services.payments.base import (
    PaymentError,
    PaymentEvent,
    PaymentProvider,
    PaymentSession,
)
from app.services.payments.cinetpay_provider import CinetPayProvider
from app.services.payments.manual_provider import ManualProvider
from app.services.payments.stripe_provider import StripeProvider

_stripe = StripeProvider()
_cinetpay = CinetPayProvider()
_manual = ManualProvider()

PROVIDERS: Dict[str, PaymentProvider] = {
    _stripe.code: _stripe,
    _cinetpay.code: _cinetpay,
    _manual.code: _manual,
}

# Ordre de préférence par devise : le premier fournisseur actif est retenu.
PREFERENCE: Dict[str, List[str]] = {
    "XOF": ["cinetpay", "manual"],
    "EUR": ["stripe", "manual"],
    "USD": ["stripe", "manual"],
}


def get_provider(code: str) -> PaymentProvider:
    provider = PROVIDERS.get(code)
    if provider is None:
        raise PaymentError(f"Moyen de paiement inconnu : {code}")
    return provider


def available_providers(currency: str) -> List[PaymentProvider]:
    """Fournisseurs réellement utilisables pour cette devise."""
    codes = PREFERENCE.get(currency.upper(), ["manual"])
    return [PROVIDERS[c] for c in codes if PROVIDERS[c].supports(currency)]


def default_provider(currency: str) -> PaymentProvider:
    providers = available_providers(currency)
    return providers[0] if providers else _manual


def resolve_provider(currency: str, requested: Optional[str] = None) -> PaymentProvider:
    """Retient le fournisseur demandé s'il est utilisable, sinon le fournisseur par défaut."""
    if requested:
        provider = PROVIDERS.get(requested)
        if provider is not None and provider.supports(currency):
            return provider
    return default_provider(currency)


__all__ = [
    "PaymentError",
    "PaymentEvent",
    "PaymentProvider",
    "PaymentSession",
    "PROVIDERS",
    "available_providers",
    "default_provider",
    "get_provider",
    "resolve_provider",
]
