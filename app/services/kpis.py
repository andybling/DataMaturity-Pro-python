"""Indicateurs de pilotage pour la console d'administration."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ORDER_PAID,
    ORDER_PENDING,
    STATUS_COMPLETED,
    Assessment,
    Order,
    as_utc,
)
from app.services.pricing import SUPPORTED_CURRENCIES, format_amount, format_xof


@dataclass
class Kpis:
    assessments_total: int
    assessments_completed: int
    assessments_30d: int
    completion_rate: float
    average_score: float
    orders_total: int
    orders_paid: int
    orders_pending: int
    conversion_rate: float
    revenue_xof: int
    revenue_30d_xof: int
    revenue_by_currency: Dict[str, int] = field(default_factory=dict)
    revenue_by_plan: Dict[str, int] = field(default_factory=dict)
    average_basket_xof: int = 0
    leads_by_stage: Dict[str, int] = field(default_factory=dict)
    top_sectors: List[tuple] = field(default_factory=list)
    top_channels: List[tuple] = field(default_factory=list)
    monthly: List[dict] = field(default_factory=list)

    @property
    def revenue_label(self) -> str:
        return format_xof(self.revenue_xof)

    @property
    def average_basket_label(self) -> str:
        return format_xof(self.average_basket_xof)


def _count(session: Session, stmt) -> int:
    return int(session.scalar(stmt) or 0)


def compute_kpis(session: Session) -> Kpis:
    now = datetime.now(timezone.utc)
    since_30d = now - timedelta(days=30)

    total = _count(session, select(func.count()).select_from(Assessment))
    completed = _count(
        session,
        select(func.count()).select_from(Assessment).where(Assessment.status == STATUS_COMPLETED),
    )
    last_30d = _count(
        session,
        select(func.count()).select_from(Assessment).where(Assessment.created_at >= since_30d),
    )
    average = session.scalar(
        select(func.avg(Assessment.percentage)).where(Assessment.status == STATUS_COMPLETED)
    )

    orders = list(session.scalars(select(Order)).all())
    paid = [o for o in orders if o.status == ORDER_PAID]
    pending = [o for o in orders if o.status == ORDER_PENDING]

    revenue = sum(o.amount_xof for o in paid)
    revenue_30d = sum(
        o.amount_xof for o in paid if as_utc(o.paid_at) and as_utc(o.paid_at) >= since_30d
    )

    by_currency = {c: 0 for c in SUPPORTED_CURRENCIES}
    for order in paid:
        by_currency[order.currency] = by_currency.get(order.currency, 0) + order.amount_xof

    by_plan: Dict[str, int] = {}
    for order in paid:
        by_plan[order.plan_code] = by_plan.get(order.plan_code, 0) + order.amount_xof

    stages: Dict[str, int] = {}
    for stage, count in session.execute(
        select(Assessment.lead_stage, func.count()).group_by(Assessment.lead_stage)
    ):
        stages[stage or "nouveau"] = int(count)

    sectors = [
        (row[0] or "Non renseigné", int(row[1]), round(float(row[2] or 0), 1))
        for row in session.execute(
            select(Assessment.sector, func.count(), func.avg(Assessment.percentage))
            .where(Assessment.status == STATUS_COMPLETED)
            .group_by(Assessment.sector)
            .order_by(func.count().desc())
            .limit(8)
        )
    ]
    channels = [
        (row[0] or "Non renseigné", int(row[1]))
        for row in session.execute(
            select(Assessment.acquisition_channel, func.count())
            .group_by(Assessment.acquisition_channel)
            .order_by(func.count().desc())
            .limit(8)
        )
    ]

    monthly = _monthly_series(session, months=6)

    return Kpis(
        assessments_total=total,
        assessments_completed=completed,
        assessments_30d=last_30d,
        completion_rate=round(completed / total * 100, 1) if total else 0.0,
        average_score=round(float(average), 1) if average else 0.0,
        orders_total=len(orders),
        orders_paid=len(paid),
        orders_pending=len(pending),
        conversion_rate=round(len(paid) / completed * 100, 1) if completed else 0.0,
        revenue_xof=revenue,
        revenue_30d_xof=revenue_30d,
        revenue_by_currency=by_currency,
        revenue_by_plan=by_plan,
        average_basket_xof=int(statistics.fmean([o.amount_xof for o in paid])) if paid else 0,
        leads_by_stage=stages,
        top_sectors=sectors,
        top_channels=channels,
        monthly=monthly,
    )


def _monthly_series(session: Session, months: int = 6) -> List[dict]:
    """Évaluations et revenus des N derniers mois, calculés en Python
    pour rester indépendant du dialecte SQL (SQLite comme PostgreSQL)."""
    now = datetime.now(timezone.utc)
    buckets: List[dict] = []
    for offset in range(months - 1, -1, -1):
        year = now.year
        month = now.month - offset
        while month <= 0:
            month += 12
            year -= 1
        buckets.append({"key": f"{year}-{month:02d}", "label": f"{month:02d}/{year}",
                        "assessments": 0, "revenue_xof": 0})
    index = {b["key"]: b for b in buckets}

    for created_at, in session.execute(select(Assessment.created_at)):
        created_at = as_utc(created_at)
        if created_at is None:
            continue
        key = f"{created_at.year}-{created_at.month:02d}"
        if key in index:
            index[key]["assessments"] += 1

    for paid_at, amount in session.execute(
        select(Order.paid_at, Order.amount_xof).where(Order.status == ORDER_PAID)
    ):
        paid_at = as_utc(paid_at)
        if paid_at is None:
            continue
        key = f"{paid_at.year}-{paid_at.month:02d}"
        if key in index:
            index[key]["revenue_xof"] += int(amount or 0)

    peak = max([b["assessments"] for b in buckets] + [1])
    peak_revenue = max([b["revenue_xof"] for b in buckets] + [1])
    for bucket in buckets:
        bucket["assessments_ratio"] = round(bucket["assessments"] / peak * 100)
        bucket["revenue_ratio"] = round(bucket["revenue_xof"] / peak_revenue * 100)
        bucket["revenue_label"] = format_amount(bucket["revenue_xof"], "XOF")
    return buckets
