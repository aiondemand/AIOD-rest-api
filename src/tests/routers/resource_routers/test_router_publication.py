import copy
from unittest.mock import Mock

from starlette.testclient import TestClient

from database.model.dataset.dataset import Dataset


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_asset: dict,
    dataset: Dataset,
    auto_publish: None,
):
    body = copy.copy(body_asset)
    body["permanent_identifier"] = "http://dx.doi.org/10.1093/ajae/aaq063"
    body["isbn"] = "9783161484100"
    body["issn"] = "20493630"
    body["type"] = "journal"
    body["content"] = {"plain": "plain content"}

    response = client.post("/publications", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/publications/{identifier}")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json["permanent_identifier"] == "http://dx.doi.org/10.1093/ajae/aaq063"
    assert response_json["isbn"] == "9783161484100"
    assert response_json["issn"] == "20493630"
    assert response_json["type"] == "journal"
    assert response_json["content"] == {"plain": "plain content"}


def test_pid_field(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_asset: dict,
    dataset: Dataset,
    auto_publish: None,
):
    """Test that the new pid field works correctly."""
    body = copy.copy(body_asset)
    body["pid"] = "https://doi.org/10.1093/ajae/aaq063"
    body["type"] = "journal"

    response = client.post("/publications", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/publications/{identifier}")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    assert response_json["pid"] == "https://doi.org/10.1093/ajae/aaq063"


def test_pid_and_permanent_identifier_coexist(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_asset: dict,
    dataset: Dataset,
    auto_publish: None,
):
    """Test that both pid and permanent_identifier can be set independently."""
    body = copy.copy(body_asset)
    body["pid"] = "https://doi.org/10.1093/ajae/aaq063"
    body["permanent_identifier"] = "http://dx.doi.org/10.1093/ajae/aaq064"
    body["type"] = "journal"

    response = client.post("/publications", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/publications/{identifier}")
    assert response.status_code == 200, response.json()
    response_json = response.json()

    # Both fields should be preserved independently
    assert response_json["pid"] == "https://doi.org/10.1093/ajae/aaq063"
    assert response_json["permanent_identifier"] == "http://dx.doi.org/10.1093/ajae/aaq064"
