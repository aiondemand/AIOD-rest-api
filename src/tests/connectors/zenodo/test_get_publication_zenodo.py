import copy
import json

import pytest
import responses
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database.model.publication import OrmPublication
from tests.testutils.paths import path_test_resources

ZENODO_URL = "https://zenodo.org/api"


@pytest.mark.skip(reason="TODO[arejula27]: implement, similar to the dataset connector test?")
def test_happy_path(client: TestClient, engine: Engine):
    publication_description = OrmPublication(
        identifier=1,
        title="Student-Centred Studio Environments: A Deep Dive into Architecture Students' Needs",
        doi="10.5281/zenodo.7712947",
        platform="zenodo",
        platform_identifier="7712947",
    )
    with Session(engine) as session:
        # Populate database.
        # Deepcopy necessary because SqlAlchemy changes the instance so that accessing the
        # platform_identifier is not possible anymore
        session.add(copy.deepcopy(publication_description))
        session.commit()

    # TODO[arejula27]: I uncommented these parts
    # assert response_json["doi"] == expected_info["doi"]
    # assert response_json["title"] == expected_info["metadata"]["title"]


@pytest.mark.skip(reason="TODO[arejula27]: implement, similar to the dataset connector test?")
def test_publication_not_found_in_local_db(client: TestClient, engine: Engine):

    publication_description = OrmPublication(
        identifier=1,
        title="Student-Centred Studio Environments: A Deep Dive into Architecture Students' Needs",
        doi="10.5281/zenodo.7712947",
        platform="zenodo",
        platform_identifier="7712947",
    )
    with Session(engine) as session:
        session.add(publication_description)
        session.commit()

    response = client.get("/platforms/zenodo/publications/2")  # Note that only dataset 1 exists
    assert response.status_code == 404
    assert response.json()["detail"] == "Publication '2' of 'zenodo' not found in the database."


@pytest.mark.skip(reason="TODO[arejula27]: implement, similar to the dataset connector test?")
def test_publication_not_found_in_zenodo(client: TestClient, engine: Engine):
    publication_description = OrmPublication(
        identifier=1,
        title="Student-Centred Studio Environments: A Deep Dive into Architecture Students' Needs",
        doi="10.5281/zenodo.7712947",
        platform="zenodo",
        platform_identifier="7712947",
    )
    with Session(engine) as session:
        session.add(publication_description)
        session.commit()

    with responses.RequestsMock() as mocked_requests:
        mocked_requests.add(
            responses.GET,
            f"{ZENODO_URL}/records/{publication_description.platform_identifier}",
            json={"status": "404", "message": "PID does not exist."},
            status=404,
        )
        response = client.get("/platforms/zenodo/publications/7712947")
    assert response.status_code == 404
    assert (
        response.json()["detail"] == "Error while fetching data from Zenodo: 'PID does not exist.'"
    )


def _mock_normal_responses(
    mocked_requests: responses.RequestsMock, publication_description: OrmPublication
):
    """
    Mocking requests to the OpenML dependency, so that we test only our own services
    """
    with open(path_test_resources() / "connectors" / "zenodo" / "data_1.json", "r") as f:
        data_response = json.load(f)

    mocked_requests.add(
        responses.GET,
        f"{ZENODO_URL}/records/{publication_description.platform_identifier}",
        json=data_response,
        status=200,
    )
