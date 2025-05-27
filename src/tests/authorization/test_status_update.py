import copy
from http import HTTPStatus

import pytest
from starlette.testclient import TestClient

from database.model.concept.aiod_entry import EntryStatus
from tests.testutils.users import logged_in_user, ALICE


@pytest.fixture()
def publication_body(body_asset: dict) -> dict:
    body = copy.deepcopy(body_asset)
    body["permanent_identifier"] = "http://dx.doi.org/10.1093/ajae/aaq063"
    body["isbn"] = "9783161484100"
    body["issn"] = "20493630"
    body["type"] = "journal"
    body["content"] = {"plain": "plain content"}
    return body


def test_entry_status_does_not_update_on_put(
    client: TestClient,
    publication_body: dict,
):
    with logged_in_user(ALICE):
        response = client.post(
            "/publications/v1", json=publication_body, headers={"Authorization": "Fake token"}
        )
    assert response.status_code == 200, response.json()

    # Default is DRAFT
    with logged_in_user(ALICE):
        response = client.get("/publications/v1/1", headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert response.json()["aiod_entry"]["status"] == EntryStatus.DRAFT
    identifier = response.json()["identifier"]

    publication_body["aiod_entry"]["status"] = EntryStatus.PUBLISHED
    with logged_in_user(ALICE):
        response = client.put(
            f"/publications/v1/{identifier}",
            json=publication_body,
            headers={"Authorization": "Fake token"},
        )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.json()

    # Status is not updated to published
    with logged_in_user(ALICE):
        response = client.get("/publications/v1/1", headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    assert response.json()["aiod_entry"]["status"] == EntryStatus.DRAFT
