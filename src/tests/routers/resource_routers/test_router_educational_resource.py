import copy
from unittest.mock import Mock

from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from authentication import keycloak_openid


def test_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_asset: dict,
):
    keycloak_openid.userinfo = mocked_privileged_token

    body = copy.deepcopy(body_asset)
    body["level"] = "EQF Level 3"
    body["type"] = "presentation"

    response = client.post(
        "/educational_resources/v1", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200, response.json()

    response = client.get("/educational_resources/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["level"] == "EQF Level 3"
    assert response_json["type"] == "presentation"
