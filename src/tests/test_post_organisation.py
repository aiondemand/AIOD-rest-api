import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient


from database.model.organisation import OrmOrganisation
from platform_names import PlatformName


def test_happy_path(client: TestClient, engine: Engine):
    organisations = [
        OrmOrganisation(
            platform=PlatformName.aiod,
            platform_identifier=None,
            name="string",
            description="string",
            connection_to_ai="string",
            type="string",
            image_url="string",
        ),
        OrmOrganisation(
            platform=PlatformName.aiod,
            platform_identifier=None,
            name="string2",
            description="string2",
            connection_to_ai="string2",
            type="string",
            image_url="string",
        ),
        OrmOrganisation(
            platform=PlatformName.aiod,
            platform_identifier=None,
            name="string3",
            description="string3",
            connection_to_ai="string3",
            type="string",
            image_url="string",
        ),
    ]

    with Session(engine) as session:
        # Populate database
        session.add_all(organisations)
        session.commit()

    response = client.post(
        "/organisations/v0",
        json={
            "platform": PlatformName.aiod,
            "platform_identifier": None,
            "name": "string",
            "description": "string",
            "connection_to_ai": "string",
            "type": "string",
            "image_url": "string",
        },
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["name"] == "string"
    assert response_json["description"] == "string"
    assert response_json["connection_to_ai"] == "string"
    assert response_json["type"] == "string"
    assert response_json["identifier"] == 4


@pytest.mark.parametrize(
    "name",
    ["\"'é:?", "!@#$%^&*()`~", "Ω≈ç√∫˜µ≤≥÷", "田中さんにあげて下さい", " أي بعد, ", "𝑻𝒉𝒆 𝐪𝐮𝐢𝐜𝐤", "گچپژ"],
)
def test_unicode(client: TestClient, engine: Engine, name):
    response = client.post(
        "/organisations/v0",
        json={
            "platform": PlatformName.aiod,
            "platform_identifier": None,
            "name": name,
            "description": "string",
            "connection_to_ai": "string",
            "type": "string",
            "image_url": "string",
        },
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["name"] == name


@pytest.mark.parametrize(
    "field",
    [
        "type",
    ],
)
def test_missing_value(client: TestClient, engine: Engine, field: str):
    data = {
        "platform": PlatformName.aiod,
        "platform_identifier": None,
        "name": "string",
        "description": "string",
        "connection_to_ai": "string",
        "type": "string",
        "image_url": "string",
    }  # type: typing.Dict[str, typing.Any]
    del data[field]
    response = client.post("/organisations/v0", json=data)
    assert response.status_code == 422
    assert response.json()["detail"] == [
        {"loc": ["body", field], "msg": "field required", "type": "value_error.missing"}
    ]


@pytest.mark.parametrize(
    "field",
    [
        "type",
    ],
)
def test_null_value(client: TestClient, engine: Engine, field: str):
    data = {
        "platform": PlatformName.aiod,
        "platform_identifier": None,
        "name": "string",
        "description": "string",
        "connection_to_ai": "string",
        "type": "string",
        "image_url": "string",
    }  # type: typing.Dict[str, typing.Any]
    data[field] = None
    response = client.post("/organisations/v0", json=data)
    assert response.status_code == 422
    assert response.json()["detail"] == [
        {
            "loc": ["body", field],
            "msg": "none is not an allowed value",
            "type": "type_error.none.not_allowed",
        }
    ]
