"""
DELETE of a submitted asset names the pending submission of the asset in its error message.
"""

import re
from http import HTTPStatus

import pytest
from httpx import Response
from starlette.testclient import TestClient

from database.model.concept.aiod_entry import EntryStatus
from database.model.knowledge_asset.publication import Publication
from dependencies.rate_limiter import _submission_timestamps
from tests.testutils.users import ALICE, logged_in_user, register_asset

HEADERS = {"Authorization": "Fake token"}


@pytest.fixture(autouse=True)
def _clear_rate_limit_state():
    """These tests submit; the submission rate limit keeps its state across tests."""
    _submission_timestamps.clear()
    yield
    _submission_timestamps.clear()


def _submit(client: TestClient, identifier: str) -> int:
    with logged_in_user(ALICE):
        response = client.post(
            "/submissions", json={"asset_identifiers": [identifier]}, headers=HEADERS
        )
    assert response.status_code == HTTPStatus.OK, response.json()  # noqa: S101
    return response.json()["submission_identifier"]


def _retract(client: TestClient, submission: int) -> Response:
    with logged_in_user(ALICE):
        return client.post(f"/submissions/retract/{submission}", headers=HEADERS)


def _delete(client: TestClient, identifier: str) -> Response:
    with logged_in_user(ALICE):
        return client.delete(f"/publications/{identifier}", headers=HEADERS)


def test_delete_names_the_only_submission(client: TestClient, publication: Publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    submission = _submit(client, identifier)

    response = _delete(client, identifier)

    assert response.status_code == HTTPStatus.FORBIDDEN, response.json()  # noqa: S101
    assert f"(submission_id: {submission})" in response.json()["detail"]  # noqa: S101


def test_delete_names_the_pending_submission(client: TestClient, publication: Publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    retracted = _submit(client, identifier)
    retraction = _retract(client, retracted)
    assert retraction.status_code == HTTPStatus.OK, retraction.json()  # noqa: S101
    pending = _submit(client, identifier)

    response = _delete(client, identifier)

    assert response.status_code == HTTPStatus.FORBIDDEN, response.json()  # noqa: S101
    detail = response.json()["detail"]
    message = "The message must give the pending submission."
    assert f"(submission_id: {pending})" in detail, message  # noqa: S101
    old = _retract(client, retracted)
    assert old.status_code == HTTPStatus.BAD_REQUEST, "The old one cannot be retracted."  # noqa: S101


def test_delete_works_after_the_named_submission_is_retracted(
    client: TestClient, publication: Publication
):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    first = _retract(client, _submit(client, identifier))
    assert first.status_code == HTTPStatus.OK, first.json()  # noqa: S101
    _submit(client, identifier)
    refusal = _delete(client, identifier)
    named = re.search(r"submission_id: (\d+)", refusal.json()["detail"])
    assert named, refusal.json()  # noqa: S101

    retraction = _retract(client, int(named.group(1)))
    response = _delete(client, identifier)

    assert retraction.status_code == HTTPStatus.OK, retraction.json()  # noqa: S101
    assert response.status_code == HTTPStatus.OK, response.json()  # noqa: S101
