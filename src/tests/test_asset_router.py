import datetime
import json

import pytest
from http import HTTPStatus

from sqlmodel import select
from starlette.testclient import TestClient
import responses

from database.authorization import register_user, PermissionType, Permission, set_permission
from database.model.agent.organisation import Organisation
from database.session import DbSession

from database.model.knowledge_asset.publication import Publication
from tests.testutils.users import logged_in_user, register_asset, ALICE, BOB
from tests.testutils.paths import path_test_resources


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


def test_add_permission_by_name(
        client: TestClient,
        publication: Publication,
):
    identifier = register_asset(publication, owner=ALICE)
    with DbSession() as session:
        register_user(BOB, session)
        session.commit()

    cached_api_token = path_test_resources() / "authentication" / "admin_connect.json"
    with cached_api_token.open("r") as f:
        connect_response = json.load(f)

    cached_user_response = path_test_resources() / "authentication" / "query_bob.json"
    with cached_user_response.open("r") as f:
        users_response = json.load(f)

    # The second time around the cached KeycloakAdmin is used, so the connect is not called
    with responses.RequestsMock(assert_all_requests_are_fired=False) as request_mock:
        request_mock.add(
            responses.POST,
            "http://keycloak:8080/aiod-auth/realms/aiod/protocol/openid-connect/token",
            json=connect_response,
        )
        request_mock.add(
            responses.GET,
            "http://keycloak:8080/aiod-auth/admin/realms/aiod/users?username=bob&max=1&exact=True",
            json=users_response,
        )

        with logged_in_user(ALICE):
            response = client.post(
                f"/assets/permissions",
                json={"user": BOB.name, "asset_identifier": identifier, "permission_type": PermissionType.WRITE.value},
                headers={"Authorization": "fake-token"},
            )
        assert response.status_code == HTTPStatus.OK

        with DbSession() as session:
            permission = session.get(Permission, {"aiod_entry_identifier": 1 , "user_identifier": BOB._subject_identifier})
        assert permission is not None
        assert permission.type_ == PermissionType.WRITE


def test_show_permission(
        client: TestClient,
        publication: Publication,
):
    identifier = register_asset(publication, owner=ALICE)
    with DbSession() as session:
        register_user(BOB, session)
        publication = session.scalar(select(Publication))
        set_permission(BOB, publication.aiod_entry, session, type_=PermissionType.WRITE)
        session.commit()

    cached_api_token = path_test_resources() / "authentication" / "admin_connect.json"
    with cached_api_token.open("r") as f:
        connect_response = json.load(f)

    cached_user_response = path_test_resources() / "authentication" / "query_alice.json"
    with cached_user_response.open("r") as f:
        alice_response = json.load(f)
        alice_response = alice_response[0]  # default json returns "multiple" user response

    cached_user_response = path_test_resources() / "authentication" / "query_bob.json"
    with cached_user_response.open("r") as f:
        bob_response = json.load(f)
        bob_response = bob_response[0]  # default json returns "multiple" user response

    # The second time around the cached KeycloakAdmin is used, so the connect is not called
    with responses.RequestsMock(assert_all_requests_are_fired=False) as request_mock:
        request_mock.add(
            responses.POST,
            "http://keycloak:8080/aiod-auth/realms/aiod/protocol/openid-connect/token",
            json=connect_response,
        )
        request_mock.add(
            responses.GET,
            "http://keycloak:8080/aiod-auth/admin/realms/aiod/users/bob00000-0000-0000-0000-000000000000",
            json=bob_response,
        )

        request_mock.add(
            responses.GET,
            "http://keycloak:8080/aiod-auth/admin/realms/aiod/users/alice000-0000-0000-0000-000000000000",
            json=alice_response,
        )

        with logged_in_user(ALICE):
            response = client.get(
                f"/assets/permissions/{identifier}",
                headers={"Authorization": "fake-token"},
            )
        assert response.status_code == HTTPStatus.OK
        server_permissions = {p["name"]: p["permission"] for p in response.json()}
        assert server_permissions == {"Alice": "admin", "Bob": "write"}
