"""Parcours public : présentation, questionnaire, résultats, rapport."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.data.grid import DIMENSIONS
from app.data.reference import (
    ACQUISITION_CHANNELS,
    COMPANY_SIZES,
    COUNTRIES,
    REVENUE_BANDS,
    SECTORS,
)
from app.database import get_session
from app.models import ORDER_PAID, STATUS_COMPLETED, Assessment, Order
from app.security import verify_token
from app.services import assessments as svc
from app.services.analysis import public_summary
from app.services.benchmark import positioning_for, public_barometer
from app.services.pricing import (
    PAID_PLAN_CODES,
    currency_for_country,
    normalise_currency,
    plan_views,
)
from app.services.reports import build_grid_xlsx, build_report_pdf, report_filename
from app.templating import render

router = APIRouter(tags=["public"])

SESSION_UNLOCKED = "unlocked_assessments"
SESSION_CURRENCY = "currency"


# ---------------------------------------------------------------------------
#  Utilitaires de session
# ---------------------------------------------------------------------------


def resolve_currency(request: Request, fallback: Optional[str] = None) -> str:
    """Devise retenue : paramètre d'URL > session > pays de l'évaluation > défaut."""
    requested = request.query_params.get("devise")
    if requested:
        code = normalise_currency(requested)
        request.session[SESSION_CURRENCY] = code
        return code
    if request.session.get(SESSION_CURRENCY):
        return normalise_currency(request.session[SESSION_CURRENCY])
    return normalise_currency(fallback or settings.default_currency)


def _unlocked_ids(request: Request) -> list[str]:
    return list(request.session.get(SESSION_UNLOCKED) or [])


def grant_access(request: Request, assessment: Assessment) -> None:
    ids = _unlocked_ids(request)
    if assessment.public_id not in ids:
        ids.append(assessment.public_id)
        request.session[SESSION_UNLOCKED] = ids


def has_access(request: Request, assessment: Assessment) -> bool:
    """Le rapport est accessible si une commande est payée et que la session,
    un jeton signé ou un code d'accès le prouve."""
    if not assessment.is_unlocked:
        return False
    if assessment.public_id in _unlocked_ids(request):
        return True
    token = request.query_params.get("jeton")
    if token and verify_token(token) == assessment.public_id:
        grant_access(request, assessment)
        return True
    code = (request.query_params.get("code") or "").strip().upper()
    if code and any(o.access_code == code and o.status == ORDER_PAID for o in assessment.orders):
        grant_access(request, assessment)
        return True
    return False


def _get_or_404(session: Session, public_id: str) -> Assessment:
    assessment = svc.get_assessment(session, public_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Évaluation introuvable.")
    return assessment


# ---------------------------------------------------------------------------
#  Pages de présentation
# ---------------------------------------------------------------------------


@router.get("/")
async def landing(request: Request, session: Session = Depends(get_session)):
    currency = resolve_currency(request)
    completed = int(
        session.scalar(
            select(func.count()).select_from(Assessment).where(Assessment.status == STATUS_COMPLETED)
        )
        or 0
    )
    average = session.scalar(
        select(func.avg(Assessment.percentage)).where(Assessment.status == STATUS_COMPLETED)
    )
    return render(
        request,
        "landing.html",
        {
            "plans": plan_views(currency, session=session),
            "currency": currency,
            "stats": {
                "completed": completed,
                "average": round(float(average), 1) if average else None,
                "sectors": int(
                    session.scalar(
                        select(func.count(func.distinct(Assessment.sector))).where(
                            Assessment.status == STATUS_COMPLETED
                        )
                    )
                    or 0
                ),
            },
        },
    )


@router.get("/tarifs")
async def pricing(request: Request, session: Session = Depends(get_session)):
    currency = resolve_currency(request)
    return render(
        request,
        "pricing.html",
        {"plans": plan_views(currency, session=session), "currency": currency},
    )


@router.get("/methodologie")
async def methodology(request: Request):
    return render(request, "methodology.html", {"dimensions": DIMENSIONS})


@router.get("/barometre")
async def barometer(request: Request, session: Session = Depends(get_session)):
    if not settings.enable_public_benchmark:
        raise HTTPException(status_code=404, detail="Baromètre non publié.")
    return render(request, "barometer.html", {"barometer": public_barometer(session)})


@router.get("/mentions-legales")
async def legal(request: Request):
    return render(request, "legal.html", {})


# ---------------------------------------------------------------------------
#  Questionnaire
# ---------------------------------------------------------------------------


@router.get("/diagnostic")
async def start_form(request: Request):
    return render(
        request,
        "assessment_start.html",
        {
            "sectors": SECTORS,
            "countries": COUNTRIES,
            "sizes": COMPANY_SIZES,
            "revenue_bands": REVENUE_BANDS,
            "channels": ACQUISITION_CHANNELS,
            "currency": resolve_currency(request),
        },
    )


@router.post("/diagnostic")
async def start_submit(
    request: Request,
    company_name: str = Form(...),
    sector: str = Form(...),
    country: str = Form(...),
    company_size: str = Form(...),
    contact_name: str = Form(...),
    contact_email: str = Form(...),
    contact_role: str = Form(""),
    contact_phone: str = Form(""),
    annual_revenue_band: str = Form(""),
    acquisition_channel: str = Form(""),
    consent: str = Form(""),
    session: Session = Depends(get_session),
):
    errors: list[str] = []
    if not company_name.strip():
        errors.append("Le nom de l'organisation est obligatoire.")
    if "@" not in contact_email or "." not in contact_email.split("@")[-1]:
        errors.append("L'adresse email professionnelle n'est pas valide.")
    if not consent:
        errors.append("Le consentement au traitement des données est nécessaire pour continuer.")

    if errors:
        return render(
            request,
            "assessment_start.html",
            {
                "sectors": SECTORS,
                "countries": COUNTRIES,
                "sizes": COMPANY_SIZES,
                "revenue_bands": REVENUE_BANDS,
                "channels": ACQUISITION_CHANNELS,
                "errors": errors,
                "form": {
                    "company_name": company_name,
                    "sector": sector,
                    "country": country,
                    "company_size": company_size,
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                    "contact_role": contact_role,
                    "contact_phone": contact_phone,
                    "annual_revenue_band": annual_revenue_band,
                    "acquisition_channel": acquisition_channel,
                },
                "currency": resolve_currency(request),
            },
            status_code=400,
        )

    currency = resolve_currency(request, currency_for_country(country))
    assessment = svc.create_assessment(
        session,
        {
            "company_name": company_name,
            "sector": sector,
            "country": country,
            "company_size": company_size,
            "annual_revenue_band": annual_revenue_band,
            "contact_name": contact_name,
            "contact_role": contact_role,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "acquisition_channel": acquisition_channel,
            "consent": bool(consent),
            "currency": currency,
            "ip_address": request.client.host if request.client else "",
            "user_agent": request.headers.get("user-agent", ""),
        },
    )
    return RedirectResponse(f"/diagnostic/{assessment.public_id}/1", status_code=303)


@router.get("/diagnostic/{public_id}/{step}")
async def section_form(
    request: Request, public_id: str, step: int, session: Session = Depends(get_session)
):
    assessment = _get_or_404(session, public_id)
    if step < 1 or step > len(DIMENSIONS):
        raise HTTPException(status_code=404, detail="Section inexistante.")
    dimension = DIMENSIONS[step - 1]
    return render(
        request,
        "assessment_section.html",
        {
            "assessment": assessment,
            "dimension": dimension,
            "step": step,
            "total_steps": len(DIMENSIONS),
            "answers": assessment.answers,
            "progress": svc.progress_of(assessment),
        },
    )


@router.post("/diagnostic/{public_id}/{step}")
async def section_submit(
    request: Request, public_id: str, step: int, session: Session = Depends(get_session)
):
    assessment = _get_or_404(session, public_id)
    if step < 1 or step > len(DIMENSIONS):
        raise HTTPException(status_code=404, detail="Section inexistante.")
    dimension = DIMENSIONS[step - 1]

    form = await request.form()
    payload = {}
    missing = []
    for criterion in dimension.criteria:
        value = form.get(criterion.code)
        if value in (None, ""):
            missing.append(criterion.code)
        else:
            payload[criterion.code] = value

    direction = form.get("direction", "next")
    if missing and direction == "next":
        svc.save_answers(session, assessment, payload)
        return render(
            request,
            "assessment_section.html",
            {
                "assessment": assessment,
                "dimension": dimension,
                "step": step,
                "total_steps": len(DIMENSIONS),
                "answers": assessment.answers,
                "progress": svc.progress_of(assessment),
                "missing": set(missing),
                "errors": [f"{len(missing)} critère(s) restent à renseigner dans cette section."],
            },
            status_code=400,
        )

    svc.save_answers(session, assessment, payload)

    if direction == "previous":
        return RedirectResponse(f"/diagnostic/{public_id}/{max(1, step - 1)}", status_code=303)

    if step < len(DIMENSIONS):
        return RedirectResponse(f"/diagnostic/{public_id}/{step + 1}", status_code=303)

    try:
        svc.finalise(session, assessment)
    except ValueError:
        return RedirectResponse(f"/diagnostic/{public_id}/1", status_code=303)
    return RedirectResponse(f"/resultats/{public_id}", status_code=303)


# ---------------------------------------------------------------------------
#  Résultats (couche gratuite)
# ---------------------------------------------------------------------------


@router.get("/resultats/{public_id}")
async def results(request: Request, public_id: str, session: Session = Depends(get_session)):
    assessment = _get_or_404(session, public_id)
    if assessment.status != STATUS_COMPLETED:
        return RedirectResponse(f"/diagnostic/{public_id}/1", status_code=303)

    analysis = svc.analysis_of(assessment)
    currency = resolve_currency(request, assessment.currency)
    unlocked = has_access(request, assessment)
    return render(
        request,
        "results.html",
        {
            "assessment": assessment,
            "analysis": analysis,
            "summary": public_summary(analysis),
            "score": analysis.score,
            "plans": plan_views(currency, session=session, codes=PAID_PLAN_CODES),
            "currency": currency,
            "unlocked": unlocked,
            "paid_plan": assessment.paid_plan_code,
        },
    )


@router.get("/resultats/{public_id}/rapport")
async def full_report(request: Request, public_id: str, session: Session = Depends(get_session)):
    assessment = _get_or_404(session, public_id)
    if assessment.status != STATUS_COMPLETED:
        return RedirectResponse(f"/diagnostic/{public_id}/1", status_code=303)
    if not has_access(request, assessment):
        return RedirectResponse(f"/resultats/{public_id}", status_code=303)

    analysis = svc.analysis_of(assessment)
    plan = assessment.paid_plan_code or "standard"
    return render(
        request,
        "report.html",
        {
            "assessment": assessment,
            "analysis": analysis,
            "score": analysis.score,
            "plan_code": plan,
            "premium": plan == "premium",
            "positioning": positioning_for(session, assessment),
        },
    )


@router.get("/resultats/{public_id}/rapport.pdf")
async def report_pdf(request: Request, public_id: str, session: Session = Depends(get_session)):
    assessment = _get_or_404(session, public_id)
    if not has_access(request, assessment):
        raise HTTPException(status_code=403, detail="Ce rapport nécessite une commande réglée.")
    analysis = svc.analysis_of(assessment)
    plan = assessment.paid_plan_code or "standard"
    content = build_report_pdf(
        assessment, analysis, plan_code=plan, positioning=positioning_for(session, assessment)
    )
    filename = report_filename(assessment, "pdf", plan)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/resultats/{public_id}/grille.xlsx")
async def report_xlsx(request: Request, public_id: str, session: Session = Depends(get_session)):
    assessment = _get_or_404(session, public_id)
    unlocked = has_access(request, assessment)
    analysis = svc.analysis_of(assessment)
    content = build_grid_xlsx(assessment, analysis, include_action_plan=unlocked)
    filename = report_filename(assessment, "xlsx", assessment.paid_plan_code or "gratuit")
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
#  Récupération d'accès par code
# ---------------------------------------------------------------------------


@router.get("/acces")
async def access_form(request: Request):
    return render(request, "access.html", {})


@router.post("/acces")
async def access_submit(
    request: Request, code: str = Form(...), session: Session = Depends(get_session)
):
    cleaned = code.strip().upper()
    order = session.scalar(
        select(Order).where(Order.access_code == cleaned, Order.status == ORDER_PAID)
    )
    if order is None:
        return render(
            request,
            "access.html",
            {"errors": ["Ce code d'accès est inconnu ou la commande n'est pas encore validée."]},
            status_code=404,
        )
    grant_access(request, order.assessment)
    return RedirectResponse(f"/resultats/{order.assessment.public_id}/rapport", status_code=303)
