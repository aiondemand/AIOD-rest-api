import pytest
from starlette.testclient import TestClient
from versioning import Version


def test_taxonomy_router(client: TestClient):
    response = client.get("/news_categories")
    assert response.status_code == 200, response.json()
    terms = {item["term"] for item in response.json()}
    assert terms.issuperset({"Education"})


@pytest.mark.versions(Version.V2)
def test_taxonomy_router_v2(client: TestClient):
    response = client.get("/news_categorys")
    assert response.status_code == 200, response.json()
    terms = {item["term"] for item in response.json()}
    assert terms.issuperset({"Education"})
