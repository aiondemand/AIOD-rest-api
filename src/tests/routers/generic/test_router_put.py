from unittest.mock import Mock

import pytest
from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from authentication import keycloak_openid


@pytest.mark.parametrize(
    "title",
    ["\"'é:?", "!@#$%^&*()`~", "Ω≈ç√∫˜µ≤≥÷", "田中さんにあげて下さい", " أي بعد, ", "𝑻𝒉𝒆 𝐪𝐮𝐢𝐜𝐤", "گچپژ"],
)
def test_unicode(
    client_test_resource: TestClient,
    engine_test_resource_filled: Engine,
    title: str,
    mocked_privileged_token: Mock,
):
    keycloak_openid.userinfo = mocked_privileged_token
    response = client_test_resource.put(
        "/test_resources/v0/1",
        json={"title": title, "platform": "openml", "platform_resource_identifier": "2"},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200, response.json()
    response = client_test_resource.get("/test_resources/v0/1")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert response_json["title"] == title
    assert response_json["platform"] == "openml"
    assert response_json["platform_resource_identifier"] == "2"


def test_non_existent(
    client_test_resource: TestClient,
    engine_test_resource_filled: Engine,
    mocked_privileged_token: Mock,
):
    keycloak_openid.userinfo = mocked_privileged_token
    response = client_test_resource.put(
        "/test_resources/v0/2",
        json={"title": "new_title", "platform": "other", "platform_resource_identifier": "2"},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 404, response.json()
    response_json = response.json()
    assert response_json["detail"] == "Test_resource '2' not found in the database."


def test_too_long_name(
    client_test_resource: TestClient,
    engine_test_resource_filled: Engine,
    mocked_privileged_token: Mock,
):
    keycloak_openid.userinfo = mocked_privileged_token
    name = "a" * 251
    response = client_test_resource.put(
        "/test_resources/v0/1", json={"title": name}, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 422, response.json()
    response_json = response.json()
    assert response_json["detail"] == [
        {
            "ctx": {"limit_value": 250},
            "loc": ["body", "title"],
            "msg": "ensure this value has at most 250 characters",
            "type": "value_error.any_str.max_length",
        }
    ]


def test_no_platform_with_platform_resource_identifier(
    client_test_resource: TestClient,
    engine_test_resource_filled: Engine,
    mocked_privileged_token: Mock,
):
    """
    The error handling should be the same as with the POST endpoints, so we're not testing all
    the possible UNIQUE / CHECK constraints here, just this one.
    """
    keycloak_openid.userinfo = mocked_privileged_token
    response = client_test_resource.put(
        "/test_resources/v0/1",
        json={"title": "title", "platform": "other", "platform_resource_identifier": None},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 400, response.json()
    assert (
        response.json()["detail"]
        == "If platform is NULL, platform_resource_identifier should also be "
        "NULL, and vice versa."
    )
