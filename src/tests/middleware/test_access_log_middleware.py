# src/tests/test_access_log_middleware.py
from fastapi import FastAPI
from starlette.testclient import TestClient
import types

from middleware.access_log import AccessLogMiddleware

class _FakeSession:
    def __init__(self, store): self._store = store
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def add(self, entry): self._store.append(entry)
    def commit(self): pass

def test_middleware_logs_asset_hit(monkeypatch):
    app = FastAPI()
    app.add_middleware(AccessLogMiddleware)

    # Endpoint that looks like an asset
    @app.get("/v2/datasets/v1/1")
    def _ok(): return {"ok": True}

    # capture writes
    written = []

    # monkeypatch DbSession in the middleware module
    import middleware.access_log as m
    def _fake_db_session():
        return _FakeSession(written)
    monkeypatch.setattr(m, "DbSession", _fake_db_session, raising=True)

    client = TestClient(app)
    r = client.get("/v2/datasets/v1/1")
    assert r.status_code == 200

    # exactly one entry captured
    assert len(written) == 1
    entry = written[0]
    assert entry.resource_type == "datasets"
    assert entry.asset_id == "v1/1"
    assert entry.status == 200

def test_middleware_ignores_non_asset(monkeypatch):
    app = FastAPI()
    app.add_middleware(AccessLogMiddleware)

    @app.get("/metrics")
    def _metrics(): return "ok"

    written = []
    import middleware.access_log as m
    monkeypatch.setattr(m, "DbSession", lambda: _FakeSession(written), raising=True)

    client = TestClient(app)
    assert client.get("/metrics").status_code == 200
    assert written == []