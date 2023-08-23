import json

import pytest
import responses

import connectors
from database.model.platform.platform_names import PlatformName
from tests.testutils.paths import path_test_resources

OPENML_URL = "https://www.openml.org/api/v1/json"


@pytest.mark.skip(reason="TODO: while going to Metadata model v2")
def test_fetch_happy_path():
    connector = connectors.dataset_connectors[PlatformName.openml]
    id_ = "2"
    with responses.RequestsMock() as mocked_requests:
        mock_openml_responses(mocked_requests, id_)
        dataset = connector.fetch(id_)
    with open(path_test_resources() / "connectors" / "openml" / "data_2.json", "r") as f:
        expected = json.load(f)["data_set_description"]

    assert dataset.name == "anneal"
    assert dataset.description == expected["description"]
    assert not hasattr(dataset, "identifier")  # will be set when saving to the db
    assert dataset.platform == PlatformName.openml.value
    assert dataset.platform_identifier == id_
    assert dataset.same_as == "https://www.openml.org/api/v1/json/data/2"
    assert len(dataset.citations) == 0
    assert dataset.license == "Public"
    assert dataset.version == "1"
    assert dataset.is_accessible_for_free
    assert dataset.size == 898

    assert len(dataset.distributions) == 1
    (distribution,) = dataset.distributions
    assert distribution.encoding_format == "ARFF"
    assert distribution.content_url == "https://api.openml.org/data/v1/download/1666876/anneal.arff"

    assert len(dataset.keywords) == 9
    assert set(dataset.keywords) == {
        "study_1",
        "study_14",
        "study_34",
        "study_37",
        "study_41",
        "study_70",
        "study_76",
        "test",
        "uci",
    }


@pytest.mark.skip(reason="TODO: while going to Metadata model v2")
def test_fetch_all_happy_path():
    connector = connectors.dataset_connectors[PlatformName.openml]
    with responses.RequestsMock() as mocked_requests:
        with open(path_test_resources() / "connectors" / "openml" / "data_list.json", "r") as f:
            response = json.load(f)
        mocked_requests.add(
            responses.GET, f"{OPENML_URL}/data/list/limit/3", json=response, status=200
        )
        for i in range(2, 5):
            mock_openml_responses(mocked_requests, str(i))
        datasets = list(connector.fetch_all(limit=3))

    assert len(datasets) == 3
    assert {len(d.citations) for d in datasets} == {0}


def mock_openml_responses(mocked_requests: responses.RequestsMock, platform_identifier: str):
    """
    Mocking requests to the OpenML dependency, so that we test only our own services
    """
    with open(
        path_test_resources() / "connectors" / "openml" / f"data_{platform_identifier}.json",
        "r",
    ) as f:
        data_response = json.load(f)
    with open(
        path_test_resources()
        / "connectors"
        / "openml"
        / f"data_{platform_identifier}_qualities.json",
        "r",
    ) as f:
        data_qualities_response = json.load(f)
    mocked_requests.add(
        responses.GET,
        f"{OPENML_URL}/data/{platform_identifier}",
        json=data_response,
        status=200,
    )
    mocked_requests.add(
        responses.GET,
        f"{OPENML_URL}/data/qualities/{platform_identifier}",
        json=data_qualities_response,
        status=200,
    )
