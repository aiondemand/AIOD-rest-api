from sqlalchemy import Engine
from starlette.testclient import TestClient


def test_happy_path(client: TestClient, engine: Engine):
    response = client.get("/platforms/v0")
    assert response.status_code == 200
    response_json = response.json()

    assert set(response_json) == {"aiod", "openml", "huggingface", "example", "zenodo"}
