import os
import json

from unittest.mock import Mock
from starlette.testclient import TestClient
from tests.testutils.paths import path_test_resources
from routers.search_routers import SearchRouterServices, router_list

def test_search_happy_path(client: TestClient):
    """Tests the Services search"""
    
    # Get the correspondent router instance from the search routers list
    search_router = None
    for router_instance in router_list:
        if isinstance(router_instance, SearchRouterServices):
            search_router = router_instance
    
    # Get the mocker results to test
    resources_path = os.path.join(path_test_resources(), "elasticsearch")
    mocked_file = os.path.join(resources_path, "service_search.json")
    with open(mocked_file, "r") as f:
        mocked_results = json.load(f)
    
    # Mock and launch
    search_router.client.search = Mock(return_value=mocked_results)
    response = client.get("/search/services/v1",
                          params={'search_query': "description"})
    
    # Assert the correct execution and get the response
    assert response.status_code == 200, response.json()
    resource = response.json()['resources'][0]
    
    # Test the response
    assert resource['same_as'] == "https://www.example.com/resource/this_resource"
    assert resource['identifier'] == 1
    assert resource['description'] == "A description."
    assert resource['platform_identifier'] == "1"
    assert resource['aiod_entry']['date_modified'] == "2023-09-01T00:00:00+00:00"
    assert resource['slogan'] == "Making your Smart Paradigm Shifts more Disruptive"
    assert resource['application_area'] == ["Fraud Prevention", "Voice Assistance", "Disease Classification"]
    assert resource['name'] == "The name of this service"
    assert resource['aiod_entry']['date_created'] == "2023-09-01T00:00:00+00:00"
    assert resource['platform'] == "example"
    assert resource['aiod_entry']['status'] == "draft"
    assert resource['terms_of_service'] == "Your use of this service is subject to the following terms: [...]."
