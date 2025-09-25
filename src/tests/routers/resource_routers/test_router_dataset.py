import copy
from unittest.mock import Mock

from starlette import status
from starlette.testclient import TestClient

from database.model.agent.person import Person
from database.session import DbSession
from tests.testutils.users import logged_in_user


def test_happy_path(
    client: TestClient,
    body_asset: dict,
    person: Person,
    auto_publish: None,
):
    with DbSession() as session:
        session.add(person)
        session.commit()
        session.refresh(person)

    body = copy.deepcopy(body_asset)
    body["issn"] = "20493630"
    body["measurement_technique"] = "mass spectrometry"
    body["temporal_coverage"] = "2011/2012"

    body["funder"] = [person.identifier]
    body["size"] = {"unit": "Rows", "value": "100"}
    body["spatial_coverage"] = {
        "address": {"country": "Spain", "street": "Street Name 10", "postal_code": "1234AB"},
        "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
    }

    with logged_in_user():
        response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/datasets/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["issn"] == "20493630"
    assert response_json["measurement_technique"] == "mass spectrometry"
    assert response_json["temporal_coverage"] == "2011/2012"

    assert response_json["funder"] == [person.identifier]
    assert response_json["size"] == {"unit": "Rows", "value": 100}
    assert response_json["spatial_coverage"] == {
        "address": {"country": "Spain", "street": "Street Name 10", "postal_code": "1234AB"},
        "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
    }
    # TODO: test delete


def test_post_invalid_huggingface_identifier(
    client: TestClient,
    mocked_privileged_token: Mock,
):
    body = {"name": "name", "platform": "huggingface", "platform_resource_identifier": ""}

    response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.json()
    assert (
        response.json()["detail"][0]["msg"]
        == "Repo id must use alphanumeric chars or '-', '_', '.', '--' and '..' are"
        " forbidden, '-' and '.' cannot start or end the name, max length is 96:"
        f" '{body['platform_resource_identifier']}'."
    )


def test_post_invalid_openml_identifier(
    client: TestClient,
    mocked_privileged_token: Mock,
):
    body = {"name": "name", "platform": "openml", "platform_resource_identifier": "a"}

    response = client.post("/datasets", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.json()
    assert (
        response.json()["detail"][0]["msg"]
        == "An OpenML platform_resource_identifier should be a positive integer."
    )
