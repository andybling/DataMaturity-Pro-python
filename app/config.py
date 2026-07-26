"""Configuration centralisée de l'application (12-factor, via variables d'environnement)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    """Paramètres applicatifs. Toute valeur peut être surchargée par une variable d'environnement."""

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", str(PROJECT_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_env: str = "development"
    secret_key: str = "dev-secret-key-a-remplacer-en-production"
    base_url: str = "http://localhost:8000"
    default_locale: str = "fr"
    default_currency: str = "XOF"

    # --- Base de données ---
    database_url: str = f"sqlite:///{PROJECT_DIR / 'data' / 'datamaturity.db'}"

    # --- Administration ---
    admin_username: str = "admin"
    admin_password: str = "admin"
    admin_email: str = "yvesmouaha@yahoo.fr"

    # --- Marque ---
    brand_name: str = "DataMaturity Pro"
    brand_owner: str = "Yves Mouaha Handy"
    brand_tagline: str = "Diagnostic de maturité data pour les organisations africaines"
    contact_email: str = "yves.mouaha@akilicorp.com"
    contact_phone: str = "+225 07 48 78 25 17"
    contact_whatsapp: str = "2250748782517"

    # --- Change ---
    fx_eur_to_xof: float = 655.957
    fx_usd_to_xof: float = 610.0

    # --- Stripe ---
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    # --- CinetPay ---
    cinetpay_api_key: str = ""
    cinetpay_site_id: str = ""
    cinetpay_secret_key: str = ""
    cinetpay_mode: str = "TEST"

    # --- Divers ---
    enable_public_benchmark: bool = True
    min_benchmark_sample: int = 3

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @property
    def stripe_enabled(self) -> bool:
        return bool(self.stripe_secret_key)

    @property
    def cinetpay_enabled(self) -> bool:
        return bool(self.cinetpay_api_key and self.cinetpay_site_id)

    @property
    def whatsapp_url(self) -> str:
        return f"https://wa.me/{self.contact_whatsapp}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
