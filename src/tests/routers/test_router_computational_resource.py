"""
Dataset is a complex resource, so they are tested separately.
"""

from unittest.mock import Mock

from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from authentication import keycloak_openid


def test_happy_path(client: TestClient, engine: Engine, mocked_privileged_token: Mock):
    keycloak_openid.decode_token = mocked_privileged_token

    body = {
        "platform": "example",
        "platform_identifier": "1",
        "description": "A description.",
        "name": "Example Computational resource",
        "keyword": ["keyword1", "keyword2"],
        "citation": ["citation1", "citation2"],
        "logo": "https://www.example.com/computational_resource/logo.png",
        "creationTime": "2023-01-01T15:15:00.000Z",
        "validity": 5,
        "other_info": ["info1", "info2"],
        "capability": ["capability 1", "capability 2"],
        "complexity": "complexity example",
        "location": "Example location",
        "alternate_name": ["name1", "name2"],
        "distribution": [],
    }
    response = client.post(
        "/computational_resources/v0", json=body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200

    response = client.get("/computational_resources/v0/1")
    assert response.status_code == 200

    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["platform"] == "example"
    assert response_json["platform_identifier"] == "1"
    assert response_json["description"] == "A description."
    assert response_json["name"] == "Example Computational resource"
    assert set(response_json["keyword"]) == {"keyword1", "keyword2"}
    assert set(response_json["citation"]) == {"citation1", "citation2"}
    assert response_json["logo"] == "https://www.example.com/computational_resource/logo.png"
    assert response_json["creationTime"] == "2023-01-01T15:15:00"
    assert response_json["validity"] == 5
    assert set(response_json["other_info"]) == {"info1", "info2"}
    assert set(response_json["capability"]) == {"capability 1", "capability 2"}
    assert response_json["complexity"] == "complexity example"
    assert response_json["location"] == "Example location"
    assert set(response_json["alternate_name"]) == {"name1", "name2"}
