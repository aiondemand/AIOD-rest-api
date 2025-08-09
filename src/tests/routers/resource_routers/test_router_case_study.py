import copy

from starlette.testclient import TestClient

from tests.testutils.users import logged_in_user


def test_happy_path(
    client: TestClient,
    body_asset: dict,
    auto_publish: None,
):
    body = copy.copy(body_asset)
    body["name"] = "Case Study"

    with logged_in_user():
        response = client.post("/case_studies", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']
    response = client.get(f"/case_studies/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["name"] == "Case Study"
