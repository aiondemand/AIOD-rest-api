import copy
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.agent.contact import Contact
from database.model.agent.person import Person
from database.model.agent.organisation import Organisation
from database.model.platform.platform import Platform
from database.session import DbSession
from tests.testutils.default_sqlalchemy import AI4EUROPE_CMS_TOKEN


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_agent: dict,
    person: Person,
    contact: Contact,
    organisation: Organisation,
    auto_publish: None,
):
    body = copy.copy(body_agent)
    body["expertise"] = ["machine learning"]
    body["languages"] = ["eng", "nld"]
    body["price_per_hour_euro"] = 10.50
    body["wants_to_be_contacted"] = True
    with DbSession() as session:
        session.add(person)
        session.add(contact)
        session.merge(organisation)
        session.commit()
        body["contact_details"] = contact.identifier
        body["member_of"] = [organisation.identifier]


    response = client.post("/persons", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/persons/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["identifier"] == identifier
    assert response_json["ai_resource_identifier"] == identifier
    assert response_json["agent_identifier"] == identifier

    assert set(response_json["expertise"]) == {"machine learning"}
    assert set(response_json["languages"]) == {"eng", "nld"}

    assert response_json["price_per_hour_euro"] == 10.50
    assert response_json["wants_to_be_contacted"]
    assert response_json["contact_details"] == body["contact_details"]
    assert response_json["member_of"] == body["member_of"]

    assert response_json["platform"] == "aiod"
    assert response_json["platform_resource_identifier"] == response_json["identifier"]


@pytest.mark.parametrize(
    "endpoint",
    [
        "/persons",
        "/persons/1",
        "/platforms/ai4europe_cms/persons",
        "/platforms/ai4europe_cms/persons/2",
    ]
)
def test_privacy_for_ai4europe_cms(
    client: TestClient,
    mocked_privileged_token: Mock,
    overwrites_keycloak_token: None,  # Technically already used by privileged token, but we also overwrite explicitly  # noqa: E501
    platform: Platform,
    person: Person,
    contact: Contact,
    endpoint: str,
    auto_publish: None,
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
        session.refresh(person)
        session.refresh(contact)

    headers = {"Authorization": "Fake token"}

    endpoint = endpoint.replace("/1", f"/{person.identifier}")
    response = client.get(endpoint, headers=headers)
    response_json = response.json()
    response_json = [response_json] if isinstance(response_json, dict) else response_json
    assert response.status_code == 200, response_json
    for person_dict in response_json:
        assert person_dict["name"] == "******"
        assert person_dict["given_name"] == "******"
        assert person_dict["surname"] == "******"

    keycloak_openid.introspect = AI4EUROPE_CMS_TOKEN
    response = client.get(endpoint, headers=headers)
    response_json = response.json()
    response_json = [response_json] if isinstance(response_json, dict) else response_json
    assert response.status_code == 200, response_json
    for person_dict in response_json:
        assert person_dict["name"] == "Joe Doe"
        assert person_dict["given_name"] == "Joe"
        assert person_dict["surname"] == "Doe"
