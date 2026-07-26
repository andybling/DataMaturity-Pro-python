"""Modèles de données (SQLAlchemy 2.0)."""

from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Normalise une date en UTC conscient du fuseau.

    SQLite ne conserve pas le fuseau horaire : les dates relues sont naïves.
    Toute comparaison entre dates doit donc passer par cette fonction pour
    rester valable aussi bien sur SQLite que sur PostgreSQL.
    """
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def new_public_id() -> str:
    return uuid.uuid4().hex


def new_access_code() -> str:
    return "DM-" + secrets.token_hex(4).upper()


class Base(DeclarativeBase):
    pass


class JSONMixin:
    """Aide à la (dé)sérialisation des colonnes texte contenant du JSON."""

    @staticmethod
    def _loads(raw: Optional[str], default: Any) -> Any:
        if not raw:
            return default
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _dumps(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)


# ----------------------------------------------------------------------------
#  Évaluations (le coeur du produit et de la base de prospects)
# ----------------------------------------------------------------------------

STATUS_DRAFT = "draft"
STATUS_COMPLETED = "completed"


class Assessment(Base, JSONMixin):
    """Une évaluation de maturité data réalisée par une organisation."""

    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, default=new_public_id, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Identité de l'organisation
    company_name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str] = mapped_column(String(120), index=True)
    country: Mapped[str] = mapped_column(String(120), index=True)
    company_size: Mapped[str] = mapped_column(String(60))
    annual_revenue_band: Mapped[str] = mapped_column(String(60), default="")

    # Contact (le lead commercial)
    contact_name: Mapped[str] = mapped_column(String(180))
    contact_role: Mapped[str] = mapped_column(String(180), default="")
    contact_email: Mapped[str] = mapped_column(String(255), index=True)
    contact_phone: Mapped[str] = mapped_column(String(60), default="")
    acquisition_channel: Mapped[str] = mapped_column(String(120), default="")
    consent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Contexte technique
    locale: Mapped[str] = mapped_column(String(10), default="fr")
    currency: Mapped[str] = mapped_column(String(3), default="XOF")
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(String(400), default="")

    # Réponses & résultats
    answers_raw: Mapped[str] = mapped_column(Text, default="{}")
    dimension_scores_raw: Mapped[str] = mapped_column(Text, default="{}")
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[int] = mapped_column(Integer, default=0)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    level_code: Mapped[str] = mapped_column(String(30), default="", index=True)
    status: Mapped[str] = mapped_column(String(20), default=STATUS_DRAFT, index=True)

    # Suivi commercial
    lead_stage: Mapped[str] = mapped_column(String(30), default="nouveau", index=True)
    lead_notes: Mapped[str] = mapped_column(Text, default="")

    orders: Mapped[list["Order"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (Index("ix_assessments_sector_country", "sector", "country"),)

    # --- accès typés aux colonnes JSON ---
    @property
    def answers(self) -> dict[str, int]:
        return {k: int(v) for k, v in self._loads(self.answers_raw, {}).items()}

    @answers.setter
    def answers(self, value: dict[str, int]) -> None:
        self.answers_raw = self._dumps({k: int(v) for k, v in value.items()})

    @property
    def dimension_scores(self) -> dict[str, dict]:
        return self._loads(self.dimension_scores_raw, {})

    @dimension_scores.setter
    def dimension_scores(self, value: dict[str, dict]) -> None:
        self.dimension_scores_raw = self._dumps(value)

    @property
    def is_unlocked(self) -> bool:
        """Vrai si au moins une commande payée débloque le rapport détaillé."""
        return any(o.status == ORDER_PAID for o in self.orders)

    @property
    def paid_plan_code(self) -> Optional[str]:
        paid = [o for o in self.orders if o.status == ORDER_PAID]
        if not paid:
            return None
        # Le plan le plus élevé l'emporte (premium > standard).
        order_rank = {"premium": 2, "standard": 1}
        return sorted(paid, key=lambda o: order_rank.get(o.plan_code, 0))[-1].plan_code


# ----------------------------------------------------------------------------
#  Commandes & paiements
# ----------------------------------------------------------------------------

ORDER_PENDING = "pending"
ORDER_PAID = "paid"
ORDER_FAILED = "failed"
ORDER_CANCELLED = "cancelled"
ORDER_REFUNDED = "refunded"


class Order(Base, JSONMixin):
    """Une commande de rapport payant, quel que soit le moyen de paiement."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, default=new_public_id, index=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), index=True)
    assessment: Mapped[Assessment] = relationship(back_populates="orders", lazy="joined")

    plan_code: Mapped[str] = mapped_column(String(40), index=True)
    currency: Mapped[str] = mapped_column(String(3), default="XOF")
    amount_minor: Mapped[int] = mapped_column(Integer, default=0)  # centimes (ou unité pour XOF)
    amount_xof: Mapped[int] = mapped_column(Integer, default=0)    # montant normalisé pour le reporting

    provider: Mapped[str] = mapped_column(String(40), default="manual", index=True)
    provider_reference: Mapped[str] = mapped_column(String(180), default="", index=True)
    status: Mapped[str] = mapped_column(String(20), default=ORDER_PENDING, index=True)

    access_code: Mapped[str] = mapped_column(String(40), default=new_access_code, index=True)
    customer_email: Mapped[str] = mapped_column(String(255), default="")
    meta_raw: Mapped[str] = mapped_column(Text, default="{}")

    @property
    def meta(self) -> dict:
        return self._loads(self.meta_raw, {})

    @meta.setter
    def meta(self, value: dict) -> None:
        self.meta_raw = self._dumps(value)


# ----------------------------------------------------------------------------
#  Paramètres pilotables depuis l'admin
# ----------------------------------------------------------------------------


class Setting(Base, JSONMixin):
    """Paramètre modifiable à chaud (tarifs, taux de change, drapeaux)."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value_raw: Mapped[str] = mapped_column(Text, default="null")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    @property
    def value(self) -> Any:
        return self._loads(self.value_raw, None)

    @value.setter
    def value(self, v: Any) -> None:
        self.value_raw = self._dumps(v)


# ----------------------------------------------------------------------------
#  Administration
# ----------------------------------------------------------------------------


class AdminUser(Base):
    """Compte d'accès à la console de pilotage."""

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base, JSONMixin):
    """Journal des opérations sensibles (traçabilité en production)."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    actor: Mapped[str] = mapped_column(String(120), default="system")
    action: Mapped[str] = mapped_column(String(120), index=True)
    target: Mapped[str] = mapped_column(String(180), default="")
    detail_raw: Mapped[str] = mapped_column(Text, default="{}")

    @property
    def detail(self) -> dict:
        return self._loads(self.detail_raw, {})

    @detail.setter
    def detail(self, value: dict) -> None:
        self.detail_raw = self._dumps(value)
