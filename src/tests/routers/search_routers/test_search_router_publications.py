import json
from unittest.mock import Mock

from starlette.testclient import TestClient

from authentication import keycloak_openid
from routers import other_routers, SearchRouterPublications
from tests.testutils.paths import path_test_resources


def test_search_happy_path(client: TestClient, mocked_privileged_token: Mock):
    keycloak_openid.userinfo = mocked_privileged_token

    (search_router,) = [r for r in other_routers if isinstance(r, SearchRouterPublications)]
    with open(path_test_resources() / "elasticsearch" / "publication_search.json", "r") as f:
        mocked_results = json.load(f)
    search_router.client.search = Mock(return_value=mocked_results)

    response = client.get(
        "/search/publications/v1",
        params={"name": "resource"},
        headers={"Authorization": "Fake token"},
    )

    assert response.status_code == 200, response.json()
    response_json = response.json()
    (resource,) = response_json["resources"]
    # assert resource["platform_identifier"] == "1"
    # assert resource["license"] == "https://creativecommons.org/share-your-work/public-domain/cc0/"
    # assert resource["knowledge_asset_identifier"] == 1
    # assert resource["asset_identifier"] == 1
    # assert resource["resource_identifier"] == 1
    # assert resource["permanent_identifier"] == "http://dx.doi.org/10.1093/ajae/aaq063"
    # assert resource["description"] == "A description."
    # assert resource["isbn"] == "9783161484100"
    # assert resource["aiod_entry"]["date_modified"] == "2023-08-24T10:14:52+00:00"
    # assert resource["aiod_entry"]["date_created"] == "2023-08-24T10:14:52+00:00"
    # assert resource["aiod_entry"]["status"] == "draft"
    # assert resource["version"] == "1.1.0"
    # assert resource["name"] == "The name of this publication"
    # assert resource["platform"] == "example"
    # assert resource["type"] == "journal"
    # assert resource["same_as"] == "https://www.example.com/resource/this_resource"
    # assert resource["identifier"] == 1
    # assert resource["issn"] == "20493630"
    # assert resource["date_published"] == "2022-01-01T15:15:00+00:00"
