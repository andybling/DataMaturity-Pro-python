"""Sécurité : hachage de mots de passe, jetons signés, authentification admin."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import Optional

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AdminUser

_ITERATIONS = 260_000
_ALGO = "pbkdf2_sha256"


# --------------------------------------------------------------------------
#  Mots de passe (PBKDF2-HMAC-SHA256, sans dépendance externe)
# --------------------------------------------------------------------------


def hash_password(password: str, *, salt: Optional[str] = None, iterations: int = _ITERATIONS) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"{_ALGO}${iterations}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt, _ = stored.split("$", 3)
    except ValueError:
        return False
    if algo != _ALGO:
        return False
    candidate = hash_password(password, salt=salt, iterations=int(iterations))
    return hmac.compare_digest(candidate, stored)


# --------------------------------------------------------------------------
#  Jetons signés (accès aux rapports par lien, sans compte utilisateur)
# --------------------------------------------------------------------------


def sign_token(payload: str, *, ttl_seconds: int = 60 * 60 * 24 * 365) -> str:
    """Signe `payload` avec une date d'expiration. Format : payload.expiry.signature."""
    expiry = int(time.time()) + ttl_seconds
    body = f"{payload}|{expiry}"
    sig = hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest()
    return f"{base64.urlsafe_b64encode(body.encode()).decode().rstrip('=')}.{base64.urlsafe_b64encode(sig).decode().rstrip('=')}"


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def verify_token(token: str) -> Optional[str]:
    """Retourne le payload si la signature est valide et le jeton non expiré, sinon None."""
    try:
        body_b64, sig_b64 = token.split(".", 1)
        body = _b64decode(body_b64).decode()
        sig = _b64decode(sig_b64)
    except Exception:
        return None
    expected = hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return None
    payload, _, expiry = body.rpartition("|")
    try:
        if int(expiry) < int(time.time()):
            return None
    except ValueError:
        return None
    return payload


# --------------------------------------------------------------------------
#  Authentification de la console admin
# --------------------------------------------------------------------------

SESSION_KEY = "admin_user"


def authenticate_admin(session: Session, username: str, password: str) -> Optional[AdminUser]:
    user = session.scalar(select(AdminUser).where(AdminUser.username == username))
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def current_admin(request: Request) -> Optional[str]:
    return request.session.get(SESSION_KEY)


def login_admin(request: Request, user: AdminUser) -> None:
    request.session[SESSION_KEY] = user.username


def logout_admin(request: Request) -> None:
    request.session.pop(SESSION_KEY, None)
