import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient
from database.model.code_artifact import OrmCodeArtifact


def test_happy_path(client: TestClient, engine: Engine):
    publications = [
        OrmCodeArtifact(
            name="code1",
            doi="doi1",
            platform="zenodo",
            platform_identifier="1",
        ),
        OrmCodeArtifact(
            name="code1",
            doi="doi1",
            platform="other_node",
            platform_identifier="1",
        ),
        OrmCodeArtifact(
            name="code2",
            doi="doi2",
            platform="other_node",
            platform_identifier="2",
        ),
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(publications)
        session.commit()

    response = client.post(
        "/code_artifacts/v0",
        json={"name": "code2", "doi": "doi2", "platform": "zenodo", "platform_identifier": "2"},
    )
    assert response.status_code == 200

    response_json = response.json()
    assert response_json["name"] == "code2"
    assert response_json["doi"] == "doi2"
    assert response_json["platform"] == "zenodo"
    assert response_json["platform_identifier"] == "2"
    assert response_json["identifier"] == 4
    assert len(response_json) == 5


@pytest.mark.parametrize(
    "name",
    ["\"'é:?", "!@#$%^&*()`~", "Ω≈ç√∫˜µ≤≥÷", "田中さんにあげて下さい", " أي بعد, ", "𝑻𝒉𝒆 𝐪𝐮𝐢𝐜𝐤", "گچپژ"],
)
def test_unicode(client: TestClient, engine: Engine, name):
    response = client.post(
        "/code_artifacts/v0",
        json={"name": name, "doi": "doi2", "platform": "zenodo", "platform_identifier": "2"},
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["name"] == name


def test_duplicated_codeartifact(client: TestClient, engine: Engine):
    codeartifacts = [
        OrmCodeArtifact(name="code1", doi="doi1", platform="zenodo", platform_identifier="1")
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(codeartifacts)
        session.commit()
    response = client.post(
        "/code_artifacts/v0",
        json={"name": "code1", "doi": "doi1", "platform": "zenodo", "platform_identifier": "1"},
    )
    assert response.status_code == 409
    assert (
        response.json()["detail"] == "There already exists a code_artifact with the same platform "
        "and name, with identifier=1."
    )


# Test if the api allows creating publications with not all fields
@pytest.mark.parametrize("field", ["name"])
def test_missing_value(client: TestClient, engine: Engine, field: str):
    data = {
        "name": "code2",
        "doi": "doi2",
        "platform": "zenodo",
        "platform_identifier": "2",
    }  # type: typing.Dict[str, typing.Any]
    del data[field]
    response = client.post("/code_artifacts/v0", json=data)
    assert response.status_code == 422
    assert response.json()["detail"] == [
        {"loc": ["body", field], "msg": "field required", "type": "value_error.missing"}
    ]


@pytest.mark.parametrize("field", ["name", "platform"])
def test_null_value(client: TestClient, engine: Engine, field: str):
    data = {
        "name": "code2",
        "doi": "doi2",
        "platform": "zenodo",
        "platform_identifier": "2",
    }  # type: typing.Dict[str, typing.Any]
    data[field] = None
    response = client.post("/code_artifacts/v0", json=data)
    assert response.status_code == 422
    assert response.json()["detail"] == [
        {
            "loc": ["body", field],
            "msg": "none is not an allowed value",
            "type": "type_error.none.not_allowed",
        }
    ]
