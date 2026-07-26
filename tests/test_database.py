from contextlib import contextmanager

from sqlalchemy.exc import OperationalError

from app import database
import app.models as models_module
from app.services import admin_setup


def test_init_db_retries_transient_database_errors(monkeypatch):
    calls = 0

    def flaky_create_all(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OperationalError("statement", None, Exception("temporary db unavailable"))

    @contextmanager
    def fake_session_scope():
        yield object()

    monkeypatch.setattr(models_module.Base.metadata, "create_all", flaky_create_all)
    monkeypatch.setattr(admin_setup, "ensure_bootstrap", lambda session: None)
    monkeypatch.setattr(database, "session_scope", fake_session_scope)
    monkeypatch.setattr(database.time, "sleep", lambda *_args, **_kwargs: None)

    database.init_db(max_retries=2, delay_seconds=0)

    assert calls == 2
