import os
import json

from unittest.mock import Mock
from starlette.testclient import TestClient
from tests.testutils.paths import path_test_resources
from routers.search_routers import SearchRouterPublications, router_list

def test_search_happy_path(client: TestClient):
    """Tests the Publications search"""
    
    # Get the correspondent router instance from the search routers list
    search_router = None
    for router_instance in router_list:
        if isinstance(router_instance, SearchRouterPublications):
            search_router = router_instance
    
    # Get the mocker results to test
    resources_path = os.path.join(path_test_resources(), "elasticsearch")
    mocked_file = os.path.join(resources_path, "publication_search.json")
    with open(mocked_file, "r") as f:
        mocked_results = json.load(f)
    
    # Mock and launch
    search_router.client.search = Mock(return_value=mocked_results)
    response = client.get("/search/publications/v1",
                          params={'search_query': "description"})
    
    # Assert the correct execution and get the response
    assert response.status_code == 200, response.json()
    resource = response.json()['resources'][0]
    
    # Test the response
    assert resource['identifier'] == 1
    assert resource['aiod_entry']['date_created'] == "2023-09-01T00:00:00+00:00"
    assert resource['aiod_entry']['date_modified'] == "2023-09-01T00:00:00+00:00"
    assert resource['aiod_entry']['status'] == "draft"
    assert resource['name'] == "A name"
    assert resource['description'] == "A description"
    assert resource['version'] == "1.0.0"
    assert resource['platform'] == "example"
    assert resource['platform_identifier'] == "1"
    assert resource['date_published'] == "2023-09-01T00:00:00+00:00"
    assert resource['issn'] == "00000000"
    assert resource['isbn'] == "0000000000000"
    assert resource['permanent_identifier'] == "https://test_resource.test"
    assert resource['license'] == "https://test_resource.test"
    assert resource['same_as'] == "https://test_resource.test"
