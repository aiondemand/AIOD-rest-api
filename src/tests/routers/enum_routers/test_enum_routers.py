import pytest
from starlette.testclient import TestClient
from versioning import Version


def test_taxonomy_router_news_categories(client: TestClient):
    response = client.get("/news_categories")
    assert response.status_code == 200, response.json()
    terms = {item["term"] for item in response.json()}
    assert terms.issuperset({"Education"})


@pytest.mark.versions(Version.V2)
def test_taxonomy_router_news_categories_v2(client: TestClient):
    response = client.get("/news_categorys")
    assert response.status_code == 200, response.json()
    terms = {item["term"] for item in response.json()}
    assert terms.issuperset({"Education"})


def test_enum_router_removed(client: TestClient):
    # keywords was a generic enum previously exposed
    response = client.get("/keywords")
    assert response.status_code == 404
