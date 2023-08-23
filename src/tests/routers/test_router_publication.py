import copy
from unittest.mock import Mock

from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.dataset.dataset import Dataset


def test_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset: dict,
    dataset: Dataset,
):
    keycloak_openid.userinfo = mocked_privileged_token

    body = copy.copy(body_asset)
    body["permanent_identifier"] = "http://dx.doi.org/10.1093/ajae/aaq063"
    body["isbn"] = "9783161484100"
    body["issn"] = "20493630"
    body["type"] = "journal"

    response = client.post("/publications/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/publications/v1/1")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json["permanent_identifier"] == "http://dx.doi.org/10.1093/ajae/aaq063"
    assert response_json["isbn"] == "9783161484100"
    assert response_json["issn"] == "20493630"
    assert response_json["type"] == "journal"
