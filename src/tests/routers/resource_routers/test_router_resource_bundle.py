import copy
from unittest.mock import Mock

from starlette.testclient import TestClient
from database.model.ai_resource.resource_table import AIResourceORM
from database.session import DbSession
from tests.testutils.users import register_asset, ALICE


def test_resource_bundle_api(
    client: TestClient,
    mocked_privileged_token: Mock,
    publication_factory,
    body_asset: dict,
    auto_publish: None,
):
    """
    Test creating and retrieving a ResourceBundle through the API.
    """
    resource_1 = register_asset(publication_factory(), owner=ALICE)
    resource_2 = register_asset(publication_factory(), owner=ALICE)

    # Prepare request body
    body = copy.copy(body_asset)
    body["name"] = "My AI Bundle"
    body["includes_resource"] = [resource_1, resource_2]
    body["includes_external_reference"] = ["https://example.com/resource"]


    response = client.post("/resource_bundles", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/resource_bundles/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["name"] == "My AI Bundle"
    assert set(response_json["includes_resource"]) == {resource_1, resource_2}
    assert response_json["includes_external_reference"] == ["https://example.com/resource"]
