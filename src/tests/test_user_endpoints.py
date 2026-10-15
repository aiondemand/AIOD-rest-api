import json
from http import HTTPStatus
from typing import Callable

import pytest
import responses
from starlette.testclient import TestClient

from database.authorization import set_permission, PermissionType, register_user
from database.model.knowledge_asset.publication import Publication
from database.model.concept.aiod_entry import EntryStatus
from database.session import DbSession
from database.model.agent.organisation import Organisation
from authentication import ADMIN_ROLE
from tests.testutils.paths import path_test_resources
from tests.testutils.users import (
    register_asset,
    logged_in_user,
    kc_user_with_roles,
    ALICE,
    BOB,
)
from tests.testutils.default_instances import publication_factory, publication
from versioning import Version


def test_my_resources_can_be_empty(client: TestClient) -> None:
    with logged_in_user(ALICE):
        response = client.get("/user/resources", headers={"Authorization": "fake token"})
    assert response.status_code == HTTPStatus.OK
    msg = "A user with no resources should get an empty list"
    assert all(items == [] for items in response.json().values()), msg
    assert len(response.json()) >= 16, "Every asset type should always be included in the response"


def test_my_resources_shows_draft_assets(client: TestClient, publication: Publication) -> None:
    register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    with logged_in_user(ALICE):
        response = client.get("/user/resources", headers={"Authorization": "fake token"})
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()["publication"]) == 1, "Draft assets should be included in this view."
    msg = "Properties should be deserialized"
    assert response.json()["publication"][0]["aiod_entry"]["status"] == "draft", msg


def test_my_resources_shows_published_assets(client: TestClient, publication: Publication) -> None:
    register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)
    with logged_in_user(ALICE):
        response = client.get("/user/resources", headers={"Authorization": "fake token"})
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()["publication"]) == 1, "Published assets should be included in this view."


def test_my_resources_shows_mixed_assets(client: TestClient, publication: Publication, organisation: Organisation) -> None:
    register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    register_asset(organisation, owner=ALICE, status=EntryStatus.PUBLISHED)
    with logged_in_user(ALICE):
        response = client.get("/user/resources", headers={"Authorization": "fake token"})
    assert response.status_code == HTTPStatus.OK

    assert len(response.json()["contact"]) == 0
    assert len(response.json()["publication"]) == 1
    assert len(response.json()["organisation"]) == 1

    pub = response.json()["publication"][0]
    org = response.json()["organisation"][0]

    dataset_property = "legal_name"
    publication_property = "isbn"

    assert dataset_property in org and publication_property in pub, "Assets should report properties unique to their type"
    assert dataset_property not in pub and publication_property not in org, "Assets should not report properties they do not have"


def test_my_resources_shows_only_own_resources(client: TestClient, publication_factory: Callable[[], Publication]) -> None:
    register_asset(publication_factory(), owner=ALICE, status=EntryStatus.DRAFT)
    register_asset(publication_factory(), owner=ALICE, status=EntryStatus.PUBLISHED)
    register_asset(publication_factory(), owner=BOB, status=EntryStatus.PUBLISHED)

    with logged_in_user(ALICE):
        response = client.get("/user/resources", headers={"Authorization": "fake token"})
        assert len(response.json()["publication"]) == 2

    with logged_in_user(BOB):
        response = client.get("/user/resources", headers={"Authorization": "fake token"})
        assert len(response.json()["publication"]) == 1


def test_my_resources_counts_only_if_admin(client: TestClient, publication_factory: Callable[[], Publication]) -> None:
    asset_one = publication_factory()
    identifier_one = register_asset(asset_one, owner=ALICE, status=EntryStatus.PUBLISHED)
    asset_two = publication_factory()
    identifier_two = register_asset(asset_two, owner=ALICE, status=EntryStatus.PUBLISHED)
    asset_three = publication_factory()
    identifier_three = register_asset(asset_three, owner=ALICE, status=EntryStatus.PUBLISHED)

    with DbSession() as session:
        register_user(BOB, session)
        set_permission(BOB, session.get(Publication, identifier_one).aiod_entry, session, type_=PermissionType.READ)
        set_permission(BOB, session.get(Publication, identifier_two).aiod_entry, session, type_=PermissionType.WRITE)
        set_permission(BOB, session.get(Publication, identifier_three).aiod_entry, session, type_=PermissionType.ADMIN)
        session.commit()

    with logged_in_user(BOB):
        response = client.get("/user/resources", headers={"Authorization": "fake token"})
        assert len(response.json()["publication"]) == 1, "Bob has ADMIN permission to one asset."
        assert response.json()["publication"][0]["identifier"] == identifier_three


def test_my_resources_must_be_authorized(client: TestClient) -> None:
    response = client.get("/user/resources")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_my_resources_paginates(client: TestClient, publication_factory: Publication) -> None:
    register_asset(publication_factory(), owner=ALICE, status=EntryStatus.PUBLISHED)
    register_asset(publication_factory(), owner=ALICE, status=EntryStatus.PUBLISHED)
    register_asset(publication_factory(), owner=ALICE, status=EntryStatus.PUBLISHED)

    with logged_in_user(ALICE):
        response = client.get("/user/resources?limit=2", headers={"Authorization": "fake token"})
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()["publication"]) == 2, "Set limit should be respected"

        first_asset = response.json()["publication"][0]["identifier"]

        response = client.get("/user/resources?offset=1", headers={"Authorization": "fake token"})
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()["publication"]) == 2, "Using an offset can reduce the amount of returned results."
        msg = "Increasing offset should lead to different assets."
        assert first_asset not in [pub["identifier"] for pub in response.json()["publication"]], msg

        response = client.get("/user/resources?offset=1&limit=1", headers={"Authorization": "fake token"})
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()["publication"]) == 1, "Offset and limit should be able to be used together."


@pytest.mark.versions(Version.V2)
def test_my_resources_no_limit_default_in_v2(client: TestClient, publication_factory: Publication) -> None:
    for _ in range(11):  # The default pagination limit is 10
        register_asset(publication_factory(), owner=ALICE, status=EntryStatus.PUBLISHED)

    with logged_in_user(ALICE):
        response = client.get("/user/resources", headers={"Authorization": "fake token"})
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()["publication"]) == 11


@pytest.mark.versions(Version.LATEST)
def test_my_resources_limit_default_in_latest(client: TestClient, publication_factory: Publication) -> None:
    for _ in range(11):  # The default pagination limit is 10
        register_asset(publication_factory(), owner=ALICE, status=EntryStatus.PUBLISHED)

    with logged_in_user(ALICE):
        response = client.get("/user/resources", headers={"Authorization": "fake token"})
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()["publication"]) == 10, "Set limit should be respected"


def _keycloak_mock(request_mock: responses.RequestsMock) -> None:
    """Mock the Keycloak admin calls needed to look up Alice by name and by sub."""
    cached_api_token = path_test_resources() / "authentication" / "admin_connect.json"
    with cached_api_token.open("r") as f:
        connect_response = json.load(f)

    cached_user_response = path_test_resources() / "authentication" / "query_alice.json"
    with cached_user_response.open("r") as f:
        alice_response = json.load(f)

    request_mock.add(
        responses.POST,
        "http://keycloak:8080/aiod-auth/realms/aiod/protocol/openid-connect/token",
        json=connect_response,
    )
    request_mock.add(
        responses.GET,
        "http://keycloak:8080/aiod-auth/admin/realms/aiod/users?username=alice&max=1&exact=True",
        json=alice_response,
    )
    request_mock.add(
        responses.GET,
        f"http://keycloak:8080/aiod-auth/admin/realms/aiod/users/{ALICE._subject_identifier}",
        json=alice_response[0],
    )


@pytest.mark.parametrize("user", [ALICE.name, ALICE._subject_identifier])
def test_other_user_resources_as_admin(client: TestClient, publication_factory: Callable[[], Publication], user: str) -> None:
    register_asset(publication_factory(), owner=ALICE, status=EntryStatus.DRAFT)
    register_asset(publication_factory(), owner=ALICE, status=EntryStatus.PUBLISHED)
    register_asset(publication_factory(), owner=BOB, status=EntryStatus.PUBLISHED)

    with responses.RequestsMock(assert_all_requests_are_fired=False) as request_mock:
        _keycloak_mock(request_mock)
        with logged_in_user(kc_user_with_roles(ADMIN_ROLE)):
            response = client.get(f"/user/{user}/resources", headers={"Authorization": "fake token"})

    assert response.status_code == HTTPStatus.OK, response.json()
    msg = "An admin should see the assets of the requested user only, drafts included."
    assert len(response.json()["publication"]) == 2, msg


def test_other_user_resources_forbidden_for_non_admin(client: TestClient, publication: Publication) -> None:
    register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)
    with logged_in_user(BOB):
        response = client.get(f"/user/{ALICE.name}/resources", headers={"Authorization": "fake token"})
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_other_user_resources_must_be_authorized(client: TestClient) -> None:
    response = client.get(f"/user/{ALICE.name}/resources")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_other_user_resources_unknown_user(client: TestClient) -> None:
    cached_api_token = path_test_resources() / "authentication" / "admin_connect.json"
    with cached_api_token.open("r") as f:
        connect_response = json.load(f)

    with responses.RequestsMock(assert_all_requests_are_fired=False) as request_mock:
        request_mock.add(
            responses.POST,
            "http://keycloak:8080/aiod-auth/realms/aiod/protocol/openid-connect/token",
            json=connect_response,
        )
        request_mock.add(
            responses.GET,
            "http://keycloak:8080/aiod-auth/admin/realms/aiod/users?username=nobody&max=1&exact=True",
            json=[],
        )
        with logged_in_user(kc_user_with_roles(ADMIN_ROLE)):
            response = client.get("/user/nobody/resources", headers={"Authorization": "fake token"})

    assert response.status_code == HTTPStatus.NOT_FOUND
