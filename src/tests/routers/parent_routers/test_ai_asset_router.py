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

        response = client.get(f"/ai_assets/{dataset.identifier}")
        assert response.status_code == 200, response.json()
        response_json = response.json()
        assert response_json["identifier"] == dataset.identifier
        assert response_json["ai_asset_identifier"] == dataset.identifier
        assert response_json["name"] == "Dataset"

        response = client.get(f"/ai_assets/{publication.identifier}")
        assert response.status_code == 200, response.json()
        response_json = response.json()
        assert response_json["identifier"] == publication.identifier
        assert response_json["ai_asset_identifier"] == publication.identifier
        assert response_json["name"] == "Publication"
