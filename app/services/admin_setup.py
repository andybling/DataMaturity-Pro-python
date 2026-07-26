"""Amorçage : compte administrateur et paramètres par défaut."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AdminUser
from app.security import hash_password
from app.services.pricing import (
    FX_SETTING_KEY,
    PRICE_SETTING_KEY,
    default_fx_rates,
    get_plan_prices_xof,
)
from app.services.settings_store import get_setting, set_setting


def ensure_admin_user(session: Session) -> AdminUser:
    """Crée le compte administrateur défini par les variables d'environnement."""
    user = session.scalar(select(AdminUser).where(AdminUser.username == settings.admin_username))
    if user is None:
        user = AdminUser(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
            email=settings.admin_email,
        )
        session.add(user)
        session.flush()
    return user


def ensure_default_settings(session: Session) -> None:
    if get_setting(session, FX_SETTING_KEY) is None:
        set_setting(session, FX_SETTING_KEY, default_fx_rates())
    if get_setting(session, PRICE_SETTING_KEY) is None:
        set_setting(session, PRICE_SETTING_KEY, get_plan_prices_xof())


def ensure_bootstrap(session: Session) -> None:
    ensure_admin_user(session)
    ensure_default_settings(session)


def admin_count(session: Session) -> int:
    return int(session.scalar(select(func.count()).select_from(AdminUser)) or 0)
