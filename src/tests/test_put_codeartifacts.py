import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database.model.code_artifact import OrmCodeArtifact


@pytest.mark.parametrize(
    "identifier,name,platform,doi,platform_identifier",
    [
        (1, "NEW NAME", "zenodo", "doi1", "1"),
        (1, "code1", "zenodo", "doi1", "new-id"),
        (1, "code1", "other_node", "doi1", "3"),
        (3, "CODE2", "other_node", "doi2", "3"),
    ],
)
def test_happy_path(
    client: TestClient,
    engine: Engine,
    identifier: int,
    name: str,
    platform: str,
    doi: str,
    platform_identifier: str,
):
    _setup(engine)
    response = client.put(
        f"/code_artifacts/{identifier}",
        json={
            "name": name,
            "platform": platform,
            "doi": doi,
            "platform_identifier": platform_identifier,
        },
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["name"] == name
    assert response_json["platform"] == platform
    assert response_json["doi"] == doi
    assert response_json["platform_identifier"] == platform_identifier
    assert response_json["identifier"] == identifier
    assert len(response_json) == 5


def test_non_existent(client: TestClient, engine: Engine):
    _setup(engine)

    response = client.put(
        "/code_artifacts/4",
        json={"name": "name", "platform": "platform", "doi": "doi", "platform_identifier": "id"},
    )
    assert response.status_code == 404
    response_json = response.json()
    assert response_json["detail"] == "Code_artifact '4' not found in the database."


def test_partial_update(client: TestClient, engine: Engine):
    _setup(engine)

    response = client.put("/code_artifacts/4", json={"doi": "doi"})
    # Partial update: node and node_specific_identifier omitted. This is not supported,
    # and should be a PATCH request if we supported it.

    assert response.status_code == 422
    response_json = response.json()
    assert response_json["detail"] == [
        {"loc": ["body", "name"], "msg": "field required", "type": "value_error.missing"},
    ]


def test_too_long_name(client: TestClient, engine: Engine):
    _setup(engine)

    name = "a" * 300
    response = client.put(
        "/code_artifacts/2",
        json={"name": name, "doi": "doi", "platform": "platform", "platform_identifier": "id"},
    )
    assert response.status_code == 422
    response_json = response.json()
    assert response_json["detail"] == [
        {
            "ctx": {"limit_value": 250},
            "loc": ["body", "name"],
            "msg": "ensure this value has at most 250 characters",
            "type": "value_error.any_str.max_length",
        }
    ]


def _setup(engine):
    datasets = [
        OrmCodeArtifact(name="code1", platform="openml", doi="doi1", platform_identifier="1"),
        OrmCodeArtifact(name="code1", platform="other_node", doi="doi1", platform_identifier="1"),
        OrmCodeArtifact(name="code2", platform="other_node", doi="doi2", platform_identifier="2"),
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(datasets)
        session.commit()
