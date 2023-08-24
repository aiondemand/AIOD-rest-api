from unittest.mock import Mock

from sqlalchemy.future import Engine
from starlette.testclient import TestClient

from authentication import keycloak_openid


def test_get_all_unauthenticated(
    client_test_resource: TestClient, engine_test_resource_filled: Engine
):
    """You don't need authentication for GET"""
    response = client_test_resource.get("/test_resources/v0")
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 1


def test_get_unauthenticated(client_test_resource: TestClient, engine_test_resource_filled: Engine):
    """You don't need authentication for GET"""
    response = client_test_resource.get("/test_resources/v0/1")
    assert response.status_code == 200, response.json()


def test_platform_get_all_unauthenticated(
    client_test_resource: TestClient, engine_test_resource_filled: Engine
):
    """You don't need authentication for GET"""
    response = client_test_resource.get("/platforms/example/test_resources/v0")
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 1


def test_platform_get_unauthenticated(
    client_test_resource: TestClient, engine_test_resource_filled: Engine
):
    """You don't need authentication for GET"""
    response = client_test_resource.get("/platforms/example/test_resources/v0")
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 1


def test_delete_unauthenticated(
    client_test_resource: TestClient, engine_test_resource_filled: Engine
):
    response = client_test_resource.delete("/test_resources/v0/1")
    assert response.status_code == 401, response.json()


def test_delete_unauthorized(client_test_resource: TestClient, mocked_token: Mock):
    keycloak_openid.userinfo = mocked_token
    response = client_test_resource.delete(
        "/test_resources/v0/1",
        headers={"Authorization": "fake-token"},
    )
    assert response.status_code == 403, response.json()
    response_json = response.json()
    assert response_json["detail"] == "You do not have permission to edit Aiod resources."


def test_post_unauthorized(client_test_resource: TestClient, mocked_token: Mock):
    keycloak_openid.userinfo = mocked_token
    response = client_test_resource.post(
        "/test_resources/v0",
        json={"title": "example"},
        headers={"Authorization": "fake-token"},
    )
    assert response.status_code == 403, response.json()
    response_json = response.json()
    assert response_json["detail"] == "You do not have permission to edit Aiod resources."


def test_post_unauthenticated(client_test_resource: TestClient):
    response = client_test_resource.post("/test_resources/v0", json={"title": "example"})
    assert response.status_code == 401, response.json()
    response_json = response.json()
    assert (
        response_json["detail"] == "This endpoint requires authorization. You need to be logged in."
    )


def test_put_unauthorized(client_test_resource: TestClient, mocked_token: Mock):
    keycloak_openid.userinfo = mocked_token
    response = client_test_resource.put(
        "/test_resources/v0/1",
        json={"title": "example"},
        headers={"Authorization": "fake-token"},
    )
    assert response.status_code == 403, response.json()
    response_json = response.json()
    assert response_json["detail"] == "You do not have permission to edit Aiod resources."


def test_put_unauthenticated(client_test_resource: TestClient):
    response = client_test_resource.put("/test_resources/v0/1", json={"title": "example"})
    assert response.status_code == 401, response.json()
    response_json = response.json()
    assert (
        response_json["detail"] == "This endpoint requires authorization. You need to be logged in."
    )
