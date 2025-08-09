from http import HTTPStatus
from typing import Callable

from starlette.testclient import TestClient

from database.authorization import set_permission, PermissionType, register_user
from database.model.knowledge_asset.publication import Publication
from database.model.concept.aiod_entry import EntryStatus
from database.session import DbSession
from database.model.agent.organisation import Organisation
from tests.testutils.users import register_asset, logged_in_user, ALICE, BOB
from tests.testutils.default_instances import publication_factory, publication


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
