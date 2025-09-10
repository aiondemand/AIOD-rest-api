from http import HTTPStatus
from unittest.mock import Mock

import pytest
from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from tests.testutils.users import logged_in_user, kc_user_with_roles


@pytest.mark.parametrize(
    "title",
    ["\"'é:?", "!@#$%^&*()`~", "Ω≈ç√∫˜µ≤≥÷", "田中さんにあげて下さい", " أي بعد, ", "𝑻𝒉𝒆 𝐪𝐮𝐢𝐜𝐤", "گچپژ"],
)
def test_unicode(
    client_test_resource: TestClient,
    engine_test_resource_filled: Engine,
    title: str,
):
    with logged_in_user(kc_user_with_roles("update_test_resources")):
        response = client_test_resource.put(
            f"/test_resources/{engine_test_resource_filled}",
            json={"title": title, "platform": "openml", "platform_resource_identifier": "2"},
            headers={"Authorization": "Fake token"},
        )
    assert response.status_code == 200, response.json()
    response = client_test_resource.get(f"/test_resources/{engine_test_resource_filled}")
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
    response = client_test_resource.put(
        "/test_resources/test_2",
        json={"title": "new_title", "platform": "other", "platform_resource_identifier": "2"},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 404, response.json()
    response_json = response.json()
    assert response_json["detail"] == "Test_resource 'test_2' not found in the database."


def test_wrong_identifier_type(
        client_test_resource: TestClient,
        engine_test_resource_filled: Engine,
        mocked_privileged_token: Mock,
):
    response = client_test_resource.put(
        "/test_resources/data_2",
        json={"title": "new_title", "platform": "other", "platform_resource_identifier": "2"},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.json()
    response_json = response.json()
    assert "is not a valid" in response_json["detail"]


def test_too_long_name(
    client_test_resource: TestClient,
    engine_test_resource_filled: Engine,
    mocked_privileged_token: Mock,
):
    name = "a" * 251
    response = client_test_resource.put(
        f"/test_resources/{engine_test_resource_filled}", json={"title": name}, headers={"Authorization": "Fake token"}
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
):
    """
    The error handling should be the same as with the POST endpoints, so we're not testing all
    the possible UNIQUE / CHECK constraints here, just this one.
    """
    with logged_in_user(kc_user_with_roles("update_test_resources")):
        response = client_test_resource.put(
            f"/test_resources/{engine_test_resource_filled}",
            json={"title": "title", "platform": "other", "platform_resource_identifier": None},
            headers={"Authorization": "Fake token"},
        )
    assert response.status_code == 400, response.json()
    assert (
        response.json()["detail"]
        == "If platform is NULL, platform_resource_identifier should also be "
        "NULL, and vice versa."
    )
