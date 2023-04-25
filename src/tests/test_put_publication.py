import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from database.model.publication import OrmPublication


@pytest.mark.parametrize(
    "identifier,title,url,doi,platform,platform_identifier",
    [
        (1, "NEW NAME", "url1", "doi1", "zenodo", "1"),
        (1, "pub1", "url1", "doi1", "zenodo", "new-id"),
        (1, "pub1", "url1", "doi1", "other_platform", "3"),
        (3, "pub2", "url3", "doi1", "other_platform", "3"),
    ],
)
def test_happy_path(
    client: TestClient,
    engine: Engine,
    identifier: int,
    title: str,
    url: str,
    doi: str,
    platform: str,
    platform_identifier: str,
):
    _setup(engine)
    response = client.put(
        f"/publications/v0/{identifier}",
        json={
            "title": title,
            "url": url,
            "doi": doi,
            "platform": platform,
            "platform_identifier": platform_identifier,
        },
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["title"] == title
    assert response_json["url"] == url
    assert response_json["doi"] == doi
    assert response_json["platform"] == platform
    assert response_json["platform_identifier"] == platform_identifier
    assert response_json["identifier"] == identifier
    assert len(response_json["datasets"]) == 0
    assert len(response_json) == 7


def test_non_existent(client: TestClient, engine: Engine):
    _setup(engine)

    response = client.put(
        "/publications/v0/4",
        json={"title": "pub2", "doi": "doi2", "platform": "zenodo", "platform_identifier": "2"},
    )
    assert response.status_code == 404
    response_json = response.json()
    assert response_json["detail"] == "Publication '4' not found in the database."


def test_partial_update(client: TestClient, engine: Engine):
    _setup(engine)

    response = client.put("/publications/v0/4", json={"doi": "doi"})
    # Partial update: title omitted. This is not supported,
    # and should be a PATCH request if we supported it.

    assert response.status_code == 422
    response_json = response.json()
    assert response_json["detail"] == [
        {"loc": ["body", "title"], "msg": "field required", "type": "value_error.missing"},
    ]


def test_too_long_name(client: TestClient, engine: Engine):
    _setup(engine)

    title = "a" * 300
    response = client.put(
        "/publications/v0/3",
        json={"title": title, "doi": "doi2", "platform": "platform", "platform_identifier": "id"},
    )
    assert response.status_code == 422
    response_json = response.json()
    assert response_json["detail"] == [
        {
            "ctx": {"limit_value": 250},
            "loc": ["body", "title"],
            "msg": "ensure this value has at most 250 characters",
            "type": "value_error.any_str.max_length",
        }
    ]


def _setup(engine):
    datasets = [
        OrmPublication(title="pub1", doi="doi1", platform="zenodo", platform_identifier="1"),
        OrmPublication(title="pub1", doi="doi2", platform="other", platform_identifier="1"),
        OrmPublication(title="pub2", doi="doi3", platform="zenodo", platform_identifier="2"),
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(datasets)
        session.commit()
