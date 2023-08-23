import json

import pytest
import responses

import connectors
from connectors.resource_with_relations import ResourceWithRelations
from database.model.platform.platform_names import PlatformName
from tests.testutils.paths import path_test_resources

HUGGINGFACE_URL = "https://datasets-server.huggingface.co"


@pytest.mark.skip(reason="TODO: while going to Metadata model v2")
def test_fetch_all_happy_path():
    ids_expected = {
        "0n1xus/codexglue",
        "04-07-22/wep-probes",
        "rotten_tomatoes",
        "acronym_identification",
        "air_dialogue",
    }
    connector = connectors.dataset_connectors[PlatformName.huggingface]
    with responses.RequestsMock() as mocked_requests:
        path_data_list = path_test_resources() / "connectors" / "huggingface" / "data_list.json"
        with open(path_data_list, "r") as f:
            response = json.load(f)
        mocked_requests.add(
            responses.GET,
            "https://huggingface.co/api/datasets?full=True",
            json=response,
            status=200,
        )
        for dataset_id in ids_expected:
            mock_parquet(mocked_requests, dataset_id)
        resources_with_relations = list(connector.fetch_all(limit=None))

    assert len(resources_with_relations) == 5
    assert all(type(r) == ResourceWithRelations for r in resources_with_relations)
    datasets = [r.resource for r in resources_with_relations]
    ids = {d.platform_identifier for d in datasets}
    names = {d.name for d in datasets}
    assert ids == ids_expected
    assert names == ids_expected
    assert all(len(r.related_resources) == 1 for r in resources_with_relations)
    assert all(len(r.related_resources["citations"]) == 1 for r in resources_with_relations)


def mock_parquet(mocked_requests: responses.RequestsMock, dataset_id: str):
    filename = f"parquet_{dataset_id.replace('/', '_')}.json"
    path_split = path_test_resources() / "connectors" / "huggingface" / filename
    with open(path_split, "r") as f:
        response = json.load(f)
    status = 200 if "error" not in response else 404
    mocked_requests.add(
        responses.GET,
        f"{HUGGINGFACE_URL}/parquet?dataset={dataset_id}",
        json=response,
        status=status,
    )
