import copy
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.agent.contact import Contact
from database.model.agent.person import Person
from database.model.platform.platform import Platform
from database.session import DbSession


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_agent: dict,
    person: Person,
    contact: Contact,
):
    keycloak_openid.introspect = mocked_privileged_token

    with DbSession() as session:
        person.platform_resource_identifier = "2"
        session.add(person)
        session.add(contact)
        session.commit()

    body = copy.copy(body_agent)
    body["expertise"] = ["machine learning"]
    body["language"] = ["eng", "nld"]
    body["price_per_hour_euro"] = 10.50
    body["wants_to_be_contacted"] = True
    body["contact_details"] = 1

    response = client.post("/persons/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/persons/v1/2")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["identifier"] == 2
    assert response_json["ai_resource_identifier"] == 2
    assert response_json["agent_identifier"] == 2

    assert set(response_json["expertise"]) == {"machine learning"}
    assert set(response_json["language"]) == {"eng", "nld"}

    assert response_json["price_per_hour_euro"] == 10.50
    assert response_json["wants_to_be_contacted"]
    assert response_json["contact_details"] == 1


@pytest.fixture(
    params=[
        "/persons/v1",
        "/persons/v1/1",
        "/platforms/ai4europe_cms/persons/v1",
        "/platforms/ai4europe_cms/persons/v1/2",
    ]
)
def endpoint(request) -> str:
    return request.param


def test_privacy_for_ai4europe_cms(
    client: TestClient,
    mocked_privileged_token: Mock,
    mocked_ai4europe_cms_token: Mock,
    platform: Platform,
    person: Person,
    contact: Contact,
    endpoint: str,
):
    """Test to ensure that only authenticated users with "full_view_ai4europe_cms_resources" role
    can visualise fields such as name, given_name and surname of a person migrated from
    the old ai4europe_cms platform.
    """

    with DbSession() as session:
        person.platform = "ai4europe_cms"
        person.platform_resource_identifier = "2"
        person.name = "Joe Doe"
        person.given_name = "Joe"
        person.surname = "Doe"
        session.add(person)
        session.add(contact)
        session.commit()

    headers = {"Authorization": "Fake token"}
    keycloak_openid.introspect = mocked_privileged_token

    response = client.get(endpoint, headers=headers)
    response_json = response.json()
    response_json = [response_json] if isinstance(response_json, dict) else response_json
    assert response.status_code == 200, response_json
    for person_dict in response_json:
        assert person_dict["name"] == "******"
        assert person_dict["given_name"] == "******"
        assert person_dict["surname"] == "******"

    keycloak_openid.introspect = mocked_ai4europe_cms_token
    response = client.get(endpoint, headers=headers)
    response_json = response.json()
    response_json = [response_json] if isinstance(response_json, dict) else response_json
    assert response.status_code == 200, response_json
    for person_dict in response_json:
        assert person_dict["name"] == "Joe Doe"
        assert person_dict["given_name"] == "Joe"
        assert person_dict["surname"] == "Doe"
