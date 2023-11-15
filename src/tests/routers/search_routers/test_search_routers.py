import os
import json

from unittest.mock import Mock
from starlette.testclient import TestClient
from tests.testutils.paths import path_test_resources
import routers.search_routers as sr

def test_search_happy_path(client: TestClient):
    """Tests the search router"""
    
    for search_router in sr.router_list:
        
        # Get the mocker results to test
        resources_path = os.path.join(path_test_resources(), "elasticsearch")
        resource_file = f"{search_router.es_index}_search.json"
        mocked_file = os.path.join(resources_path, resource_file)
        with open(mocked_file, "r") as f:
            mocked_results = json.load(f)
        
        # Mock and launch
        search_router.client.search = Mock(return_value=mocked_results)
        search_service = f"/search/{search_router.resource_name_plural}/v1"
        params = {'search_query': "description", 'get_all': False}
        response = client.get(search_service, params=params)
        
        # Assert the correct execution and get the response
        assert response.status_code == 200, response.json()
        resource = response.json()['resources'][0]
        
        # Test the common responses
        assert resource['identifier'] == 1
        assert resource['name'] == "A name."
        assert resource['description']['plain'] == "A plain text description."
        assert resource['description']['html'] == "An html description."
        assert resource['aiod_entry']['date_modified'] == "2023-09-01T00:00:00+00:00"
        
        # Test the extra fields
        global_fields = set(['name', 'plain', 'html'])
        extra_fields = list(search_router.match_fields^global_fields)
        for field in extra_fields:
            assert resource[field]

def test_search_bad_platform(client: TestClient):
    """Tests the search router bad platform error"""
    
    for search_router in sr.router_list:
        
        # Get the mocker results to test
        resources_path = os.path.join(path_test_resources(), "elasticsearch")
        resource_file = f"{search_router.es_index}_search.json"
        mocked_file = os.path.join(resources_path, resource_file)
        with open(mocked_file, "r") as f:
            mocked_results = json.load(f)
        
        # Mock and launch
        search_router.client.search = Mock(return_value=mocked_results)
        search_service = f"/search/{search_router.resource_name_plural}/v1"
        params = {'search_query': "description", 'platforms': ["bad_platform"]}
        response = client.get(search_service, params=params)
        
        # Assert the platform error
        assert response.status_code == 400, response.json()
        err_msg = "The available platformas are"
        assert response.json()["detail"][:len(err_msg)] == err_msg

def test_search_bad_fields(client: TestClient):
    """Tests the search router bad fields error"""
    
    for search_router in sr.router_list:
        
        # Get the mocker results to test
        resources_path = os.path.join(path_test_resources(), "elasticsearch")
        resource_file = f"{search_router.es_index}_search.json"
        mocked_file = os.path.join(resources_path, resource_file)
        with open(mocked_file, "r") as f:
            mocked_results = json.load(f)
        
        # Mock and launch
        search_router.client.search = Mock(return_value=mocked_results)
        search_service = f"/search/{search_router.resource_name_plural}/v1"
        params = {'search_query': "description", 'search_fields': ["bad_field"]}
        response = client.get(search_service, params=params)
        
        # Assert the platform error
        assert response.status_code == 400, response.json()
        err_msg = "The available search fields for this entity are"
        assert response.json()["detail"][:len(err_msg)] == err_msg

def test_search_bad_limit(client: TestClient):
    """Tests the search router bad fields error"""
    
    for search_router in sr.router_list:
        
        # Get the mocker results to test
        resources_path = os.path.join(path_test_resources(), "elasticsearch")
        resource_file = f"{search_router.es_index}_search.json"
        mocked_file = os.path.join(resources_path, resource_file)
        with open(mocked_file, "r") as f:
            mocked_results = json.load(f)
        
        # Mock and launch
        search_router.client.search = Mock(return_value=mocked_results)
        search_service = f"/search/{search_router.resource_name_plural}/v1"
        params = {'search_query': "description", 'limit': 1001}
        response = client.get(search_service, params=params)
        
        # Assert the platform error
        assert response.status_code == 400, response.json()
        err_msg = "The limit should be maximum 1000."
        assert response.json()["detail"][:len(err_msg)] == err_msg

def test_search_bad_page(client: TestClient):
    """Tests the search router bad fields error"""
    
    for search_router in sr.router_list:
        
        # Get the mocker results to test
        resources_path = os.path.join(path_test_resources(), "elasticsearch")
        resource_file = f"{search_router.es_index}_search.json"
        mocked_file = os.path.join(resources_path, resource_file)
        with open(mocked_file, "r") as f:
            mocked_results = json.load(f)
        
        # Mock and launch
        search_router.client.search = Mock(return_value=mocked_results)
        search_service = f"/search/{search_router.resource_name_plural}/v1"
        params = {'search_query': "description", 'page': 0}
        response = client.get(search_service, params=params)
        
        # Assert the platform error
        assert response.status_code == 400, response.json()
        err_msg = "The page numbers start by 1."
        assert response.json()["detail"][:len(err_msg)] == err_msg
