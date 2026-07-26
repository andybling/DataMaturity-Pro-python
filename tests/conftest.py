"""Fixtures de test : instance isolée avec base SQLite temporaire."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

TMP_DB = Path(tempfile.gettempdir()) / "datamaturity_tests.db"

os.environ.setdefault("ENV_FILE", str(Path(tempfile.gettempdir()) / "no-such-env-file"))
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DB}"
os.environ["SECRET_KEY"] = "cle-de-test-uniquement-pour-les-tests-automatises"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "motdepasse-de-test"
os.environ["APP_ENV"] = "development"
os.environ["BASE_URL"] = "http://testserver"


@pytest.fixture(scope="session", autouse=True)
def _fresh_database():
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(TMP_DB) + suffix)
        if candidate.exists():
            candidate.unlink()
    from app.database import init_db

    init_db()
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest.fixture
def admin_client(client):
    response = client.post(
        "/admin/connexion",
        data={"username": "admin", "password": "motdepasse-de-test"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return client


@pytest.fixture
def full_answers():
    from app.data.grid import ALL_CRITERIA

    return {crit.code: (index * 3) % 4 for index, crit in enumerate(ALL_CRITERIA)}
