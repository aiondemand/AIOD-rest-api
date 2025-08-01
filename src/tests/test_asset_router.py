import datetime

from starlette.testclient import TestClient
from database.model.agent.organisation import Organisation
from database.session import DbSession
import pytest
from http import HTTPStatus


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

    response = client.get(f"assets/{asset_obj.identifier}")  # type: ignore[attr-defined]
    assert response.status_code == HTTPStatus.OK, response.json()
    response_json = response.json()
    assert response_json["identifier"] == asset_obj.identifier  # type: ignore[attr-defined]


def test_ignore_deleted(
    client: TestClient,
    organisation: Organisation,
):

    organisation.name = "organisation"
    organisation.date_deleted = datetime.datetime.now()
    with DbSession() as session:
        session.add(organisation)
        session.commit()

        response = client.get(f"/assets/{organisation.identifier}")
        assert response.status_code == HTTPStatus.NOT_FOUND, response.json()
