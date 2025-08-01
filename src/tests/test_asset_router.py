import datetime

from starlette.testclient import TestClient
from database.model.agent.organisation import Organisation
from database.session import DbSession
import pytest
from http import HTTPStatus
from tests.testutils.users import logged_in_user, register_asset


@pytest.mark.parametrize(
    "asset_type",
    [
        "organisation", # agent
        "person",   # agent
        "publication",  # ai_asset
    ]
)
def test_get_assets(
    client: TestClient,
    asset_type: str,
    request,
):
    asset = request.getfixturevalue(asset_type)
    identifier = register_asset(asset)
    with logged_in_user():
        response = client.get(f"assets/{identifier}", headers={"Authorization": "fake-token"})  # type: ignore[attr-defined]

    assert response.status_code == HTTPStatus.OK, response.json()
    response_json = response.json()
    assert response_json["identifier"] == identifier  # type: ignore[attr-defined]


def test_ignore_deleted(
    client: TestClient,
    organisation: Organisation,
):

    organisation.name = "organisation"
    organisation.date_deleted = datetime.datetime.now()
    with DbSession() as session:
        session.add(organisation)
        session.commit()

        with logged_in_user():
            response = client.get(f"/assets/{organisation.identifier}", headers={"Authorization": "fake-token"})
        assert response.status_code == HTTPStatus.NOT_FOUND, response.json()
