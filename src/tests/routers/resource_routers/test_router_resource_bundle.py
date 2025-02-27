import copy
from unittest.mock import Mock

from starlette.testclient import TestClient
from database.model.resource_bundle.resource_bundle import ResourceBundle
from database.model.ai_resource.resource_table import AIResourceORM
from database.session import DbSession


def test_resource_bundle_api(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_asset: dict,
):
    """
    Test creating and retrieving a ResourceBundle through the API.
    """
    resource_1 = AIResourceORM(name="AI Resource 1")
    resource_2 = AIResourceORM(name="AI Resource 2")


    with DbSession() as session:
        session.add(resource_1)
        session.add(resource_2)
        session.commit()
        session.refresh(resource_1)
        session.refresh(resource_2)

    # Prepare request body
    body = copy.copy(body_asset)
    body["name"] = "My AI Bundle"
    body["includes_resources"] = [resource_1.identifier, resource_2.identifier]
    body["includes_external_resource"] = ["https://example.com/resource"]


    response = client.post("/resource_bundles/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/resource_bundles/v1/1")
    assert response.status_code == 200, response.json()


    response_json = response.json()
    assert response_json["name"] == "My AI Bundle"
    assert response_json["includes_resources"] == [resource_1.identifier, resource_2.identifier]
    assert response_json["includes_external_resource"] == ["https://example.com/resource"]
