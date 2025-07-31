import datetime

from starlette.testclient import TestClient


from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.session import DbSession
import pytest

def test_get_assets_by_identifier(
    client: TestClient,
    organisation: Organisation,
    person: Person,
    dataset: Dataset,
    publication: Publication,
):
    organisation.name = "Test Org"
    person.name = "Test Person"
    dataset.name = "Test Dataset"
    publication.name = "Test Publication"

    with DbSession() as session:
        session.merge(organisation)
        session.merge(dataset)
        session.merge(publication)
        session.merge(person)
        session.commit()

    for asset in [organisation, person, dataset, publication]:
        response = client.get(f"assets?identifier={asset.identifier}")
        assert response.status_code == 200, response.json()
        response_json = response.json()
        assert response_json["identifier"] == asset.identifier
        assert response_json["name"].startswith("Test") 


@pytest.mark.skip()
def test_deleted_assets_are_not_returned(
    client: TestClient,
    organisation: Organisation,
    person: Person,
):
    pass
@pytest.mark.skip()
def test_unknown_prefix_returns_404(client: TestClient):
    pass
