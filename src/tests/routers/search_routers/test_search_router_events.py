import os
import json

from unittest.mock import Mock
from starlette.testclient import TestClient
from tests.testutils.paths import path_test_resources
from routers.search_routers import SearchRouterEvents, router_list

def test_search_happy_path(client: TestClient):
    """Tests the Events search"""
    
    # Get the correspondent router instance from the search routers list
    search_router = None
    for router_instance in router_list:
        if isinstance(router_instance, SearchRouterEvents):
            search_router = router_instance
    
    # Get the mocker results to test
    resources_path = os.path.join(path_test_resources(), "elasticsearch")
    mocked_file = os.path.join(resources_path, "event_search.json")
    with open(mocked_file, "r") as f:
        mocked_results = json.load(f)
    
    # Mock and launch
    search_router.client.search = Mock(return_value=mocked_results)
    response = client.get("/search/events/v1",
                          params={'search_query': "description"})
    
    # Assert the correct execution and get the response
    assert response.status_code == 200, response.json()
    resource = response.json()['resources'][0]
    
    # Test the response
    assert resource['end_date'] == "2023-09-01T00:00:00+00:00"
    assert resource['mode'] == "offline"
    assert resource['description'] == "A description."
    assert resource['platform_identifier'] == "1"
    assert resource['application_area'] == ["Fraud Prevention", "Voice Assistance", "Disease Classification"]
    assert resource['registration_link'] == "https://example.com/registration-form"
    assert resource['name'] == "The name of the Event"
    assert resource['schedule'] == "10:00-10:30: Opening. 10:30-11:00 ..."
    assert resource['platform'] == "example"
    assert resource['start_date'] == "2023-09-01T00:00:00+00:00"
    assert resource['same_as'] == "https://www.example.com/resource/this_resource"
    assert resource['identifier'] == 1
    assert resource['aiod_entry']['date_modified'] == "2023-09-01T00:00:00+00:00"
    assert resource['aiod_entry']['date_created'] == "2023-09-01T00:00:00+00:00"
    assert resource['aiod_entry']['status'] == "draft"
