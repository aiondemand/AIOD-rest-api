import copy
import pytest
from unittest.mock import Mock

from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.agent.contact import Contact
from database.model.agent.email import Email
from database.model.platform.platform import Platform
from database.session import DbSession
from tests.testutils.default_instances import _create_class_with_body
from tests.testutils.default_sqlalchemy import AI4EUROPE_CMS_TOKEN
from tests.testutils.users import logged_in_user


def test_happy_path(client: TestClient, body_asset: dict, auto_publish: None):
    with logged_in_user():
        response = client.post(
            "/persons", json={"name": "test person"}, headers={"Authorization": "Fake token"}
        )
    person_identifier = response.json()['identifier']

    body = copy.deepcopy(body_asset)
    body["name"] = "Contact name"
    body["email"] = ["a@b.com"]
    body["telephone"] = ["0032 xxxx xxxx"]
    body["location"] = [
        {
            "address": {"country": "NED", "street": "Street Name 10", "postal_code": "1234AB"},
            "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
        }
    ]
    body["person"] = person_identifier

    with logged_in_user():
        response = client.post("/contacts", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    with logged_in_user():  # Authenticated users should not get masked e-mail addresses
        response = client.get(f"/contacts/{identifier}", headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["name"] == "Contact name"
    assert response_json["email"] == ["a@b.com"]
    assert response_json["telephone"] == ["0032 xxxx xxxx"]
    assert response_json["location"] == [
        {
            "address": {"country": "NED", "street": "Street Name 10", "postal_code": "1234AB"},
            "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
        }
    ]
    assert response_json["person"] == person_identifier


def test_post_duplicate_email(
    client: TestClient,
    auto_publish: None,
):
    """
    It should be possible to add same email in different contacts, to enable
    """
    body1 = {"email": ["a@example.com", "b@example.com"]}
    body2 = {"email": ["c@example.com", "b@example.com"]}
    # Authenticated users should not get masked e-mail addresses
    with logged_in_user():
        response = client.post("/contacts", json=body1, headers={"Authorization": "Fake token"})
        assert response.status_code == 200, response.json()
        first_contact_identifier = response.json()['identifier']

        response = client.post("/contacts", json=body2, headers={"Authorization": "Fake token"})
        assert response.status_code == 200, response.json()
        second_contact_identifier = response.json()['identifier']

        contact = client.get(f"/contacts/{second_contact_identifier}", headers={"Authorization": "Fake token"}).json()
        assert set(contact["email"]) == {"b@example.com", "c@example.com"}

        body3 = {"email": ["d@example.com", "b@example.com"]}
        client.put(f"/contacts/{first_contact_identifier}", json=body3, headers={"Authorization": "Fake token"})
        contact = client.get(f"/contacts/{second_contact_identifier}", headers={"Authorization": "Fake token"}).json()
        msg = "changing emails of contact 1 should not change emails of contact 2."
        assert set(contact["email"]) == {"b@example.com", "c@example.com"}, msg


@pytest.mark.skip(reason="https://github.com/aiondemand/AIOD-rest-api/issues/518")
def test_person_and_organisation_both_specified(client: TestClient):
    headers = {"Authorization": "Fake token"}
    body = {"person": 1, "organisation": 1}
    with logged_in_user():
        client.post("/persons", json={"name": "test person"}, headers=headers)
        client.post("/organisations", json={"name": "test organisation"}, headers=headers)
        response = client.post("/contacts", json=body, headers=headers)
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "Person and organisation cannot be both filled."


@pytest.fixture
def contact2(body_concept) -> Contact:
    body = copy.copy(body_concept)
    body["platform"] = "aiod"
    body["platform_resource_identifier"] = "fake:100"
    body["email"] = ["fake@email.com", "fake2@email.com"]
    return _create_class_with_body(Contact, body)


@pytest.mark.parametrize(
    "endpoint",
    [
        "/contacts",
        "/contacts/1",
        "/platforms/aiod/contacts",
        "/platforms/aiod/contacts/fake:100",
    ]
)
def test_email_mask_for_not_authenticated_user(
    client: TestClient,
    mocked_privileged_token: Mock,
    contact: Contact,
    contact2: Contact,
    endpoint: str,
    auto_publish: None,
):
    with DbSession() as session:
        session.add(contact)
        session.add(contact2)
        session.commit()
        session.refresh(contact)

    # clunky way to account for random identifier because only 1 endpoint matches this pattern
    endpoint = endpoint.replace("/1", f"/{contact.identifier}")
    guest_response = client.get(endpoint)
    assert guest_response.status_code == 200, guest_response.json()
    guest_response_json = guest_response.json()
    if not isinstance(guest_response_json, list):
        guest_response_json = [guest_response_json]

    assert len(guest_response_json) > 0, guest_response_json
    for contact_json in guest_response_json:
        assert contact_json["email"] == ["******"]


def test_email_mask_for_authenticated_user(
    client: TestClient,
    mocked_privileged_token: Mock,
    overwrites_keycloak_token: None,  # Technically already used by privileged token, but we also overwrite explicitly  # noqa: E501
    contact: Contact,
    contact2: Contact,
    auto_publish: None,
):
    headers = {"Authorization": "Fake token"}

    with DbSession() as session:
        contact.platform = 'aiod'
        contact.platform_resource_identifier = '1'
        session.add(contact)
        session.add(contact2)
        session.commit()
        session.refresh(contact2)

    response = client.get("/contacts", headers=headers)
    response_json = response.json()
    assert response.status_code == 200, response_json
    assert len(response_json) == 2, response_json
    assert response_json[0]["email"] == ["a@b.com"]
    assert set(response_json[1]["email"]) == {"fake2@email.com", "fake@email.com"}

    response = client.get(f"/contacts/{contact2.identifier}", headers=headers)
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert set(response_json["email"]) == {"fake2@email.com", "fake@email.com"}
    response = client.get("/platforms/aiod/contacts/", headers=headers)

    response_json = response.json()
    assert response.status_code == 200, response_json

    assert len(response_json) == 2, response_json
    assert response_json[0]["email"] == ["a@b.com"]
    assert set(response_json[1]["email"]) == {"fake2@email.com", "fake@email.com"}

    response = client.get("/platforms/aiod/contacts/fake:100", headers=headers)
    response_json = response.json()
    assert response.status_code == 200, response_json
    assert set(response_json["email"]) == {"fake2@email.com", "fake@email.com"}


@pytest.mark.parametrize(
    "endpoint",
    [
        "/contacts",
        "/contacts/1",
        "/platforms/ai4europe_cms/contacts",
        "/platforms/ai4europe_cms/contacts/fake:100",
    ]
)
def test_email_privacy_for_ai4europe_cms(
    client: TestClient,
    mocked_privileged_token: Mock,
    contact: Contact,
    platform: Platform,
    endpoint: str,
    auto_publish: None,
):

    with DbSession() as session:
        contact.platform = "ai4europe_cms"
        contact.platform_resource_identifier = "fake:100"
        email = Email(name="fake@email.com")
        another_email = Email(name="fake2@email.com")
        contact.email = [email, another_email]
        session.add(contact)
        session.commit()
        session.refresh(contact)

    headers = {"Authorization": "Fake token"}

    endpoint = endpoint.replace("/1", f"/{contact.identifier}")
    response = client.get(endpoint, headers=headers)
    response_json = response.json()
    if isinstance(response_json, list):
        response_json = response_json[0]

    assert response.status_code == 200, response_json
    assert len(response_json) > 0, response_json
    assert response_json["email"] == ["******"]

    keycloak_openid.introspect = AI4EUROPE_CMS_TOKEN

    response = client.get(endpoint, headers=headers)
    response_json = response.json()
    if isinstance(response_json, list):
        response_json = response_json[0]

    assert response.status_code == 200, response_json
    assert len(response_json) > 0, response_json
    assert response_json["email"] == ["fake@email.com", "fake2@email.com"]
