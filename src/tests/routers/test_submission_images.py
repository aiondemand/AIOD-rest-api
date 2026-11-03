"""
GET /submissions/{identifier} returns image bytes only on request, like the resource routes.
"""

import io
from http import HTTPStatus

import pytest
from starlette.testclient import TestClient

from database.model.agent.organisation import Organisation
from database.model.concept.aiod_entry import EntryStatus
from dependencies.rate_limiter import _submission_timestamps
from tests.testutils.users import ALICE, REVIEWER, logged_in_user, register_asset


@pytest.fixture(autouse=True)
def _clear_rate_limit_state():
    """These tests submit; the submission rate limit keeps its state across tests."""
    _submission_timestamps.clear()
    yield
    _submission_timestamps.clear()


def _submit_organisation_with_logo(client: TestClient, organisation: Organisation) -> int:
    identifier = register_asset(organisation, owner=ALICE, status=EntryStatus.DRAFT)
    logo = io.BytesIO(b"\x89PNG\r\n\x1a\n...")  # fake PNG bytes
    with logged_in_user(ALICE):
        upload = client.post(
            f"/organisations/{identifier}/image",
            params={"name": "logo"},
            files={"file": ("logo.png", logo, "image/png")},
            headers={"Authorization": "Fake token"},
        )
        submission = client.post(
            "/submissions",
            json={"asset_identifiers": [identifier]},
            headers={"Authorization": "Fake token"},
        )
    assert upload.status_code == HTTPStatus.OK, upload.json()  # noqa: S101
    assert submission.status_code == HTTPStatus.OK, submission.json()  # noqa: S101
    return submission.json()["submission_identifier"]


def _logo_in_submission(client: TestClient, submission: int, query: str = "") -> dict:
    with logged_in_user(REVIEWER):
        response = client.get(
            f"/submissions/{submission}{query}", headers={"Authorization": "Fake token"}
        )
    assert response.status_code == HTTPStatus.OK, response.json()  # noqa: S101
    [asset] = response.json()["assets"]
    [logo] = [media for media in asset["media"] if media["name"] == "logo"]
    return logo


def test_submission_omits_image_bytes_by_default(client: TestClient, organisation: Organisation):
    submission = _submit_organisation_with_logo(client, organisation)

    logo = _logo_in_submission(client, submission)

    assert not logo.get("binary_blob"), "Image bytes should be returned only on request."  # noqa: S101
    assert logo["encoding_format"] == "image/png"  # noqa: S101


def test_submission_returns_image_bytes_on_request(client: TestClient, organisation: Organisation):
    submission = _submit_organisation_with_logo(client, organisation)

    logo = _logo_in_submission(client, submission, "?get_image=true")

    assert logo["binary_blob"], "get_image=true should return the image bytes."  # noqa: S101


def test_submission_without_image_bytes_keeps_them_stored(
    client: TestClient, organisation: Organisation
):
    submission = _submit_organisation_with_logo(client, organisation)

    _logo_in_submission(client, submission)
    logo = _logo_in_submission(client, submission, "?get_image=true")

    assert logo["binary_blob"], "Omitting the bytes must not remove them from the database."  # noqa: S101
