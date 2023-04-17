import copy

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database.model.publication import OrmPublication


@pytest.mark.parametrize("publication_id", [1, 2])
def test_happy_path(client: TestClient, engine: Engine, publication_id: int):
    publications = [
        OrmPublication(
            title="Title 1",
            doi="doi1",
            platform="zenodo",
            platform_identifier="1",
            datasets=[],
        ),
        OrmPublication(
            title="Title 2",
            doi="doi2",
            platform="zenodo",
            platform_identifier="2",
            datasets=[],
        ),
    ]
    with Session(engine) as session:
        # Populate database
        # Deepcopy necessary because SqlAlchemy changes the instance so that accessing the
        # attributes is not possible anymore
        session.add_all(copy.deepcopy(publications))
        session.commit()

    response = client.get(f"/publications/{publication_id}")
    # assert response.status_code == 200
    response_json = response.json()

    expected = publications[publication_id - 1]

    assert response_json["title"] == expected.title
    assert response_json["doi"] == expected.doi
    assert response_json["platform"] == expected.platform
    assert response_json["platform_identifier"] == expected.platform_identifier
    assert response_json["identifier"] == publication_id
    assert len(response_json["datasets"]) == 0
    assert len(response_json) == 6


@pytest.mark.parametrize("publication_id", [-1, 2, 3])
def test_empty_db(client: TestClient, engine: Engine, publication_id):
    response = client.get(f"/publications/{publication_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"Publication '{publication_id}' not found in the database."


@pytest.mark.parametrize("publication_id", [-1, 2, 3])
def test_publication_not_found(client: TestClient, engine: Engine, publication_id):
    publications = [
        OrmPublication(
            title="Title 1", doi="doi1", platform="zenodo", platform_identifier="1", datasets=[]
        )
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(publications)
        session.commit()
    response = client.get(f"/publications/{publication_id}")  # Note that only publication 1 exists
    assert response.status_code == 404
    assert response.json()["detail"] == f"Publication '{publication_id}' not found in the database."
