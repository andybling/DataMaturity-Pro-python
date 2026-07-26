"""Console d'administration : pilotage commercial et paramétrage en production."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.data.reference import ACQUISITION_CHANNELS, LEAD_STAGES, SECTORS
from app.database import get_session
from app.models import (
    ORDER_PAID,
    ORDER_PENDING,
    STATUS_COMPLETED,
    Assessment,
    AuditLog,
    Order,
)
from app.security import (
    authenticate_admin,
    current_admin,
    hash_password,
    login_admin,
    logout_admin,
    sign_token,
    verify_password,
)
from app.models import AdminUser
from app.services import assessments as svc
from app.services.benchmark import global_segment, segments_by
from app.services.exports import to_csv, to_xlsx
from app.services.kpis import compute_kpis
from app.services.pricing import (
    FX_SETTING_KEY,
    PLANS,
    PRICE_OVERRIDE_KEY,
    PRICE_SETTING_KEY,
    SUPPORTED_CURRENCIES,
    get_fx_rates,
    get_plan_prices_xof,
    get_price_overrides,
    plan_views,
)
from app.services.settings_store import set_setting
from app.templating import render

router = APIRouter(prefix="/admin", tags=["administration"])


# ---------------------------------------------------------------------------
#  Authentification
# ---------------------------------------------------------------------------


def require_admin(request: Request) -> str:
    username = current_admin(request)
    if not username:
        raise HTTPException(status_code=303, detail="/admin/connexion")
    return username


def _redirect_login() -> RedirectResponse:
    return RedirectResponse("/admin/connexion", status_code=303)


@router.get("/connexion")
async def login_form(request: Request):
    if current_admin(request):
        return RedirectResponse("/admin", status_code=303)
    return render(request, "admin/login.html", {})


@router.post("/connexion")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = authenticate_admin(session, username.strip(), password)
    if user is None:
        svc.log(session, "admin.login_failed", username.strip(), actor="anonyme")
        return render(
            request,
            "admin/login.html",
            {"errors": ["Identifiants incorrects."]},
            status_code=401,
        )
    login_admin(request, user)
    user.last_login_at = datetime.now(timezone.utc)
    svc.log(session, "admin.login", user.username, actor=user.username)
    return RedirectResponse("/admin", status_code=303)


@router.get("/deconnexion")
async def logout(request: Request):
    logout_admin(request)
    return RedirectResponse("/admin/connexion", status_code=303)


# ---------------------------------------------------------------------------
#  Tableau de bord
# ---------------------------------------------------------------------------


@router.get("")
@router.get("/")
async def dashboard(request: Request, session: Session = Depends(get_session)):
    if not current_admin(request):
        return _redirect_login()
    kpis = compute_kpis(session)
    recent = list(
        session.scalars(select(Assessment).order_by(desc(Assessment.created_at)).limit(8)).all()
    )
    recent_orders = list(session.scalars(select(Order).order_by(desc(Order.created_at)).limit(8)).all())
    return render(
        request,
        "admin/dashboard.html",
        {
            "admin": current_admin(request),
            "kpis": kpis,
            "recent": recent,
            "recent_orders": recent_orders,
            "active": "dashboard",
        },
    )


# ---------------------------------------------------------------------------
#  Prospects
# ---------------------------------------------------------------------------


def _filtered_assessments(session: Session, params) -> list[Assessment]:
    stmt = select(Assessment)
    search = (params.get("q") or "").strip()
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Assessment.company_name.ilike(like),
                Assessment.contact_name.ilike(like),
                Assessment.contact_email.ilike(like),
            )
        )
    for field_name, column in (
        ("secteur", Assessment.sector),
        ("pays", Assessment.country),
        ("niveau", Assessment.level_code),
        ("etape", Assessment.lead_stage),
        ("statut", Assessment.status),
    ):
        value = (params.get(field_name) or "").strip()
        if value:
            stmt = stmt.where(column == value)
    if (params.get("payes") or "") == "1":
        stmt = stmt.where(Assessment.orders.any(Order.status == ORDER_PAID))
    return list(session.scalars(stmt.order_by(desc(Assessment.created_at))).all())


@router.get("/prospects")
async def leads(request: Request, session: Session = Depends(get_session)):
    if not current_admin(request):
        return _redirect_login()
    rows = _filtered_assessments(session, request.query_params)
    countries = [
        row[0] for row in session.execute(
            select(Assessment.country).distinct().order_by(Assessment.country)
        ) if row[0]
    ]
    return render(
        request,
        "admin/leads.html",
        {
            "admin": current_admin(request),
            "rows": rows,
            "sectors": SECTORS,
            "countries": countries,
            "stages": LEAD_STAGES,
            "filters": dict(request.query_params),
            "active": "leads",
            "query_string": str(request.url.query),
        },
    )


@router.get("/prospects/export.csv")
async def leads_csv(request: Request, session: Session = Depends(get_session)):
    if not current_admin(request):
        return _redirect_login()
    rows = _filtered_assessments(session, request.query_params)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    return Response(
        content=to_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="prospects-{stamp}.csv"'},
    )


@router.get("/prospects/export.xlsx")
async def leads_xlsx(request: Request, session: Session = Depends(get_session)):
    if not current_admin(request):
        return _redirect_login()
    rows = _filtered_assessments(session, request.query_params)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    return Response(
        content=to_xlsx(rows),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="prospects-{stamp}.xlsx"'},
    )


@router.get("/prospects/{public_id}")
async def lead_detail(request: Request, public_id: str, session: Session = Depends(get_session)):
    if not current_admin(request):
        return _redirect_login()
    assessment = svc.get_assessment(session, public_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Évaluation introuvable.")
    analysis = svc.analysis_of(assessment) if assessment.status == STATUS_COMPLETED else None
    return render(
        request,
        "admin/lead_detail.html",
        {
            "admin": current_admin(request),
            "assessment": assessment,
            "analysis": analysis,
            "score": analysis.score if analysis else None,
            "stages": LEAD_STAGES,
            "report_token": sign_token(assessment.public_id),
            "active": "leads",
        },
    )


@router.post("/prospects/{public_id}")
async def lead_update(
    request: Request,
    public_id: str,
    lead_stage: str = Form(...),
    lead_notes: str = Form(""),
    session: Session = Depends(get_session),
):
    admin = current_admin(request)
    if not admin:
        return _redirect_login()
    assessment = svc.get_assessment(session, public_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Évaluation introuvable.")
    assessment.lead_stage = lead_stage if lead_stage in LEAD_STAGES else assessment.lead_stage
    assessment.lead_notes = lead_notes
    svc.log(session, "lead.updated", public_id, {"stage": lead_stage}, actor=admin)
    return RedirectResponse(f"/admin/prospects/{public_id}", status_code=303)


# ---------------------------------------------------------------------------
#  Commandes
# ---------------------------------------------------------------------------


@router.get("/commandes")
async def orders(request: Request, session: Session = Depends(get_session)):
    if not current_admin(request):
        return _redirect_login()
    status_filter = (request.query_params.get("statut") or "").strip()
    stmt = select(Order)
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    rows = list(session.scalars(stmt.order_by(desc(Order.created_at))).all())
    totals = {
        "paid": sum(o.amount_xof for o in rows if o.status == ORDER_PAID),
        "pending": sum(o.amount_xof for o in rows if o.status == ORDER_PENDING),
    }
    return render(
        request,
        "admin/orders.html",
        {
            "admin": current_admin(request),
            "rows": rows,
            "totals": totals,
            "filters": dict(request.query_params),
            "active": "orders",
        },
    )


@router.post("/commandes/{reference}/valider")
async def validate_order(
    request: Request, reference: str, session: Session = Depends(get_session)
):
    """Validation manuelle d'un paiement (virement, dépôt Mobile Money, facture)."""
    admin = current_admin(request)
    if not admin:
        return _redirect_login()
    order = svc.get_order_by_reference(session, reference)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    svc.mark_order_paid(session, order, actor=admin, detail={"validation": "manuelle"})
    return RedirectResponse("/admin/commandes", status_code=303)


@router.post("/commandes/{reference}/annuler")
async def cancel_order(request: Request, reference: str, session: Session = Depends(get_session)):
    admin = current_admin(request)
    if not admin:
        return _redirect_login()
    order = svc.get_order_by_reference(session, reference)
    if order is None:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    svc.mark_order_status(session, order, "cancelled", actor=admin)
    return RedirectResponse("/admin/commandes", status_code=303)


# ---------------------------------------------------------------------------
#  Tarification
# ---------------------------------------------------------------------------


@router.get("/tarification")
async def pricing_admin(request: Request, session: Session = Depends(get_session)):
    if not current_admin(request):
        return _redirect_login()
    return render(
        request,
        "admin/pricing.html",
        {
            "admin": current_admin(request),
            "plans": PLANS,
            "prices_xof": get_plan_prices_xof(session),
            "fx": get_fx_rates(session),
            "overrides": get_price_overrides(session),
            "views": {code: plan_views(code, session=session) for code in SUPPORTED_CURRENCIES},
            "active": "pricing",
        },
    )


@router.post("/tarification")
async def pricing_save(request: Request, session: Session = Depends(get_session)):
    admin = current_admin(request)
    if not admin:
        return _redirect_login()
    form = await request.form()

    prices = get_plan_prices_xof(session)
    for plan in PLANS:
        raw = form.get(f"price_{plan.code}")
        if raw not in (None, ""):
            try:
                prices[plan.code] = max(0, int(float(str(raw).replace(" ", "").replace(",", "."))))
            except ValueError:
                continue
    set_setting(session, PRICE_SETTING_KEY, prices)

    rates = get_fx_rates(session)
    for code in SUPPORTED_CURRENCIES:
        if code == "XOF":
            continue
        raw = form.get(f"fx_{code}")
        if raw not in (None, ""):
            try:
                value = float(str(raw).replace(",", "."))
                if value > 0:
                    rates[code] = value
            except ValueError:
                continue
    set_setting(session, FX_SETTING_KEY, rates)

    overrides: dict = {}
    for plan in PLANS:
        for code in SUPPORTED_CURRENCIES:
            raw = form.get(f"override_{plan.code}_{code}")
            if raw not in (None, ""):
                try:
                    overrides.setdefault(plan.code, {})[code] = float(
                        str(raw).replace(" ", "").replace(",", ".")
                    )
                except ValueError:
                    continue
    set_setting(session, PRICE_OVERRIDE_KEY, overrides)

    svc.log(session, "pricing.updated", "settings",
            {"prices": prices, "fx": rates, "overrides": overrides}, actor=admin)
    return RedirectResponse("/admin/tarification?ok=1", status_code=303)


# ---------------------------------------------------------------------------
#  Baromètre interne
# ---------------------------------------------------------------------------


@router.get("/barometre")
async def barometer_admin(request: Request, session: Session = Depends(get_session)):
    if not current_admin(request):
        return _redirect_login()
    return render(
        request,
        "admin/barometer.html",
        {
            "admin": current_admin(request),
            "overall": global_segment(session),
            "sectors": segments_by(session, "sector"),
            "countries": segments_by(session, "country"),
            "sizes": segments_by(session, "company_size"),
            "active": "barometer",
        },
    )


# ---------------------------------------------------------------------------
#  Journal et compte
# ---------------------------------------------------------------------------


@router.get("/journal")
async def audit(request: Request, session: Session = Depends(get_session)):
    if not current_admin(request):
        return _redirect_login()
    rows = list(session.scalars(select(AuditLog).order_by(desc(AuditLog.at)).limit(300)).all())
    return render(
        request,
        "admin/audit.html",
        {"admin": current_admin(request), "rows": rows, "active": "audit"},
    )


@router.get("/compte")
async def account(request: Request, session: Session = Depends(get_session)):
    if not current_admin(request):
        return _redirect_login()
    return render(
        request,
        "admin/account.html",
        {
            "admin": current_admin(request),
            "active": "account",
            "config": {
                "environnement": settings.app_env,
                "base_de_donnees": settings.database_url.split("://")[0],
                "url_publique": settings.base_url,
                "stripe": "configuré" if settings.stripe_enabled else "non configuré",
                "cinetpay": "configuré" if settings.cinetpay_enabled else "non configuré",
                "barometre_public": "activé" if settings.enable_public_benchmark else "désactivé",
                "seuil_barometre": settings.min_benchmark_sample,
            },
        },
    )


@router.post("/compte/mot-de-passe")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    session: Session = Depends(get_session),
):
    admin = current_admin(request)
    if not admin:
        return _redirect_login()
    user = session.scalar(select(AdminUser).where(AdminUser.username == admin))
    errors = []
    if user is None or not verify_password(current_password, user.password_hash):
        errors.append("Le mot de passe actuel est incorrect.")
    if len(new_password) < 10:
        errors.append("Le nouveau mot de passe doit comporter au moins 10 caractères.")
    if new_password != confirm_password:
        errors.append("La confirmation ne correspond pas au nouveau mot de passe.")

    if errors:
        return render(
            request,
            "admin/account.html",
            {"admin": admin, "active": "account", "errors": errors, "config": {}},
            status_code=400,
        )

    user.password_hash = hash_password(new_password)
    svc.log(session, "admin.password_changed", admin, actor=admin)
    return RedirectResponse("/admin/compte?ok=1", status_code=303)
