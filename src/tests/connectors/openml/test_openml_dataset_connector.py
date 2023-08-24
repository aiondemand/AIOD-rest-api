import json

import responses

from connectors.openml.openml_dataset_connector import OpenMlDatasetConnector
from tests.testutils.paths import path_test_resources

OPENML_URL = "https://www.openml.org/api/v1/json"


def test_first_run():
    connector = OpenMlDatasetConnector(limit_per_iteration=2)
    with responses.RequestsMock() as mocked_requests:
        for offset in (0, 2):
            mock_list_data(mocked_requests, offset)
        for i in range(2, 5):
            mock_get_data(mocked_requests, str(i))

        datasets = list(connector.run(state={}, from_identifier=0, limit=None))
    assert {d.name for d in datasets} == {"anneal", "labor", "kr-vs-kp"}
    assert len(datasets) == 3
    assert {len(d.citation) for d in datasets} == {0}


def test_second_run():
    connector = OpenMlDatasetConnector(limit_per_iteration=2)
    with responses.RequestsMock() as mocked_requests:
        mock_list_data(mocked_requests, offset=2)
        mock_get_data(mocked_requests, "4")
        datasets = list(
            connector.run(state={"offset": 2, "last_id": 3}, from_identifier=0, limit=None)
        )
    assert len(datasets) == 1
    assert {d.name for d in datasets} == {"labor"}


def test_second_run_wrong_identifier():
    connector = OpenMlDatasetConnector(limit_per_iteration=2)
    with responses.RequestsMock() as mocked_requests:
        mock_list_data(mocked_requests, offset=2)
        mock_get_data(mocked_requests, "4")
        datasets = list(
            connector.run(state={"offset": 2, "last_id": 1}, from_identifier=0, limit=None)
        )
    assert len(datasets) == 1
    assert {d.name for d in datasets} == {"labor"}


def mock_list_data(mocked_requests, offset):
    """
    Mocking requests to the OpenML dependency, so that we test only our own services
    """

    with open(
        path_test_resources() / "connectors" / "openml" / f"list_offset_{offset}.json",
        "r",
    ) as f:
        data_response = json.load(f)
    mocked_requests.add(
        responses.GET,
        f"{OPENML_URL}/data/list/limit/2/offset/{offset}",
        json=data_response,
        status=200,
    )


def mock_get_data(mocked_requests: responses.RequestsMock, platform_identifier: str):
    """
    Mocking requests to the OpenML dependency, so that we test only our own services
    """

    with open(
        path_test_resources() / "connectors" / "openml" / f"data_{platform_identifier}.json",
        "r",
    ) as f:
        data_response = json.load(f)
    mocked_requests.add(
        responses.GET,
        f"{OPENML_URL}/data/{platform_identifier}",
        json=data_response,
        status=200,
    )


def mock_get_qualities(mocked_requests: responses.RequestsMock, platform_identifier: str):
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
