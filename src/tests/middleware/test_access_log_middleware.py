from fastapi import FastAPI
from starlette.testclient import TestClient
import pytest

from middleware.access_log import AccessLogMiddleware

# simple in-memory recorder instead of touching a real DB
class _FakeSession:
    def __init__(self, store): self._store = store
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def add(self, entry): self._store.append(entry)
    def commit(self): pass


def test_middleware_logs_asset_hit(monkeypatch):
    app = FastAPI()
    app.add_middleware(AccessLogMiddleware)

    @app.get("/datasets/data_foobar12foobar12foobar12")
    def _ok(): return {"ok": True}

    written = []
    import middleware.access_log as m
    monkeypatch.setattr(m, "DbSession", lambda: _FakeSession(written), raising=True)

    client = TestClient(app)
    r = client.get("/datasets/data_foobar12foobar12foobar12")
    assert r.status_code == 200

    assert len(written) == 1
    entry = written[0]
    assert entry.resource_type == "datasets"
    assert entry.asset_id == "data_foobar12foobar12foobar12"
    assert entry.status == 200


def test_middleware_logs_404_asset(monkeypatch):
    app = FastAPI()
    app.add_middleware(AccessLogMiddleware)

    written = []
    import middleware.access_log as m
    monkeypatch.setattr(m, "DbSession", lambda: _FakeSession(written), raising=True)

    client = TestClient(app)
    r = client.get("/v2/ml_models/mdl_bertbertbertbertbertbert")
    assert r.status_code == 404

    assert len(written) == 1
    entry = written[0]
    assert entry.resource_type == "ml_models"
    assert entry.asset_id == "mdl_bertbertbertbertbertbert"
    assert entry.status == 404

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
