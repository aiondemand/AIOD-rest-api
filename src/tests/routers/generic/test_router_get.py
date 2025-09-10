from http import HTTPStatus

from sqlalchemy.future import Engine
from starlette.testclient import TestClient

from database.model.concept.aiod_entry import EntryStatus
from tests.testutils.users import register_asset, ALICE, logged_in_user
from tests.testutils.test_resource import factory_test_resource


def test_get_happy_path(client_test_resource: TestClient, engine_test_resource_filled: str):
    response = client_test_resource.get(f"/test_resources/{engine_test_resource_filled}")
    assert response.status_code == HTTPStatus.OK, response.json()
    response_json = response.json()

    assert response_json["title"] == "A title"
    assert response_json["identifier"].startswith("test")
    assert "deprecated" not in response.headers


def test_not_found(client_test_resource: TestClient, engine_test_resource_filled: str):
    response = client_test_resource.get("/test_resources/test_99")
    assert response.status_code == HTTPStatus.NOT_FOUND, response.json()
    assert response.json()["detail"] == "Test_resource 'test_99' not found in the database."


def test_not_valid(client_test_resource: TestClient, engine_test_resource_filled: str):
    response = client_test_resource.get("/test_resources/99")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.json()
    assert "is not a valid" in response.json()["detail"]


def test_get_draft_unauthenticated_not_allowed(client_test_resource: TestClient):
    identifier = register_asset(factory_test_resource(), owner=ALICE, status=EntryStatus.DRAFT)
    response = client_test_resource.get(f"/test_resources/{identifier}")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_draft_no_permission_not_allowed(client_test_resource: TestClient):
    identifier = register_asset(factory_test_resource(), owner=ALICE, status=EntryStatus.DRAFT)
    with logged_in_user():
        response = client_test_resource.get(f"/test_resources/{identifier}", headers={"Authorization": "fake-token"})
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_get_draft_with_permission_is_allowed(client_test_resource: TestClient):
    identifier = register_asset(factory_test_resource(), owner=ALICE, status=EntryStatus.DRAFT)
    with logged_in_user(ALICE):
        response = client_test_resource.get(f"/test_resources/{identifier}", headers={"Authorization": "fake-token"})
    assert response.status_code == HTTPStatus.OK
