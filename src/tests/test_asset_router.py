import datetime

from starlette.testclient import TestClient
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.session import DbSession
import pytest


@pytest.mark.parametrize(
    "asset",
    [
        "organisation", # agent
        "person",   # agent
        "dataset",  # ai_asset
        "publication",  # ai_asset
    ]
)
def test_get_assets(
    client: TestClient,
    asset: str,
    request,
):
    asset_obj = request.getfixturevalue(asset)
    asset_obj.name = asset

    with DbSession() as session:
        session.merge(asset_obj)
        session.commit()

    response = client.get(f"assets?identifier={asset_obj.identifier}")  # type: ignore[attr-defined]
    assert response.status_code == 200, response.json()
    response_json = response.json()
    assert response_json["identifier"] == asset_obj.identifier  # type: ignore[attr-defined]


def test_ignore_deleted(
    client: TestClient,
    organisation: Organisation,
    person: Person,
):

    organisation.name = "Organisation"
    organisation.date_deleted = datetime.datetime.now()
    person.name = "Person"
    with DbSession() as session:
        session.add(organisation)
        session.merge(person)
        session.commit()

        response = client.get(f"/assets?identifier={organisation.identifier}")
        assert response.status_code == 404, response.json()

        response = client.get(f"/assets?identifier={person.identifier}")
        assert response.status_code == 200, response.json()
