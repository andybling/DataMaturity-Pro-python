"""Sélection des fournisseurs de paiement et robustesse des webhooks."""

from app.services.payments import available_providers, default_provider, resolve_provider
from app.services.payments.cinetpay_provider import CinetPayProvider
from app.services.payments.stripe_provider import StripeProvider


def test_stripe_ne_traite_pas_le_franc_cfa():
    provider = StripeProvider(secret_key="sk_test_x", webhook_secret="whsec_x")
    assert provider.supports("EUR")
    assert provider.supports("USD")
    assert not provider.supports("XOF")


def test_cinetpay_ne_traite_que_le_franc_cfa():
    provider = CinetPayProvider(api_key="k", site_id="1", secret_key="s")
    assert provider.supports("XOF")
    assert not provider.supports("EUR")


def test_repli_sur_le_circuit_manuel_sans_configuration():
    """Sans clés d'API, l'application reste vendable : virement et facture."""
    for currency in ("XOF", "EUR", "USD"):
        providers = available_providers(currency)
        assert providers, currency
        assert default_provider(currency).code == "manual"


def test_fournisseur_demande_ignore_si_indisponible():
    assert resolve_provider("XOF", "stripe").code == "manual"


def test_webhook_stripe_sans_signature_rejete(client):
    response = client.post("/paiement/webhook/stripe", content=b"{}")
    assert response.status_code == 400


def test_webhook_cinetpay_sans_transaction_rejete(client):
    response = client.post("/paiement/webhook/cinetpay", content=b"")
    assert response.status_code == 400


def test_idempotence_du_marquage_paye():
    from app.database import session_scope
    from app.models import ORDER_PAID, Assessment, Order
    from app.services import assessments as svc

    with session_scope() as session:
        assessment = svc.create_assessment(
            session,
            {"company_name": "Idempotence SARL", "sector": "Technologie & Services numériques",
             "country": "Sénégal", "company_size": "10-49", "contact_name": "Test",
             "contact_email": "test@example.com", "consent": True, "currency": "XOF"},
        )
        order = svc.create_order(session, assessment, "standard", "XOF", "manual")
        svc.mark_order_paid(session, order, actor="test")
        first_paid_at = order.paid_at
        svc.mark_order_paid(session, order, actor="test")
        assert order.status == ORDER_PAID
        assert order.paid_at == first_paid_at


def test_jetons_signes():
    from app.security import sign_token, verify_token

    token = sign_token("abc123")
    assert verify_token(token) == "abc123"
    assert verify_token(token + "x") is None
    assert verify_token("nimporte.quoi") is None
    assert verify_token(sign_token("abc123", ttl_seconds=-10)) is None
