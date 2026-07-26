"""Tunnel de paiement : sélection de l'offre, redirection fournisseur, webhooks."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_session
from app.models import ORDER_PAID, ORDER_PENDING, STATUS_COMPLETED
from app.security import sign_token
from app.services import assessments as svc
from app.services.payments import (
    PaymentError,
    available_providers,
    get_provider,
    resolve_provider,
)
from app.services.pricing import PLANS_BY_CODE, normalise_currency, price_for
from app.templating import render

logger = logging.getLogger("datamaturity.checkout")
router = APIRouter(prefix="/paiement", tags=["paiement"])

PAYABLE = {"standard", "premium"}


# ---------------------------------------------------------------------------
#  IMPORTANT — ordre d'enregistrement des routes
#  FastAPI résout les routes dans l'ordre de déclaration. Les chemins fixes
#  (/webhook/..., /{id}/retour, /{id}/instructions) doivent donc être déclarés
#  AVANT le chemin générique /{public_id}/{plan_code}, sinon « instructions »
#  serait interprété comme un code d'offre.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#  Webhooks
# ---------------------------------------------------------------------------


async def _handle_webhook(provider_code: str, request: Request, session: Session) -> JSONResponse:
    provider = get_provider(provider_code)
    body = await request.body()
    try:
        event = provider.parse_webhook(body, dict(request.headers))
    except PaymentError as exc:
        logger.warning("Webhook %s rejeté : %s", provider_code, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    order = svc.get_order_by_reference(session, event.order_reference)
    if order is None:
        logger.warning("Webhook %s : commande %s inconnue", provider_code, event.order_reference)
        return JSONResponse({"status": "ignored", "reason": "commande inconnue"}, status_code=200)

    if event.status == "paid":
        if event.amount_minor and event.amount_minor != order.amount_minor:
            logger.error(
                "Montant incohérent sur %s : attendu %s, reçu %s",
                order.reference, order.amount_minor, event.amount_minor,
            )
            svc.log(session, "order.amount_mismatch", order.reference,
                    {"expected": order.amount_minor, "received": event.amount_minor},
                    actor=f"webhook:{provider_code}")
            return JSONResponse({"status": "rejected", "reason": "montant incohérent"}, status_code=200)
        svc.mark_order_paid(
            session, order,
            provider_reference=event.provider_reference,
            actor=f"webhook:{provider_code}",
            detail=event.raw,
        )
    elif event.status in {"failed", "cancelled"}:
        svc.mark_order_status(session, order, event.status, actor=f"webhook:{provider_code}")

    return JSONResponse({"status": "ok", "order": order.reference, "state": order.status})


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)):
    return await _handle_webhook("stripe", request, session)


@router.post("/webhook/cinetpay")
async def cinetpay_webhook(request: Request, session: Session = Depends(get_session)):
    return await _handle_webhook("cinetpay", request, session)


# ---------------------------------------------------------------------------
#  Pages de retour
# ---------------------------------------------------------------------------


@router.get("/{order_public_id}/instructions")
async def instructions(
    request: Request, order_public_id: str, session: Session = Depends(get_session)
):
    order = svc.get_order_by_public_id(session, order_public_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    return render(
        request,
        "payment_instructions.html",
        {"order": order, "assessment": order.assessment, "plan": PLANS_BY_CODE.get(order.plan_code)},
    )


@router.get("/{order_public_id}/retour")
async def payment_return(
    request: Request, order_public_id: str, session: Session = Depends(get_session)
):
    """Page de retour après paiement.

    Le statut n'est jamais déduit de cette redirection : seul le webhook (ou une
    vérification serveur explicite) fait foi. La page reflète l'état réel connu.
    """
    order = svc.get_order_by_public_id(session, order_public_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")

    if order.status == ORDER_PENDING and order.provider == "cinetpay":
        # Vérification synchrone : l'utilisateur revient souvent avant la notification.
        try:
            provider = get_provider("cinetpay")
            result = provider.check_transaction(order.reference)  # type: ignore[attr-defined]
            if str(result.get("code")) == "00":
                svc.mark_order_paid(session, order, actor="retour_client",
                                    detail={"verification": "synchrone"})
        except PaymentError as exc:
            logger.warning("Vérification CinetPay impossible : %s", exc)

    if order.status == ORDER_PAID:
        from app.routers.public import grant_access

        grant_access(request, order.assessment)

    return render(
        request,
        "payment_return.html",
        {
            "order": order,
            "assessment": order.assessment,
            "plan": PLANS_BY_CODE.get(order.plan_code),
            "paid": order.status == ORDER_PAID,
            "report_token": sign_token(order.assessment.public_id) if order.status == ORDER_PAID else "",
        },
    )


@router.get("/{order_public_id}/annule")
async def payment_cancelled(
    request: Request, order_public_id: str, session: Session = Depends(get_session)
):
    order = svc.get_order_by_public_id(session, order_public_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    if order.status == ORDER_PENDING:
        svc.mark_order_status(session, order, "cancelled", actor="client")
    return render(
        request,
        "payment_return.html",
        {
            "order": order,
            "assessment": order.assessment,
            "plan": PLANS_BY_CODE.get(order.plan_code),
            "paid": False,
            "cancelled": True,
            "report_token": "",
        },
    )


# ---------------------------------------------------------------------------
#  Création de la commande
# ---------------------------------------------------------------------------


@router.get("/{public_id}/{plan_code}")
async def checkout_page(
    request: Request, public_id: str, plan_code: str, session: Session = Depends(get_session)
):
    if plan_code not in PAYABLE:
        raise HTTPException(status_code=404, detail="Offre inconnue.")
    assessment = svc.get_assessment(session, public_id)
    if assessment is None or assessment.status != STATUS_COMPLETED:
        raise HTTPException(status_code=404, detail="Évaluation introuvable ou incomplète.")

    from app.routers.public import resolve_currency

    currency = resolve_currency(request, assessment.currency)
    return render(
        request,
        "checkout.html",
        {
            "assessment": assessment,
            "plan": PLANS_BY_CODE[plan_code],
            "price": price_for(plan_code, currency, session=session),
            "currency": currency,
            "providers": available_providers(currency),
        },
    )


@router.post("/{public_id}/{plan_code}")
async def checkout_submit(
    request: Request,
    public_id: str,
    plan_code: str,
    currency: str = Form(...),
    provider: str = Form("manual"),
    session: Session = Depends(get_session),
):
    if plan_code not in PAYABLE:
        raise HTTPException(status_code=404, detail="Offre inconnue.")
    assessment = svc.get_assessment(session, public_id)
    if assessment is None or assessment.status != STATUS_COMPLETED:
        raise HTTPException(status_code=404, detail="Évaluation introuvable ou incomplète.")

    currency = normalise_currency(currency)
    selected = resolve_provider(currency, provider)
    order = svc.create_order(session, assessment, plan_code, currency, selected.code)

    base = settings.base_url.rstrip("/")
    success_url = f"{base}/paiement/{order.public_id}/retour"
    cancel_url = f"{base}/paiement/{order.public_id}/annule"

    try:
        payment = selected.create_session(
            order, assessment, success_url=success_url, cancel_url=cancel_url
        )
    except PaymentError as exc:
        logger.warning("Initialisation de paiement refusée (%s) : %s", selected.code, exc)
        return render(
            request,
            "checkout.html",
            {
                "assessment": assessment,
                "plan": PLANS_BY_CODE[plan_code],
                "price": price_for(plan_code, currency, session=session),
                "currency": currency,
                "providers": available_providers(currency),
                "errors": [str(exc)],
            },
            status_code=502,
        )

    meta = order.meta
    meta.update({"provider_payload": payment.raw})
    order.meta = meta
    order.provider_reference = payment.provider_reference
    session.flush()

    if payment.redirect_url:
        return RedirectResponse(payment.redirect_url, status_code=303)
    return RedirectResponse(
        payment.instructions_url or f"/paiement/{order.public_id}/instructions", status_code=303
    )
