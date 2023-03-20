import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database.models import CodeArtifactDescription


@pytest.mark.parametrize(
    "identifier,name,node,doi,node_specific_identifier",
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
    node: str,
    doi: str,
    node_specific_identifier: str,
):
    _setup(engine)
    response = client.put(
        f"/codeartifacts/{identifier}",
        json={
            "name": name,
            "node": node,
            "doi": doi,
            "node_specific_identifier": node_specific_identifier,
        },
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["name"] == name
    assert response_json["node"] == node
    assert response_json["doi"] == doi
    assert response_json["node_specific_identifier"] == node_specific_identifier
    assert response_json["id"] == identifier
    assert len(response_json) == 5


def test_non_existent(client: TestClient, engine: Engine):
    _setup(engine)

    response = client.put(
        "/codeartifacts/4",
        json={"name": "name", "node": "node", "doi": "doi", "node_specific_identifier": "id"},
    )
    assert response.status_code == 404
    response_json = response.json()
    assert response_json["detail"] == "CodeArtifact '4' not found in the database."


def test_partial_update(client: TestClient, engine: Engine):
    _setup(engine)

    response = client.put("/codeartifacts/4", json={"name": "name", "doi": "doi"})
    # Partial update: node and node_specific_identifier omitted. This is not supported,
    # and should be a PATCH request if we supported it.

    assert response.status_code == 422
    response_json = response.json()
    assert response_json["detail"] == [
        {"loc": ["body", "node"], "msg": "field required", "type": "value_error.missing"},
        {
            "loc": ["body", "node_specific_identifier"],
            "msg": "field required",
            "type": "value_error.missing",
        },
    ]


def test_too_long_name(client: TestClient, engine: Engine):
    _setup(engine)

    name = "a" * 300
    response = client.put(
        "/codeartifacts/2",
        json={"name": name, "doi": "doi", "node": "node", "node_specific_identifier": "id"},
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
        CodeArtifactDescription(
            name="code1", node="openml", doi="doi1", node_specific_identifier="1"
        ),
        CodeArtifactDescription(
            name="code1", node="other_node", doi="doi1", node_specific_identifier="1"
        ),
        CodeArtifactDescription(
            name="code2", node="other_node", doi="doi2", node_specific_identifier="2"
        ),
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(datasets)
        session.commit()
