import copy
from unittest.mock import Mock

from starlette.testclient import TestClient


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_resource: dict,
    auto_publish: None,
):
    body = copy.deepcopy(body_resource)
    body["headline"] = "A headline to show on top of the page."
    body["alternative_headline"] = "An alternative headline."
    body["category"] = ["research: education", "research: awards", "business: health"]
    body["content"] = {"plain": "plain content"}
    body["source"] = "https://tailor-network.eu/shaping-the-future-of-ai-within-the-eu/"

    response = client.post("/news", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    identifier = response.json()['identifier']

    response = client.get(f"/news/{identifier}")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["headline"] == "A headline to show on top of the page."
    assert response_json["alternative_headline"] == "An alternative headline."
    assert (
        response_json["source"]
        == "https://tailor-network.eu/shaping-the-future-of-ai-within-the-eu/"
    )
    assert set(response_json["category"]) == {
        "research: education",
        "research: awards",
        "business: health",
    }
    assert response_json["content"] == {"plain": "plain content"}
