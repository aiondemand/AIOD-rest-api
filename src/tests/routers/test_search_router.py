import json
from unittest.mock import Mock

from sqlalchemy.engine import Engine
from starlette.testclient import TestClient

from authentication import keycloak_openid
from routers import SearchRouter, other_routers
from tests.testutils.paths import path_test_resources


def test_search_publication_happy_path(
    client: TestClient,
    engine: Engine,
    mocked_privileged_token: Mock,
    body_resource: dict,
):
    keycloak_openid.userinfo = mocked_privileged_token

    (search_router,) = [r for r in other_routers if isinstance(r, SearchRouter)]
    with open(path_test_resources() / "elasticsearch" / "publication_search.json", "r") as f:
        mocked_results = json.load(f)
    search_router.client = Mock()
    search_router.client.search = Mock(return_value=mocked_results)

    response = client.get(
        "/search/publications/v1",
        params={"name": "publication"},
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == 200, response.json()
    response_json = response.json()
    (publication,) = response_json["resources"]
    assert publication["platform_identifier"] == "1"
    assert (
        publication["license"] == "https://creativecommons.org/share-your-work/public-domain/cc0/"
    )
    assert publication["knowledge_asset_identifier"] == 1
    assert publication["asset_identifier"] == 1
    assert publication["resource_identifier"] == 1
    assert publication["permanent_identifier"] == "http://dx.doi.org/10.1093/ajae/aaq063"
    assert publication["description"] == "A description."
    assert publication["isbn"] == "9783161484100"
    assert publication["aiod_entry"]["date_modified"] == "2023-08-24T10:14:52+00:00"
    assert publication["aiod_entry"]["date_created"] == "2023-08-24T10:14:52+00:00"
    assert publication["aiod_entry"]["status"] == "draft"
    assert publication["version"] == "1.1.0"
    assert publication["name"] == "The name of this publication"
    assert publication["platform"] == "example"
    assert publication["type"] == "journal"
    assert publication["same_as"] == "https://www.example.com/resource/this_resource"
    assert publication["identifier"] == 1
    assert publication["issn"] == "20493630"
    assert publication["date_published"] == "2022-01-01T15:15:00+00:00"
