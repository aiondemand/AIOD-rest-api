import copy
from unittest.mock import Mock

from starlette.testclient import TestClient

from authentication import keycloak_openid


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_resource: dict,
):
    keycloak_openid.userinfo = mocked_privileged_token
    body = copy.deepcopy(body_resource)
    body["headline"] = "A headline to show on top of the page."
    body["alternative_headline"] = "An alternative headline."
    body["category"] = ["research: education", "research: awards", "business: health"]
    body["content"] = {"plain": "plain content"}

    response = client.post("/news/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/news/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["headline"] == "A headline to show on top of the page."
    assert response_json["alternative_headline"] == "An alternative headline."
    assert set(response_json["category"]) == {
        "research: education",
        "research: awards",
        "business: health",
    }
    assert response_json["content"] == {"plain": "plain content"}
