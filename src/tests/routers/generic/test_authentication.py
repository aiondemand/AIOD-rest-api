from unittest.mock import Mock

import pytest
from sqlalchemy.future import Engine
from starlette.testclient import TestClient



def test_get_all_unauthenticated(
    client_test_resource: TestClient, engine_test_resource_filled: Engine
):
    """You don't need authentication for GET"""
    response = client_test_resource.get("/test_resources")
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 1


def test_get_unauthenticated(client_test_resource: TestClient, auto_publish: None, engine_test_resource_filled: Engine):
    """You don't need authentication for GET"""
    response = client_test_resource.get(f"/test_resources/{engine_test_resource_filled}")
    assert response.status_code == 200, response.json()


def test_platform_get_all_unauthenticated(
    client_test_resource: TestClient, engine_test_resource_filled: Engine
):
    """You don't need authentication for GET"""
    response = client_test_resource.get("/platforms/example/test_resources")
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 1


def test_platform_get_unauthenticated(
    client_test_resource: TestClient, engine_test_resource_filled: Engine
):
    """You don't need authentication for GET"""
    response = client_test_resource.get("/platforms/example/test_resources")
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 1


@pytest.mark.parametrize(
    "mocked_token",
    [
        ["delete_test_resources"],
        ["delete_test_resources", "create_datasets"],
    ],
    indirect=True,
)
def test_delete_authorized(
    client_test_resource, mocked_token: Mock, engine_test_resource_filled: Engine
):
    response = client_test_resource.delete(
        f"/test_resources/{engine_test_resource_filled}",
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200, response.json()


def test_post_unauthenticated(client_test_resource: TestClient):
    response = client_test_resource.post("/test_resources", json={"title": "example"})
    assert response.status_code == 401, response.json()
    response_json = response.json()
    assert (
        response_json["detail"]
        == "No token found - This endpoint requires authorization. You need to be logged in."
    )


@pytest.mark.parametrize(
    "mocked_token",
    [
        ["update_test_resources"],
        ["update_test_resources", "delete_datasets"],
    ],
    indirect=True,
)
def test_put_authorized(
    client_test_resource, mocked_token: Mock, engine_test_resource_filled: Engine
):
    response = client_test_resource.put(
        f"/test_resources/{engine_test_resource_filled}",
        json={"title": "example"},
        headers={"Authorization": "fake-token"},
    )
    assert response.status_code == 200, response.json()


@pytest.mark.parametrize(
    "mocked_token", [["delete_test_resources"], ["update_datasets"]], indirect=True
)
def test_put_unauthorized(
    client_test_resource: TestClient, mocked_token: Mock, engine_test_resource_filled: Engine
):
    response = client_test_resource.put(
        f"/test_resources/{engine_test_resource_filled}",
        json={"title": "example"},
        headers={"Authorization": "fake-token"},
    )
    assert response.status_code == 403, response.json()
    response_json = response.json()
    assert response_json["detail"] == "You do not have permission to edit test_resources."


def test_put_unauthenticated(client_test_resource: TestClient):
    response = client_test_resource.put("/test_resources/1", json={"title": "example"})
    assert response.status_code == 401, response.json()
    response_json = response.json()
    assert (
        response_json["detail"]
        == "No token found - This endpoint requires authorization. You need to be logged in."
    )
