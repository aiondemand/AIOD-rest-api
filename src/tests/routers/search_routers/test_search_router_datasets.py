import json
from unittest.mock import Mock

from starlette.testclient import TestClient

from authentication import keycloak_openid
from routers import other_routers, SearchRouterDatasets
from tests.testutils.paths import path_test_resources


def test_search_happy_path(client: TestClient, mocked_privileged_token: Mock):
    keycloak_openid.userinfo = mocked_privileged_token

    (search_router,) = [r for r in other_routers if isinstance(r, SearchRouterDatasets)]
    with open(path_test_resources() / "elasticsearch" / "dataset_search.json", "r") as f:
        mocked_results = json.load(f)
    search_router.client.search = Mock(return_value=mocked_results)

    response = client.get(
        "/search/datasets/v1",
        params={"name": "dataset"},
        headers={"Authorization": "Fake token"},
    )

    assert response.status_code == 200, response.json()
    response_json = response.json()
    (resource,) = response_json["resources"]

    # assert resource["platform_identifier"] == "1"
    # assert resource["license"] == "https://creativecommons.org/share-your-work/public-domain/cc0/"

    # assert resource["asset_identifier"] == 3
    # assert resource["resource_identifier"] == 3
    # assert resource["description"] == "A description."
    # assert resource["aiod_entry"]["date_modified"] == "2023-08-24T12:48:49+00:00"
    # assert resource["aiod_entry"]["date_created"] == "2023-08-24T12:48:49+00:00"
    # assert resource["aiod_entry"]["status"] == "draft"
    # assert resource["version"] == "1.1.0"
    # assert resource["name"] == "The name of this dataset"
    # assert resource["platform"] == "example"
    # assert resource["same_as"] == "https://www.example.com/resource/this_resource"
    # assert resource["identifier"] == 1
    # assert resource["date_published"] == "2022-01-01T15:15:00+00:00"
    # assert resource["issn"] == "20493630"
    # assert resource["measurement_technique"] == "mass spectrometry"
    # assert resource["temporal_coverage"] == "2011/2012"
