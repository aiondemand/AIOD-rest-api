import pytest
from starlette.testclient import TestClient
from database.session import DbSession
from database.model.agent.organisation import Organisation
from database.model.agent.organisation_type import OrganisationType
from versioning import Version


def test_enum_router(client: TestClient, organisation: Organisation):
    organisation.type = OrganisationType(name="foo")
    with DbSession() as session:
        session.add(organisation)
        session.commit()

    response = client.get("/organisation_types")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert set(response_json).issuperset({"foo"})


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
