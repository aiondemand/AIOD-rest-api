import json
import datetime
import responses

from connectors.openml.openml_mlmodel_connector import OpenMlMLModelConnector
from tests.testutils.paths import path_test_resources

OPENML_URL = "https://www.openml.org/api/v1/json"


def test_first_run():
    state = {}
    connector = OpenMlMLModelConnector(limit_per_iteration=2)
    with responses.RequestsMock() as mocked_requests:
        for offset in (0, 2):
            mock_list_data(mocked_requests, offset)
        for i in range(1, 4):
            mock_get_data(mocked_requests, str(i))
        mlmodels = list(connector.run(state, from_identifier=0, limit=None))

    assert state["last_id"] == 3, state
    assert {m.resource.name for m in mlmodels} == {
        "openml.evaluation.EuclideanDistance",
        "openml.evaluation.PolynomialKernel",
        "openml.evaluation.RBFKernel",
    }
    assert len(mlmodels) == 3
    assert {len(m.related_resources["creator"]) for m in mlmodels} == {
        10,
    }


def test_request_empty_list():
    """Tests if the state doesn't change after a request when OpenML returns an empty list."""
    state = {"last_id": 3}
    connector = OpenMlMLModelConnector(limit_per_iteration=2)
    with responses.RequestsMock() as mocked_requests:
        mocked_requests.add(
            responses.GET,
            f"{OPENML_URL}/flow/list/limit/2/offset/0",
            json={"error": {"code": "500", "message": "No results"}},
            status=412,
        )
        ml_models = list(connector.run(state, from_identifier=0, limit=None))

        assert len(ml_models) == 1, ml_models
        assert "No results" in ml_models[0].error.args[0], ml_models
        assert state["last_id"] == 3, state


def test_second_run():
    connector = OpenMlMLModelConnector(limit_per_iteration=2)

    state = {"last_id": 2, "from_id": 0}
    with responses.RequestsMock() as mocked_requests:
        mock_list_data(mocked_requests, offset=0)
        mock_list_data(mocked_requests, offset=2)
        mock_get_data(mocked_requests, "3")
        mlmodels = list(connector.run(state=state, from_identifier=0, limit=None))
    assert state["last_id"] == 3, state
    assert state["from_id"] == 3, state

    assert len(mlmodels) == 1
    assert {m.resource.name for m in mlmodels} == {"openml.evaluation.RBFKernel"}
    mlmodel = mlmodels[0].resource
    assert mlmodel.platform == "openml"
    assert mlmodel.platform_resource_identifier == "3"
    assert mlmodel.description.plain == ('An implementation of the evaluation measure "RBFKernel"')
    assert len(mlmodel.distribution) == 1  # sanity check to confirm only 1 distribution is present.
    assert mlmodel.distribution[0].installation == "Runs on OpenML servers"
    assert mlmodel.date_published == datetime.datetime(2014, 1, 16, 14, 12, 56)
    assert mlmodel.keyword == []
    assert len(mlmodels[0].related_resources["creator"]) == 10
    assert mlmodels[0].related_resources["creator"][0].name == "Jan N. van Rijn"


def mock_list_data(mocked_requests, offset):
    """
    Mocking requests to the OpenML dependency, so that we test only our own services
    """
    with open(
        path_test_resources() / "connectors" / "openml" / f"mlmodel_list_offset_{offset}.json",
        "r",
    ) as f:
        mlmodel_response = json.load(f)
    mocked_requests.add(
        responses.GET,
        f"{OPENML_URL}/flow/list/limit/2/offset/{offset}",
        json=mlmodel_response,
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
        / f"mlmodel_{platform_resource_identifier}.json",
        "r",
    ) as f:
        mlmodel_response = json.load(f)
    mocked_requests.add(
        responses.GET,
        f"{OPENML_URL}/flow/{platform_resource_identifier}",
        json=mlmodel_response,
        status=200,
    )
