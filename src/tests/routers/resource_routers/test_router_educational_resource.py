import copy
from unittest.mock import Mock

from starlette.testclient import TestClient

from authentication import keycloak_openid


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_asset: dict,
):
    keycloak_openid.userinfo = mocked_privileged_token

    body = copy.deepcopy(body_asset)
    body["time_required"] = "3 weeks"
    body["type"] = "presentation"
    body["pace"] = "self-paced"
    body["access_mode"] = ["textual", "online course"]
    body["educational_level"] = ["secondary school", "university"]
    body["in_language"] = ["nld", "eng"]
    locations = [
        {
            "address": {"country": "NED", "street": "Street Name 10", "postal_code": "1234AB"},
        },
        {
            "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
        },
    ]
    body["location"] = locations
    body["prerequisite"] = [
        "undergraduate knowledge of statistics",
        "graduate knowledge of linear algebra",
    ]
    body["target_audience"] = ["professionals", "professors"]
    body["content"] = {"plain": "plain content"}

    response = client.post(
        "/educational_resources/v1", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200, response.json()

    response = client.get("/educational_resources/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["type"] == "presentation"
    assert response_json["time_required"] == "3 weeks"
    assert response_json["type"] == "presentation"
    assert response_json["pace"] == "self-paced"
    assert set(response_json["access_mode"]) == {"textual", "online course"}
    assert set(response_json["educational_level"]) == {"secondary school", "university"}
    assert set(response_json["in_language"]) == {"nld", "eng"}
    assert response_json["location"] == locations
    assert set(response_json["prerequisite"]) == {
        "undergraduate knowledge of statistics",
        "graduate knowledge of linear algebra",
    }
    assert set(response_json["target_audience"]) == {"professionals", "professors"}
    assert response_json["content"] == {"plain": "plain content"}
