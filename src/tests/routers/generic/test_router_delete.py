from functools import partial
from http import HTTPStatus
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

from authentication import KeycloakUser
from database.session import DbSession
from database.model.concept.aiod_entry import EntryStatus
from tests.testutils.test_resource import factory_test_resource
from tests.testutils.users import register_asset, ALICE, logged_in_user, BOB


@pytest.mark.parametrize("index", [0, 1])
def test_happy_path(
    client_test_resource: TestClient,
    index: int,
):
    resources = [
        factory_test_resource(title="my_test_resource", status=EntryStatus.DRAFT,
                              platform="example", platform_resource_identifier=1),
        factory_test_resource(title="second_test_resource", status=EntryStatus.DRAFT,
                              platform="example", platform_resource_identifier=2),
    ]

    for resource in resources:
        register_asset(resource, owner=ALICE, status=EntryStatus.PUBLISHED)

    identifiers = [test.identifier for test in resources]
    identifier = identifiers[index]

    with logged_in_user(ALICE):
        response = client_test_resource.delete(
            f"/test_resources/{identifier}", headers={"Authorization": "Fake token"}
        )
    assert response.status_code == 200, response.json()
    response = client_test_resource.get("/test_resources/")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert len(response_json) == 1
    assert {r["identifier"] for r in response_json} == set(identifiers) - {identifier}


@pytest.mark.parametrize(
    ("owner", "other"),
    [(ALICE, BOB), (BOB, ALICE)]
)
def test_delete_requires_admin(
        owner: KeycloakUser,
        other: KeycloakUser,
        client_test_resource: TestClient,
):
    identifier = register_asset(factory_test_resource(), owner=owner, status=EntryStatus.DRAFT)
    try_delete = partial(
        client_test_resource.delete,
            f"/test_resources/{identifier}",
        headers={"Authorization": "Fake token"}
    )
    assert try_delete().status_code == HTTPStatus.UNAUTHORIZED
    with logged_in_user(other):
        assert try_delete().status_code == HTTPStatus.FORBIDDEN
    with logged_in_user(owner):
        assert try_delete().status_code == HTTPStatus.OK


def test_non_existent(
    client_test_resource: TestClient,
    mocked_privileged_token: Mock,
):
    response = client_test_resource.delete(
        f"/test_resources/test_44", headers={"Authorization": "Fake token"}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND, response.json()
    assert response.json()["detail"] == f"Test_resource 'test_44' not found in the database."


def test_not_valid(
        client_test_resource: TestClient,
        mocked_privileged_token: Mock,
):
    response = client_test_resource.delete(
        f"/test_resources/data_44", headers={"Authorization": "Fake token"}
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.json()
    assert "is not a valid" in response.json()["detail"]


def test_add_after_deletion(
    client_test_resource: TestClient,
    mocked_privileged_token: Mock,
):
    body = {"title": "my_favourite_resource"}
    response = client_test_resource.post(
        "/test_resources", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200, response.json()
    id_ = response.json()["identifier"]
    response = client_test_resource.delete(
        f"/test_resources/{id_}", headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200, response.json()
    response = client_test_resource.post(
        "/test_resources", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200, response.json()
