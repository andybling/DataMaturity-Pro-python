"""Environnement de gabarits Jinja2 et contexte commun."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR, settings
from app.data.grid import CRITERIA_COUNT, DIMENSIONS, MAX_TOTAL_SCORE
from app.data.levels import LEVELS
from app.services.charts import radar_svg
from app.services.pricing import CURRENCIES, SUPPORTED_CURRENCIES, format_amount, format_xof

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _percent(value: Any, decimals: int = 0) -> str:
    try:
        return f"{float(value):.{decimals}f} %"
    except (TypeError, ValueError):
        return "—"


def _date(value: Optional[datetime], fmt: str = "%d/%m/%Y") -> str:
    if not value:
        return "—"
    return value.strftime(fmt)


def _datetime(value: Optional[datetime]) -> str:
    return _date(value, "%d/%m/%Y à %H:%M")


templates.env.filters["percent"] = _percent
templates.env.filters["date_fr"] = _date
templates.env.filters["datetime_fr"] = _datetime
templates.env.filters["money"] = format_amount
templates.env.filters["xof"] = format_xof

templates.env.globals.update(
    settings=settings,
    dimensions=DIMENSIONS,
    levels=LEVELS,
    criteria_count=CRITERIA_COUNT,
    max_total_score=MAX_TOTAL_SCORE,
    currencies=CURRENCIES,
    supported_currencies=SUPPORTED_CURRENCIES,
    radar_svg=radar_svg,
    now=lambda: datetime.now(timezone.utc),
)


def render(request: Request, template: str, context: Optional[dict] = None, status_code: int = 200):
    payload = {"current_year": datetime.now(timezone.utc).year}
    payload.update(context or {})
    return templates.TemplateResponse(request, template, payload, status_code=status_code)
