import pytest
from sqlalchemy.engine import Engine
from starlette.testclient import TestClient


@pytest.mark.parametrize(
    "title",
    ["\"'é:?", "!@#$%^&*()`~", "Ω≈ç√∫˜µ≤≥÷", "田中さんにあげて下さい", " أي بعد, ", "𝑻𝒉𝒆 𝐪𝐮𝐢𝐜𝐤", "گچپژ"],
)
def test_unicode(client_test_resource: TestClient, engine_test_resource_filled: Engine, title: str):
    response = client_test_resource.put(
        "/test_resources/v0/1",
        json={"title": title, "platform": "other", "platform_identifier": "2"},
    )
    assert response.status_code == 200
    response = client_test_resource.get("/test_resources/v0/1")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["title"] == title
    assert response_json["platform"] == "other"
    assert response_json["platform_identifier"] == "2"


def test_non_existent(client_test_resource: TestClient, engine_test_resource_filled: Engine):
    response = client_test_resource.put(
        "/test_resources/v0/2",
        json={"title": "new_title", "platform": "other", "platform_identifier": "2"},
    )
    assert response.status_code == 404
    response_json = response.json()
    assert response_json["detail"] == "Test_resource '2' not found in the database."


def test_too_long_name(client_test_resource: TestClient, engine_test_resource_filled: Engine):
    name = "a" * 251
    response = client_test_resource.put("/test_resources/v0/1", json={"title": name})
    assert response.status_code == 422
    response_json = response.json()
    assert response_json["detail"] == [
        {
            "ctx": {"limit_value": 250},
            "loc": ["body", "title"],
            "msg": "ensure this value has at most 250 characters",
            "type": "value_error.any_str.max_length",
        }
    ]
