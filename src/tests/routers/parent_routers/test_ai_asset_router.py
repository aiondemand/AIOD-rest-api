from starlette.testclient import TestClient

from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.session import DbSession


def test_happy_path(
    client: TestClient,
    dataset: Dataset,
    publication: Publication,
):

    dataset.name = "Dataset"
    publication.name = "Publication"
    with DbSession() as session:
        session.add(dataset)
        session.merge(publication)
        session.commit()

    response = client.get("/ai_assets/v1/1")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["ai_asset_identifier"] == 1
    assert response_json["name"] == "Dataset"

    response = client.get("/ai_assets/v1/2")
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert response_json["identifier"] == 1
    assert response_json["ai_asset_identifier"] == 2
    assert response_json["name"] == "Publication"
