"""Couche de persistance : moteur SQLAlchemy, sessions et initialisation du schéma."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

def normalise_database_url(url: str) -> str:
    """Rend l'URL de base de données utilisable par SQLAlchemy 2 + psycopg.

    Render, Railway, Heroku et Fly.io exposent la variable DATABASE_URL au format
    ``postgres://...`` ou ``postgresql://...``. SQLAlchemy 2 choisirait alors le
    pilote psycopg2, absent de requirements.txt, et l'application refuserait de
    démarrer. On force donc explicitement le pilote psycopg (version 3).
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


_url = normalise_database_url(settings.database_url)
_connect_args: dict = {}

if _url.startswith("sqlite"):
    # Crée le répertoire du fichier SQLite au besoin.
    raw = _url.split("sqlite:///")[-1]
    if raw and raw != ":memory:":
        Path(raw).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    _url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

if _url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):  # pragma: no cover - infra
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Iterator[Session]:
    """Dépendance FastAPI fournissant une session transactionnelle."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Session utilisable hors requête HTTP (scripts, tâches planifiées)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Crée les tables manquantes et amorce les données de référence."""
    from app import models  # noqa: F401  (enregistre les mappings)

    models.Base.metadata.create_all(bind=engine)

    from app.services.admin_setup import ensure_bootstrap

    with session_scope() as session:
        ensure_bootstrap(session)
