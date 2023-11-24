import copy
from unittest.mock import Mock

from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.agent.person import Person
from database.session import DbSession


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_asset: dict,
    person: Person,
):
    keycloak_openid.userinfo = mocked_privileged_token

    with DbSession() as session:
        session.add(person)
        session.commit()

    body = copy.deepcopy(body_asset)
    body["issn"] = "20493630"
    body["measurement_technique"] = "mass spectrometry"
    body["temporal_coverage"] = "2011/2012"

    body["funder"] = [1]
    body["size"] = {"unit": "Rows", "value": "100"}
    body["spatial_coverage"] = {
        "address": {"country": "NED", "street": "Street Name 10", "postal_code": "1234AB"},
        "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
    }

    response = client.post("/datasets/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/datasets/v1/1")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["issn"] == "20493630"
    assert response_json["measurement_technique"] == "mass spectrometry"
    assert response_json["temporal_coverage"] == "2011/2012"

    assert response_json["funder"] == [1]
    assert response_json["size"] == {"unit": "Rows", "value": 100}
    assert response_json["spatial_coverage"] == {
        "address": {"country": "NED", "street": "Street Name 10", "postal_code": "1234AB"},
        "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
    }
    # TODO: test delete
