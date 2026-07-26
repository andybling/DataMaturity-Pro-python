"""Accès aux paramètres administrables stockés en base."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Setting


def get_setting(session: Session, key: str, default: Any = None) -> Any:
    row = session.get(Setting, key)
    if row is None:
        return default
    value = row.value
    return default if value is None else value


def set_setting(session: Session, key: str, value: Any) -> Setting:
    row = session.get(Setting, key)
    if row is None:
        row = Setting(key=key)
        session.add(row)
    row.value = value
    session.flush()
    return row


def all_settings(session: Session) -> dict[str, Any]:
    return {row.key: row.value for row in session.scalars(select(Setting)).all()}


def delete_setting(session: Session, key: str) -> None:
    row = session.get(Setting, key)
    if row is not None:
        session.delete(row)
