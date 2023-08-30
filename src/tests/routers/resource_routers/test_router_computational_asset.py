import copy
from unittest.mock import Mock

from starlette.testclient import TestClient

from authentication import keycloak_openid


def test_happy_path(client: TestClient, mocked_privileged_token: Mock, body_asset: dict):
    keycloak_openid.userinfo = mocked_privileged_token

    body = copy.deepcopy(body_asset)
    body["status_info"] = "https://www.example.com/cluster-status"
    body["type"] = "storage"

    response = client.post(
        "/computational_assets/v1", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200, response.json()

    response = client.get("/computational_assets/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["status_info"] == "https://www.example.com/cluster-status"
    assert response_json["type"] == "storage"
