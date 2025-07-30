import copy
from unittest.mock import Mock

from starlette.testclient import TestClient

from database.model.agent.contact import Contact
from database.model.agent.organisation import Organisation
from database.session import DbSession

from tests.testutils.users import register_asset, logged_in_user
import io
import pytest

def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    organisation: Organisation,
    contact: Contact,
    body_agent: dict,
    auto_publish: None,
):
    body = copy.copy(body_agent)
    body["date_founded"] = "2023-01-01"
    body["legal_name"] = "A name for the organisation"
    body["ai_relevance"] = "Part of CLAIRE"
    body["type"] = "Research Institute"

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

    response = client.get(f"/organisations/{identifier}?get_image=false")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["identifier"] == identifier
    assert response_json["ai_resource_identifier"] == identifier
    assert response_json["agent_identifier"] == identifier

    assert response_json["date_founded"] == "2023-01-01"
    assert response_json["legal_name"] == "A name for the organisation"
    assert response_json["ai_relevance"] == "Part of CLAIRE"
    assert response_json["type"] == "research institute"
    assert response_json["member"] == body["member"]
    assert response_json["contact_details"] == body["contact_details"]
    assert response_json["contacts"][0]["name"] == "Aaron Bar"
    assert response_json["contacts"][0]["telephone"] == ["0032 xxxx xxxx"]
    assert response_json["contacts"][0]["email"] == ["a@b.com"]
    assert response_json["contacts"][0]["location"] == [
        {
            "address": {"country": "NED", "street": "Street Name 10", "postal_code": "1234AB"},
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

def test_organisation_image_post(
    client: TestClient
    ):
    with logged_in_user():
        response = client.post("/organisations", json={"name": "test organisation"}, headers={"Authorization": "Fake token"})

    assert response.status_code == 200, response.json()
    identifier = response.json()["identifier"]

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    response = client.post(
        f"/organisations/{identifier}/image",
        params={"name": "logo"},
        files={"file": ("logo.png", fake_image, "image/png")},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200, response.json()


def test_orgnisation_post_image_too_large(client: TestClient):
    with logged_in_user():
        response = client.post(
            "/organisations",
            json={"name": "test organisation"},
            headers={"Authorization": "Fake token"}
        )
    assert response.status_code == 200
    identifier = response.json()["identifier"]

    large_content = b"x" * (1 * 1024 * 1024 + 1)
    large_image = io.BytesIO(large_content)
    large_image.name = "big_logo.png"

    response = client.post(
        f"/organisations/{identifier}/image",
        params={"name": "big_logo"},
        files={"file": ("big_logo.png", large_image, "image/png")},
        headers={"Authorization": "Fake token"},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "File too large (max 1MB)"


def test_organisation_get_with_and_without_image(client: TestClient, organisation: Organisation):

    identifier = register_asset(organisation)

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    response = client.post(
        f"/organisations/{identifier}/image",
        params={"name": "logo"},
        files={"file": ("logo.png", fake_image, "image/png")},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200, response.json()

    response = client.get(f"/organisations/{identifier}?get_image=false")
    assert response.status_code == 200
    data = response.json()
    assert not data["media"][1].get("binary_blob")
    assert data["media"][1]["name"] == "logo"
    assert data["media"][1]["encoding_format"] == "image/png"

    response = client.get(f"/organisations/{identifier}?get_image=true")
    assert response.status_code == 200
    data = response.json()
    assert "media" in data and isinstance(data["media"], list)
    assert data["media"][1]["name"] == "logo"
    assert data["media"][1]["encoding_format"] == "image/png"
    assert data["media"][1]["binary_blob"]

def test_organisation_image_put(
    client: TestClient
    ):
    with logged_in_user():
        response = client.post("/organisations", json={"name": "test organisation"}, headers={"Authorization": "Fake token"})

    assert response.status_code == 200, response.json()
    identifier = response.json()["identifier"]

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    fake_image.name = "logo.png"

    response = client.post(
        f"/organisations/{identifier}/image",
        params={"name": "logo"},
        files={"file": ("logo.png", fake_image, "image/png")},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200, response.json()

    response = client.put(
        f"/organisations/{identifier}/image",
        params={"name": "LOGO"},
        files={"file": ("logo.png", fake_image, "image/png")},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No image with the name 'LOGO' found in the database."


    response = client.put(
        f"/organisations/{identifier}/image",
        params={"name": "logo"},
        files={"file": ("logo.png", fake_image, "image/png")},
        headers={"Authorization": "Fake token"},
    )

    assert response.status_code == 200, response.json()


def test_organisation_get_image(
    client: TestClient,
    organisation: Organisation
    ):

    identifier = register_asset(organisation)

    image_data = io.BytesIO(b"\x89PNG\r\n\x1a\nFAKEIMAGE")
    response = client.post(
        f"/organisations/{identifier}/image",
        params={"name": "logo"},
        files={"file": ("logo.png", image_data, "image/png")},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200, response.json()

    response = client.get(
        f"/organisations/{identifier}/image"
    )
    assert response.status_code == 200
    response = response.json()
    assert response[0]["binary_blob"]
    assert response[0]["name"] == "logo"
    assert response[0]["encoding_format"] == "image/png"


def test_organisation_delete_image(
    client: TestClient,
    organisation: Organisation
    ):

    identifier = register_asset(organisation)

    image_data = io.BytesIO(b"\x89PNG\r\n\x1a\nFAKEIMAGE")
    response = client.post(
        f"/organisations/{identifier}/image",
        params={"name": "logo"},
        files={"file": ("logo.png", image_data, "image/png")},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200, response.json()

    response = client.delete(
        f"/organisations/{identifier}/image",
        params={"name": "logo"},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200

    second_delete_response = client.delete(
        f"/organisations/{identifier}/image",
        params={"name": "logo"},
        headers={"Authorization": "Fake token"},
    )
    assert second_delete_response.status_code == 404
    assert "No image with the name" in second_delete_response.json()["detail"]
