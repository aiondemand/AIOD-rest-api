import pytest
from sqlalchemy.future import Engine
from starlette.testclient import TestClient


@pytest.mark.skip(reason="Platforms currently don't work")
def test_get_happy_path(client_test_resource: TestClient, engine_test_resource_filled: Engine):
    response = client_test_resource.get("/platforms/example/test_resources/v0/1")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json["title"] == "A title"
    assert response_json["identifier"] == 1
    assert "deprecated" not in response.headers


@pytest.mark.skip(reason="Platforms currently don't work")
def test_not_found(client_test_resource: TestClient, engine_test_resource_filled: Engine):
    response = client_test_resource.get("/platforms/example/test_resources/v0/99")
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "Test_resource '99' not found in the database."


@pytest.mark.skip(reason="Platforms currently don't work")
def test_wrong_platform(client_test_resource: TestClient, engine_test_resource_filled: Engine):
    response = client_test_resource.get("/platforms/openml/test_resources/v0/1")
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == "Test_resource '1' of 'openml' not found in the database."


@pytest.mark.skip(reason="Platforms currently don't work")
def test_nonexistent_platform(
    client_test_resource: TestClient, engine_test_resource_filled: Engine
):
    response = client_test_resource.get("/platforms/nonexistent_platform/test_resources/v0/1")
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "platform 'nonexistent_platform' not recognized."
