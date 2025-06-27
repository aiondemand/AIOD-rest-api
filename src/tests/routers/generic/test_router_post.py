
import pytest
from starlette.testclient import TestClient

from tests.testutils.users import logged_in_user, kc_connector_with_roles
from database.model.platform.platform_names import PlatformName
from http import HTTPStatus


@pytest.mark.parametrize(
    "title",
    ["\"'é:?", "!@#$%^&*()`~", "Ω≈ç√∫˜µ≤≥÷", "田中さんにあげて下さい", " أي بعد, ", "𝑻𝒉𝒆 𝐪𝐮𝐢𝐜𝐤", "گچپژ"],
)
def test_unicode(client_test_resource: TestClient, title: str, auto_publish: None):
    with logged_in_user():
        response = client_test_resource.post(
            "/test_resources/v0",
            json={"title": title},
            headers={"Authorization": "Fake token"},
        )
    assert response.status_code == 200, response.json()
    assert "identifier" in response.json()
    identifier = response.json()["identifier"]

    response = client_test_resource.get(f"/test_resources/v0/{identifier}")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert response_json["title"] == title
    assert response_json["platform"] == PlatformName.aiod


def test_missing_value(client_test_resource: TestClient):
    body: dict[str, str] = {}
    with logged_in_user():
        response = client_test_resource.post(
            "/test_resources/v0", json=body, headers={"Authorization": "Fake token"}
        )
    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == [
        {"loc": ["body", "title"], "msg": "field required", "type": "value_error.missing"}
    ]


def test_null_value(client_test_resource: TestClient):
    body = {"title": None}
    with logged_in_user():
        response = client_test_resource.post(
            "/test_resources/v0", json=body, headers={"Authorization": "Fake token"}
        )
    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == [
        {
            "loc": ["body", "title"],
            "msg": "none is not an allowed value",
            "type": "type_error.none.not_allowed",
        }
    ]

# Prevents a connector from posting the same item twice.
def test_posting_same_item_twice(client_test_resource: TestClient):
    headers = {"Authorization": "Fake token"}
    body = {"title": "title1", "platform": "example", "platform_resource_identifier": "1"}
    connector_user = kc_connector_with_roles()

    with logged_in_user(connector_user):
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)

    assert response.status_code == 200, response.json()
    identifier = response.json()["identifier"]
    body = {"title": "title2", "platform": "example", "platform_resource_identifier": "1"}
    with logged_in_user(connector_user):
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)
    assert response.status_code == 409, response.json()
    assert (
        response.json()["detail"]
        == f"There already exists a test_resource with the same platform and platform_resource_identifier, with identifier={identifier}."
    )


def test_posting_same_item_twice_but_deleted(
    client_test_resource: TestClient
):
    headers = {"Authorization": "Fake token"}
    body = {"title": "title1"}
    with logged_in_user():
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)
    identifier = response.json()["identifier"]
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    with logged_in_user():
        response = client_test_resource.delete(f"/test_resources/v0/{identifier}", headers=headers)
    assert response.status_code == 200, response.json()

    body = {"title": "title2"}
    with logged_in_user():
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)
    assert response.status_code == 200, response.json()


def test_platform_and_platform_identifier_defaults_are_set_if_not_provided(
    client_test_resource: TestClient
):
    """
    The platform and platform_resource_identifier are set by the server.
    """
    headers = {"Authorization": "Fake token"}
    body = {"title": "title1", "platform": None, "platform_resource_identifier": None}
    with logged_in_user():
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)
    assert response.status_code == 200, response.json()

    body = {"title": "title2", "platform": None, "platform_resource_identifier": None}
    with logged_in_user():
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)
    assert response.status_code == 200, response.json()

def test_post_platform_and_platform_resource_identifier_rejected(
    client_test_resource: TestClient
):
    headers = {"Authorization": "Fake token"}
    body = {"title": "title1", "platform": "aiod", "platform_resource_identifier": 2}
    with logged_in_user():
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == (
        "No permission to set platform or platform resource identifier.")



def test_no_platform_with_platform_resource_identifier(
    client_test_resource: TestClient
):
    headers = {"Authorization": "Fake token"}
    body = {"title": "title1", "platform": None, "platform_resource_identifier": "1"}
    with logged_in_user():
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)
    assert response.status_code == HTTPStatus.FORBIDDEN, response.json()
    assert (
        response.json()["detail"]
        == "No permission to set platform or platform resource identifier."
    )


def test_platform_with_no_platform_resource_identifier(
    client_test_resource: TestClient
):
    headers = {"Authorization": "Fake token"}
    body = {"title": "title1", "platform": "example", "platform_resource_identifier": None}
    with logged_in_user():
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)
    assert response.status_code == HTTPStatus.FORBIDDEN, response.json()
    assert (
        response.json()["detail"]
        == "No permission to set platform or platform resource identifier."
    )

def test_connector_can_post_to_valid_platform(
    client_test_resource: TestClient,
):
    headers = {"Authorization": "Fake token"}
    connector_user = kc_connector_with_roles()
    body = {
        "title": "ConnectorResource",
        "platform": "example",
        "platform_resource_identifier": "conn-123"
    }
    with logged_in_user(connector_user):
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)
    assert response.status_code == 200


def test_connector_cannot_post_to_other_platform(
    client_test_resource: TestClient,
):
    headers = {"Authorization": "Fake token"}
    connector_user = kc_connector_with_roles()
    body = {
        "title": "ConnectorResource",
        "platform": "aiod",
        "platform_resource_identifier": "conn-123"
    }
    with logged_in_user(connector_user):
        response = client_test_resource.post("/test_resources/v0", json=body, headers=headers)
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == "No permission to upload assets for aiod platform."
