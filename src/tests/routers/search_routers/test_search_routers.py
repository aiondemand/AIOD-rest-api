import os
import json
import pytest

from unittest.mock import Mock

from elasticsearch import Elasticsearch
from starlette.testclient import TestClient

from routers.search_routers.elasticsearch import ElasticsearchSingleton
from tests.testutils.paths import path_test_resources
import routers.search_routers as sr


@pytest.mark.parametrize("search_router", sr.router_list)
def test_search_happy_path(client: TestClient, search_router):
    """Tests the search router"""
    mocked_elasticsearch = Elasticsearch("https://example.com:9200")
    ElasticsearchSingleton().patch(mocked_elasticsearch)

    resources_path = os.path.join(path_test_resources(), "elasticsearch")
    resource_file = f"{search_router.es_index}_search.json"
    mocked_file = os.path.join(resources_path, resource_file)
    with open(mocked_file, "r") as f:
        mocked_results = json.load(f)

    mocked_elasticsearch.search = Mock(return_value=mocked_results)
    search_service = f"/search/{search_router.resource_name_plural}/v1"
    params = {"search_query": "description", "get_all": False}
    response = client.get(search_service, params=params)

    assert response.status_code == 200, response.json()
    resource = response.json()["resources"][0]

    assert resource["identifier"] == 1
    assert resource["name"] == "A name."
    assert resource["description"]["plain"] == "A plain text description."
    assert resource["description"]["html"] == "An html description."
    assert resource["aiod_entry"]["date_modified"] == "2023-09-01T00:00:00+00:00"
    assert resource["aiod_entry"]["status"] is None

    global_fields = {"name", "description_plain", "description_html"}
    extra_fields = list(search_router.indexed_fields ^ global_fields)
    for field in extra_fields:
        assert resource[field]


@pytest.mark.parametrize("search_router", sr.router_list)
def test_search_bad_platform(client: TestClient, search_router):
    """Tests the search router bad platform error"""
    mocked_elasticsearch = Elasticsearch("https://example.com:9200")
    ElasticsearchSingleton().patch(mocked_elasticsearch)

    resources_path = os.path.join(path_test_resources(), "elasticsearch")
    resource_file = f"{search_router.es_index}_search.json"
    mocked_file = os.path.join(resources_path, resource_file)
    with open(mocked_file, "r") as f:
        mocked_results = json.load(f)

    mocked_elasticsearch.search = Mock(return_value=mocked_results)
    search_service = f"/search/{search_router.resource_name_plural}/v1"
    params = {"search_query": "description", "platforms": ["bad_platform"]}
    response = client.get(search_service, params=params)

    assert response.status_code == 400, response.json()
    err_msg = "The available platforms are"
    assert response.json()["detail"][: len(err_msg)] == err_msg


@pytest.mark.parametrize("search_router", sr.router_list)
def test_search_bad_fields(client: TestClient, search_router):
    """Tests the search router bad fields error"""
    mocked_elasticsearch = Elasticsearch("https://example.com:9200")
    ElasticsearchSingleton().patch(mocked_elasticsearch)

    resources_path = os.path.join(path_test_resources(), "elasticsearch")
    resource_file = f"{search_router.es_index}_search.json"
    mocked_file = os.path.join(resources_path, resource_file)
    with open(mocked_file, "r") as f:
        mocked_results = json.load(f)

    mocked_elasticsearch.search = Mock(return_value=mocked_results)
    search_service = f"/search/{search_router.resource_name_plural}/v1"
    params = {"search_query": "description", "search_fields": ["bad_field"]}
    response = client.get(search_service, params=params)

    assert response.status_code == 422, response.json()

    assert response.json()["detail"][0]["msg"].startswith("unexpected value; permitted: ")


@pytest.mark.parametrize("search_router", sr.router_list)
def test_search_bad_limit(client: TestClient, search_router):
    """Tests the search router bad fields error"""
    mocked_elasticsearch = Elasticsearch("https://example.com:9200")
    ElasticsearchSingleton().patch(mocked_elasticsearch)

    resources_path = os.path.join(path_test_resources(), "elasticsearch")
    resource_file = f"{search_router.es_index}_search.json"
    mocked_file = os.path.join(resources_path, resource_file)
    with open(mocked_file, "r") as f:
        mocked_results = json.load(f)

    mocked_elasticsearch.search = Mock(return_value=mocked_results)
    search_service = f"/search/{search_router.resource_name_plural}/v1"
    params = {"search_query": "description", "limit": 1001}
    response = client.get(search_service, params=params)

    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == [
        {
            "ctx": {"limit_value": 1000},
            "loc": ["query", "limit"],
            "msg": "ensure this value is less than or equal to 1000",
            "type": "value_error.number.not_le",
        }
    ]


@pytest.mark.parametrize("search_router", sr.router_list)
def test_search_bad_offset(client: TestClient, search_router):
    """Tests the search router bad fields error"""
    mocked_elasticsearch = Elasticsearch("https://example.com:9200")
    ElasticsearchSingleton().patch(mocked_elasticsearch)

    resources_path = os.path.join(path_test_resources(), "elasticsearch")
    resource_file = f"{search_router.es_index}_search.json"
    mocked_file = os.path.join(resources_path, resource_file)
    with open(mocked_file, "r") as f:
        mocked_results = json.load(f)

    mocked_elasticsearch.search = Mock(return_value=mocked_results)
    search_service = f"/search/{search_router.resource_name_plural}/v1"
    params = {"search_query": "description", "offset": -1}
    response = client.get(search_service, params=params)

    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == [
        {
            "ctx": {"limit_value": 0},
            "loc": ["query", "offset"],
            "msg": "ensure this value is greater than or equal to 0",
            "type": "value_error.number.not_ge",
        }
    ]
