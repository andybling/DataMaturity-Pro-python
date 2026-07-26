"""Cas d'usage métier autour des évaluations et des commandes."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Mapping, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.grid import ALL_CRITERIA
from app.models import (
    ORDER_PAID,
    ORDER_PENDING,
    STATUS_COMPLETED,
    STATUS_DRAFT,
    Assessment,
    AuditLog,
    Order,
)
from app.services.analysis import Analysis, build_analysis
from app.services.pricing import normalise_currency, price_for
from app.services.scoring import ScoreResult, compute_score, normalise_answers


def new_reference() -> str:
    """Référence de commande lisible : DMP-AAAAMM-XXXXXX."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m")
    return f"DMP-{stamp}-{secrets.token_hex(3).upper()}"


# ---------------------------------------------------------------------------
#  Évaluations
# ---------------------------------------------------------------------------


def create_assessment(session: Session, payload: Mapping[str, object]) -> Assessment:
    """Crée une évaluation à l'état brouillon depuis le formulaire d'identité."""
    assessment = Assessment(
        company_name=str(payload.get("company_name", "")).strip(),
        sector=str(payload.get("sector", "")).strip(),
        country=str(payload.get("country", "")).strip(),
        company_size=str(payload.get("company_size", "")).strip(),
        annual_revenue_band=str(payload.get("annual_revenue_band", "") or "").strip(),
        contact_name=str(payload.get("contact_name", "")).strip(),
        contact_role=str(payload.get("contact_role", "") or "").strip(),
        contact_email=str(payload.get("contact_email", "")).strip().lower(),
        contact_phone=str(payload.get("contact_phone", "") or "").strip(),
        acquisition_channel=str(payload.get("acquisition_channel", "") or "").strip(),
        consent=bool(payload.get("consent")),
        currency=normalise_currency(str(payload.get("currency", "") or "")),
        locale=str(payload.get("locale", "fr") or "fr"),
        ip_address=str(payload.get("ip_address", "") or "")[:64],
        user_agent=str(payload.get("user_agent", "") or "")[:400],
        status=STATUS_DRAFT,
        max_score=sum(c.max_score for c in ALL_CRITERIA),
    )
    session.add(assessment)
    session.flush()
    log(session, "assessment.created", assessment.public_id,
        {"company": assessment.company_name, "sector": assessment.sector})
    return assessment


def get_assessment(session: Session, public_id: str) -> Optional[Assessment]:
    return session.scalar(select(Assessment).where(Assessment.public_id == public_id))


def save_answers(session: Session, assessment: Assessment, answers: Mapping[str, object]) -> None:
    """Fusionne les réponses transmises avec celles déjà enregistrées."""
    merged = dict(assessment.answers)
    merged.update(normalise_answers(answers))
    assessment.answers = merged
    session.flush()


def finalise(session: Session, assessment: Assessment) -> ScoreResult:
    """Calcule et persiste les scores. Lève ValueError si des critères manquent."""
    score = compute_score(assessment.answers)
    if not score.is_complete:
        raise ValueError(f"{len(score.missing)} critère(s) non renseigné(s)")
    assessment.total_score = score.total_score
    assessment.max_score = score.max_score
    assessment.percentage = score.percentage
    assessment.level_code = score.level.code
    assessment.dimension_scores = score.to_dict()
    assessment.status = STATUS_COMPLETED
    assessment.completed_at = datetime.now(timezone.utc)
    session.flush()
    log(session, "assessment.completed", assessment.public_id,
        {"score": score.total_score, "percentage": score.percentage, "level": score.level.code})
    return score


def score_of(assessment: Assessment) -> ScoreResult:
    return compute_score(assessment.answers)


def analysis_of(assessment: Assessment) -> Analysis:
    return build_analysis(
        score_of(assessment),
        company_size_code=assessment.company_size,
        company_name=assessment.company_name or "Votre organisation",
        sector=assessment.sector,
    )


def progress_of(assessment: Assessment) -> dict:
    answered = len(assessment.answers)
    total = len(ALL_CRITERIA)
    return {
        "answered": answered,
        "total": total,
        "percentage": round(answered / total * 100) if total else 0,
    }


# ---------------------------------------------------------------------------
#  Commandes
# ---------------------------------------------------------------------------


def create_order(
    session: Session,
    assessment: Assessment,
    plan_code: str,
    currency: str,
    provider_code: str,
) -> Order:
    currency = normalise_currency(currency)
    price = price_for(plan_code, currency, session=session)
    order = Order(
        reference=new_reference(),
        assessment_id=assessment.id,
        plan_code=plan_code,
        currency=currency,
        amount_minor=price.minor_units,
        amount_xof=price.amount_xof,
        provider=provider_code,
        status=ORDER_PENDING,
        customer_email=assessment.contact_email,
    )
    session.add(order)
    session.flush()
    log(session, "order.created", order.reference,
        {"plan": plan_code, "currency": currency, "amount_minor": price.minor_units,
         "provider": provider_code, "company": assessment.company_name})
    return order


def get_order_by_reference(session: Session, reference: str) -> Optional[Order]:
    return session.scalar(select(Order).where(Order.reference == reference))


def get_order_by_public_id(session: Session, public_id: str) -> Optional[Order]:
    return session.scalar(select(Order).where(Order.public_id == public_id))


def mark_order_paid(
    session: Session,
    order: Order,
    *,
    provider_reference: str = "",
    actor: str = "webhook",
    detail: Optional[dict] = None,
) -> Order:
    if order.status == ORDER_PAID:
        return order  # idempotence : un webhook peut être rejoué
    order.status = ORDER_PAID
    order.paid_at = datetime.now(timezone.utc)
    if provider_reference:
        order.provider_reference = provider_reference
    meta = order.meta
    meta.update(detail or {})
    order.meta = meta
    session.flush()
    log(session, "order.paid", order.reference,
        {"provider": order.provider, "currency": order.currency,
         "amount_minor": order.amount_minor, "actor": actor}, actor=actor)
    return order


def mark_order_status(session: Session, order: Order, status: str, actor: str = "webhook") -> Order:
    order.status = status
    session.flush()
    log(session, f"order.{status}", order.reference, {"provider": order.provider}, actor=actor)
    return order


# ---------------------------------------------------------------------------
#  Journalisation
# ---------------------------------------------------------------------------


def log(session: Session, action: str, target: str = "", detail: Optional[dict] = None,
        actor: str = "system") -> AuditLog:
    entry = AuditLog(action=action, target=target, actor=actor)
    entry.detail = detail or {}
    session.add(entry)
    session.flush()
    return entry
