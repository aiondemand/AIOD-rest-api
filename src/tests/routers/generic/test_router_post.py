from http import HTTPStatus
import pytest
from starlette.testclient import TestClient

from tests.testutils.users import logged_in_user, kc_connector_with_roles
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create
from routers import resource_routers
from versioning import Version


@pytest.mark.parametrize(
    "title",
    [
        "\"'é:?",
        "!@#$%^&*()`~",
        "Ω≈ç√∫˜µ≤≥÷",
        "田中さんにあげて下さい",
        " أي بعد, ",
        "𝑻𝒉𝒆 𝐪𝐮𝐢𝐜𝐤",
        "گچپژ",
    ],
)
def test_unicode(client_test_resource: TestClient, title: str, auto_publish: None):
    with logged_in_user():
        response = client_test_resource.post(
            "/test_resources",
            json={"title": title},
            headers={"Authorization": "Fake token"},
        )

    assert response.status_code == 200, response.json()  # noqa: S101
    assert "identifier" in response.json()  # noqa: S101
    identifier = response.json()["identifier"]

    response = client_test_resource.get(f"/test_resources/{identifier}")
    assert response.status_code == 200, response.json()  # noqa: S101

    response_json = response.json()
    assert response_json["title"] == title  # noqa: S101
    assert response_json["platform"] == PlatformName.aiod  # noqa: S101


def test_missing_value(client_test_resource: TestClient):
    body: dict[str, str] = {}

    with logged_in_user():
        response = client_test_resource.post(
            "/test_resources",
            json=body,
            headers={"Authorization": "Fake token"},
        )

    assert response.status_code == 422, response.json()  # noqa: S101
    assert response.json()["detail"] == [  # noqa: S101
        {"loc": ["body", "title"], "msg": "field required", "type": "value_error.missing"}
    ]


def test_null_value(client_test_resource: TestClient):
    body = {"title": None}

    with logged_in_user():
        response = client_test_resource.post(
            "/test_resources",
            json=body,
            headers={"Authorization": "Fake token"},
        )

    assert response.status_code == 422, response.json()  # noqa: S101
    assert response.json()["detail"] == [  # noqa: S101
        {
            "loc": ["body", "title"],
            "msg": "none is not an allowed value",
            "type": "type_error.none.not_allowed",
        }
    ]


def test_posting_same_item_twice(client_test_resource: TestClient):
    headers = {"Authorization": "Fake token"}
    body = {"title": "title1", "platform": "example", "platform_resource_identifier": "1"}
    connector_user = kc_connector_with_roles()

    with logged_in_user(connector_user):
        response = client_test_resource.post("/test_resources", json=body, headers=headers)

    assert response.status_code == 200, response.json()  # noqa: S101

    identifier = response.json()["identifier"]

    body = {"title": "title2", "platform": "example", "platform_resource_identifier": "1"}

    with logged_in_user(connector_user):
        response = client_test_resource.post("/test_resources", json=body, headers=headers)

    assert response.status_code == 409, response.json()  # noqa: S101

    assert (  # noqa: S101
        response.json()["detail"]
        == (
            "There already exists a test_resource with the same platform "
            "and platform_resource_identifier, "
            f"with identifier={identifier}."
        )
    )


def test_posting_same_item_twice_but_deleted(client_test_resource: TestClient):
    headers = {"Authorization": "Fake token"}
    body = {"title": "title1"}

    with logged_in_user():
        response = client_test_resource.post("/test_resources", json=body, headers=headers)

    assert response.status_code == 200, response.json()  # noqa: S101
    identifier = response.json()["identifier"]

    with logged_in_user():
        response = client_test_resource.delete(f"/test_resources/{identifier}", headers=headers)

    assert response.status_code == 200, response.json()  # noqa: S101

    body = {"title": "title2"}

    with logged_in_user():
        response = client_test_resource.post("/test_resources", json=body, headers=headers)

    assert response.status_code == 200, response.json()  # noqa: S101


def test_platform_and_platform_identifier_defaults_are_set_if_not_provided(
    client_test_resource: TestClient,
):
    headers = {"Authorization": "Fake token"}

    body = {"title": "title1", "platform": None, "platform_resource_identifier": None}

    with logged_in_user():
        response = client_test_resource.post("/test_resources", json=body, headers=headers)

    assert response.status_code == 200, response.json()  # noqa: S101

    body = {"title": "title2", "platform": None, "platform_resource_identifier": None}

    with logged_in_user():
        response = client_test_resource.post("/test_resources", json=body, headers=headers)

    assert response.status_code == 200, response.json()  # noqa: S101


@pytest.mark.parametrize(
    "body,expected_status,expected_detail",
    [
        (
            {"title": "title1", "platform": "aiod", "platform_resource_identifier": 2},
            HTTPStatus.FORBIDDEN,
            "No permission to set platform or platform resource identifier.",
        ),
        (
            {"title": "title1", "platform": None, "platform_resource_identifier": "1"},
            HTTPStatus.FORBIDDEN,
            "No permission to set platform or platform resource identifier.",
        ),
        (
            {"title": "title1", "platform": "example", "platform_resource_identifier": None},
            HTTPStatus.FORBIDDEN,
            "No permission to set platform or platform resource identifier.",
        ),
    ],
)
def test_invalid_platform_identifier_combinations(
    client_test_resource: TestClient,
    body,
    expected_status,
    expected_detail,
):
    headers = {"Authorization": "Fake token"}

    with logged_in_user():
        response = client_test_resource.post("/test_resources", json=body, headers=headers)

    assert response.status_code == expected_status, response.json()  # noqa: S101
    assert response.json()["detail"] == expected_detail  # noqa: S101


@pytest.mark.versions(Version.LATEST)
@pytest.mark.parametrize(
    "router",
    tested_routers := [
        r
        for r in resource_routers.versioned_routers[Version.LATEST]
        if r.resource_name != "platform"
    ],
    ids=(r.resource_name for r in tested_routers),
)
def test_example_is_valid(router, client: TestClient, with_organisation_taxonomies):
    example_values = {}

    res_create = resource_create(router.resource_class)

    for attribute, model_field in res_create.__fields__.items():
        if "example" in model_field.field_info.extra:
            example_values[attribute] = model_field.field_info.extra["example"]

        elif "examples" in model_field.field_info.extra:
            examples = model_field.field_info.extra["examples"]

            if isinstance(examples, list):
                example_values[attribute] = examples[0]
            else:
                example_values[attribute] = examples

    with logged_in_user():
        response = client.post(
            f"/{router.resource_name_plural}",
            json=example_values,
            headers={"Authorization": "Fake token"},
        )

    assert response.status_code == HTTPStatus.OK, response.json()  # noqa: S101
