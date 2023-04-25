from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database.model.dataset import OrmDataset

OPENML_URL = "https://www.openml.org/api/v1/json"


def test_happy_path(client: TestClient, engine: Engine):
    dataset_description = OrmDataset(
        name="anneal",
        platform="openml",
        description="description text",
        same_as="",
        platform_identifier="1",
    )
    with Session(engine) as session:
        session.add(dataset_description)
        session.commit()
    response = client.get("/platforms/openml/datasets/v0/1")
    assert response.status_code == 200
    response_json = response.json()

    assert response_json["name"] == "anneal"
    assert response_json["description"] == "description text"
    assert response_json["identifier"] == 1
    assert "deprecated" not in response.headers


def test_dataset_not_found_in_local_db(client: TestClient, engine: Engine):
    dataset_description = OrmDataset(
        name="anneal", platform="openml", description="", same_as="", platform_identifier="1"
    )
    with Session(engine) as session:
        # Populate database
        session.add(dataset_description)
        session.commit()
    response = client.get("/platforms/openml/datasets/v0/2")  # Note that only dataset 1 exists
    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset '2' of 'openml' not found in the database."


def test_wrong_platform(client: TestClient, engine: Engine):
    dataset_description = OrmDataset(
        name="anneal", platform="example", description="", same_as="", platform_identifier="1"
    )
    with Session(engine) as session:
        # Populate database
        session.add(dataset_description)
        session.commit()
    response = client.get("/platforms/openml/datasets/v0/1")
    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset '1' of 'openml' not found in the database."


def test_unexisting_platform(client: TestClient, engine: Engine):
    dataset_description = OrmDataset(
        name="anneal",
        platform="openml",
        description="",
        same_as="",
        platform_identifier="1",
    )
    with Session(engine) as session:
        # Populate database
        session.add(dataset_description)
        session.commit()
    response = client.get("/platforms/unexisting_platform/datasets/v0/1")
    assert response.status_code == 400
    assert response.json()["detail"] == "platform 'unexisting_platform' not recognized."
