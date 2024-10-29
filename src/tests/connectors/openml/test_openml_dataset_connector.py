import json
import responses

from connectors.openml.openml_dataset_connector import OpenMlDatasetConnector
from tests.testutils.paths import path_test_resources

OPENML_URL = "https://www.openml.org/api/v1/json"


def test_first_run():
    state = {}
    connector = OpenMlDatasetConnector(limit_per_iteration=2)
    with responses.RequestsMock() as mocked_requests:
        for offset in (0, 2):
            mock_list_data(mocked_requests, offset)
        for i in range(2, 5):
            mock_get_data(mocked_requests, str(i))

        datasets = list(connector.run(state, from_identifier=0, limit=None))

    assert state["last_id"] == 4, state
    assert {d.name for d in datasets} == {"anneal", "labor", "kr-vs-kp"}
    assert len(datasets) == 3
    assert {len(d.citation) for d in datasets} == {0}


def test_request_empty_list():
    """Tests if the state doesn't change after a request when OpenML returns an empty list."""
    state = {"last_id": 3}
    connector = OpenMlDatasetConnector(limit_per_iteration=2)
    with responses.RequestsMock() as mocked_requests:
        mocked_requests.add(
            responses.GET,
            f"{OPENML_URL}/data/list/limit/2/offset/0",
            json={"error": {"code": "372", "message": "No results"}},
            status=412,
        )
        datasets = list(connector.run(state, from_identifier=0, limit=None))

        assert len(datasets) == 1, datasets
        assert "No results" in datasets[0].error.args[0], datasets
        assert state["last_id"] == 3, state


def test_second_run():
    connector = OpenMlDatasetConnector(limit_per_iteration=2)

    state = {"last_id": 3}  # state from last run
    with responses.RequestsMock() as mocked_requests:
        mock_list_data(
            mocked_requests, offset=0
        )  # Mock the first call to fetch datasets with offset=0
        mock_list_data(
            mocked_requests, offset=2
        )  # Mock the second call for pagination with offset=2
        mock_get_data(mocked_requests, "4")
        datasets = list(connector.run(state=state, from_identifier=1, limit=None))

    assert len(datasets) == 1
    assert {d.name for d in datasets} == {"labor"}
    assert state["last_id"] == 4, state
    assert state["from_id"] == 4, state  # state["from_id"] = state["last_id"] + 1


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


def mock_get_data(mocked_requests: responses.RequestsMock, platform_resource_identifier: str):
    """
    Mocking requests to the OpenML dependency, so that we test only our own services
    """

    with open(
        path_test_resources()
        / "connectors"
        / "openml"
        / f"data_{platform_resource_identifier}.json",
        "r",
    ) as f:
        data_response = json.load(f)
    mocked_requests.add(
        responses.GET,
        f"{OPENML_URL}/data/{platform_resource_identifier}",
        json=data_response,
        status=200,
    )


def mock_get_qualities(mocked_requests: responses.RequestsMock, platform_resource_identifier: str):
    """
    Mocking requests to the OpenML dependency, so that we test only our own services
    """

    with open(
        path_test_resources()
        / "connectors"
        / "openml"
        / f"data_{platform_resource_identifier}.json",
        "r",
    ) as f:
        data_response = json.load(f)
    with open(
        path_test_resources()
        / "connectors"
        / "openml"
        / f"data_{platform_resource_identifier}_qualities.json",
        "r",
    ) as f:
        data_qualities_response = json.load(f)

    mocked_requests.add(
        responses.GET,
        f"{OPENML_URL}/data/{platform_resource_identifier}",
        json=data_response,
        status=200,
    )
    mocked_requests.add(
        responses.GET,
        f"{OPENML_URL}/data/qualities/{platform_resource_identifier}",
        json=data_qualities_response,
        status=200,
    )
