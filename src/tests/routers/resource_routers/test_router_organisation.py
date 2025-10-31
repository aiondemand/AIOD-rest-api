import copy
from unittest.mock import Mock

from fastapi.encoders import jsonable_encoder
from starlette.testclient import TestClient

from database.model.agent.contact import Contact
from database.model.agent.organisation import Organisation, Turnover,NumberOfEmployees
from database.session import DbSession

import pytest
from tests.testutils.users import register_asset, logged_in_user
import io
from routers.resource_routers.organisation_router import ALLOWED_IMAGE_TYPES
from http import HTTPStatus

from taxonomies.synchronize_taxonomy import synchronize

STANDARD_TURNOVER_VALUES = ["<1 million euros", ">1 million euros", ">3 million euros", ">5 million euros", ">50 million euros", ">1.5 billion euros"]

@pytest.fixture
def with_organisation_taxonomies():
    with DbSession() as session:
        synchronize(
            NumberOfEmployees,
            [
                NumberOfEmployees(name=value,definition="", official=True, children=[])
                for value in ["<10", "<50", "<250", ">=250"]
            ],
            session
        )
        synchronize(
            Turnover,
            [
                Turnover(name=value,definition="", official=True, children=[])
                for value in STANDARD_TURNOVER_VALUES
            ],
            session
        )
        session.commit()
    yield


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    organisation: Organisation,
    contact: Contact,
    body_agent: dict,
    auto_publish: None,
    with_organisation_taxonomies,
):
    body = copy.copy(body_agent)
    body["date_founded"] = "2023-01-01"
    body["legal_name"] = "A name for the organisation"
    body["ai_relevance"] = "Part of CLAIRE"
    body["type"] = "Research University"
    body["turnover"] = "<1 million euros"
    with DbSession() as session:
        session.add(organisation)  # The new organisation will be a member of this organisation
        session.add(contact)
        session.commit()

        body["member"] = [organisation.identifier]
        body["contact_details"] = contact.identifier
        body["contact"] = [contact.identifier]

    response = client.post("/organisations", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/organisations/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["identifier"] == identifier
    assert response_json["ai_resource_identifier"] == identifier
    assert response_json["agent_identifier"] == identifier

    assert response_json["date_founded"] == "2023-01-01"
    assert response_json["legal_name"] == "A name for the organisation"
    assert response_json["ai_relevance"] == "Part of CLAIRE"
    assert response_json["type"] == "research university"
    assert response_json["turnover"] == "<1 million euros"
    assert response_json["member"] == body["member"]
    assert response_json["contact_details"] == body["contact_details"]
    assert response_json["contacts"][0]["name"] == "Aaron Bar"
    assert response_json["contacts"][0]["telephone"] == ["0032 xxxx xxxx"]
    assert response_json["contacts"][0]["email"] == ["a@b.com"]
    assert response_json["contacts"][0]["location"] == [
        {
            "address": {"country": "Spain", "street": "Street Name 10", "postal_code": "1234AB"},
            "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
        }
    ]

    # response = client.delete("/organisations/1", headers={"Authorization": "Fake token"})
    # assert response.status_code == 200
    # response = client.get("/organisations/2")
    # assert response.status_code == 200, response.json()
    # response_json = response.json()
    # TODO(jos): make sure Agent is deleted on CASCADE

    body["type"] = "Association"
    response = client.put(f"organisations/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    response = client.get(f"organisations/{identifier}?get_image=false")
    assert response.json()["type"] == "association"

    body["number_of_employees"] = "<50"
    response = client.put(f"organisations/{identifier}", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    response = client.get(f"organisations/{identifier}")
    assert response.json()["number_of_employees"] == "<50"

    response = client.delete(f"/organisations/{identifier}", headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()


def test_ai_resource_contacts_field_is_ignored(
        client: TestClient,
        mocked_privileged_token: Mock,
        organisation: Organisation,
        contact: Contact,
        body_agent: dict,
        auto_publish: None,
):
    with DbSession() as session:
        session.add(contact)
        session.commit()
        session.refresh(contact)

    body = copy.copy(body_agent)
    body["contacts"] = [contact.json()]
    response = client.post("/organisations", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/organisations/{identifier}")
    assert response.status_code == 200, response.json()
    assert response.json()["contacts"] == []


def test_organisation_post_image(
    client: TestClient,
    organisation: Organisation,
    ):

    identifier = register_asset(organisation)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    with logged_in_user():
        response = client.post(
            f"/organisations/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )
    assert response.status_code == HTTPStatus.OK, response.json()


def test_organisation_put_without_media_keeps_media(
        client: TestClient,
        organisation: Organisation,
):
    organisation.media = []
    identifier = register_asset(organisation)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    with logged_in_user():
        response = client.post(
            f"/organisations/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()

        organisation.name = "new name"
        response = client.put(
            f"/organisations/{identifier}",
            json=jsonable_encoder(organisation.dict()),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()
        response = client.get(
            f"/organisations/{identifier}",
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()
        assert response.json()["name"] == "new name", response.json()
        assert response.json()["media"], response.json()


def test_organisation_put_with_media_keeps_media_if_no_new_binary(
        client: TestClient,
        organisation: Organisation,
):
    organisation.media = []
    identifier = register_asset(organisation)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    with logged_in_user():
        response = client.post(
            f"/organisations/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", fake_image, "image/png")},
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()

        response = client.get(
            f"/organisations/{identifier}?get_image=true",
            headers={"Authorization": "Fake token"},
        )
        org = response.json()
        del org["aiod_entry"]
        org["media"].append(
            {"name": "foo", "binary_blob": "bar="},
        )
        response = client.put(
            f"/organisations/{identifier}",
            json=org,
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST, "No new binary may be added through a PUT request"

        org["media"].pop()
        response = client.put(
            f"/organisations/{identifier}",
            json=org,
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()
