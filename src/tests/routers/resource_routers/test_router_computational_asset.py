import copy

from starlette.testclient import TestClient

from tests.testutils.users import logged_in_user


def test_happy_path(client: TestClient, body_asset: dict, auto_publish: None):
    body = copy.deepcopy(body_asset)
    body["status_info"] = "https://www.example.com/cluster-status"
    body["type"] = "storage"

    with logged_in_user():
        response = client.post(
            "/computational_assets", json=body, headers={"Authorization": "Fake token"}
        )
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/computational_assets/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["status_info"] == "https://www.example.com/cluster-status"
    assert response_json["type"] == "storage"
