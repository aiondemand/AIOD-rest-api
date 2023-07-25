from unittest.mock import Mock

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.model.ai_asset_table_old import AIAssetOldTable
from database.model.dataset.dataset import Dataset


def test_happy_path(client: TestClient, engine: Engine, mocked_privileged_token: Mock):
    keycloak_openid.userinfo = mocked_privileged_token
    asset = AIAssetOldTable(type="dataset")
    dataset_description = Dataset(
        identifier="1",
        name="Parent",
        platform="example",
        platform_identifier="1",
        description="description text",
        same_as="",
    )
    with Session(engine) as session:
        session.add_all([asset, dataset_description])
        session.commit()

    body = {
        "platform": "zenodo",
        "platform_identifier": "1",
        "title": "A publication",
        "doi": "0000000/000000000000",
        "creators": "John Doe",
        "access_right": "open access",
        "date_created": "2022-01-01T15:15:00.000Z",
        "date_published": "2023-01-01T15:15:00.000Z",
        "url": "https://www.example.com/publication/example",
        "datasets": [1],
        "license": "https://creativecommons.org/share-your-work/public-domain/cc0/",
        "resource_type": "journal article",
    }
    response = client.post("/publications/v0", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200

    response = client.get("/publications/v0/2")
    assert response.status_code == 200

    response_json = response.json()
    assert response_json["identifier"] == 2
    assert response_json["title"] == "A publication"
    assert (
        response_json["license"] == "https://creativecommons.org/share-your-work/public-domain/cc0/"
    )
    assert response_json["resource_type"] == "journal article"
    assert len(response_json["datasets"]) == 1
    assert response_json["datasets"] == [1]

    response = client.delete("/publications/v0/2", headers={"Authorization": "Fake token"})
    assert response.status_code == 200
