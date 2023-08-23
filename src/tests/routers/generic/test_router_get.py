from sqlalchemy.future import Engine
from starlette.testclient import TestClient


def test_get_happy_path(client_test_resource: TestClient, engine_test_resource_filled: Engine):
    response = client_test_resource.get("/test_resources/v0/1")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json["title"] == "A title"
    assert response_json["identifier"] == 1
    assert "deprecated" not in response.headers


def test_not_found(client_test_resource: TestClient, engine_test_resource_filled: Engine):
    response = client_test_resource.get("/test_resources/v0/99")
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "Test_resource '99' not found in the database."
