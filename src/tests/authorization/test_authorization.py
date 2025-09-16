import json
from http import HTTPStatus
from typing import Callable
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

from authentication import KeycloakUser
from database.authorization import (
    PermissionType, user_can_read, user_can_write, user_can_administer, set_permission,
)
from database.model.concept.aiod_entry import EntryStatus
from database.review import Decision, ReviewCreate
from database.session import DbSession
from database.model.knowledge_asset.publication import Publication
from routers.review_router import ListMode
from tests.testutils.users import ALICE, BOB, REVIEWER, _register_user_in_db, \
    logged_in_user, register_asset
from versioning import Version


def test_user_must_be_logged_in_to_publish(client, publication):
    response = client.post("/publications", content=publication.json(), headers=None)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    with logged_in_user(ALICE):
        response = client.post(
            "/publications", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()


def test_new_asset_is_draft(client, publication, mocked_privileged_token: Mock):
    with logged_in_user(ALICE):
        response = client.post(
            "/publications", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()

        server_data = client.get(
            f"/publications/{response.json()['identifier']}",
            headers={"Authorization": "Fake token"},
        ).json()
        assert server_data["aiod_entry"]["status"] == EntryStatus.DRAFT


def test_drafts_are_private(
    client,
    publication,
    mocked_privileged_token: Mock,
):
    with logged_in_user(ALICE):
        response = client.post(
            "/publications", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()

    response = client.get(f"/publications/{response.json()['identifier']}")
    pytest.skip("Privacy rules not yet implemented.")
    # assert response.status_code == HTTPStatus.FORBIDDEN
    # through list
    # through ES
    # with and without authentication


@pytest.mark.versions(Version.V2)
@pytest.mark.parametrize(
    "comment", [None, "foo"]
)
def test_user_can_submit_draft_for_review_v2(comment, client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    content = f'{{"comment": "{comment}"}}' if comment else None

    with logged_in_user(ALICE):
        submission = client.post(
            f"/publications/submit/{identifier}",
            headers={"Authorization": "Fake token"},
            content=content,
        )
        assert submission.status_code == HTTPStatus.OK, submission.json()
        assert "submission_identifier" in submission.json()

    with logged_in_user(REVIEWER):
        queue = client.get("/submissions", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 1, "A successful request should result in a submission."
        [sub] = queue.json()
        assert "requestee_identifier" not in sub, "Submissions should not review who submitted."
        assert sub["comment"] == (comment if comment else ""), "Comment should be stored."


@pytest.mark.parametrize(
    "comment", [None, "foo"]
)
def test_user_can_submit_draft_for_review(comment, client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    content: dict[str, str | list[str]] = {"asset_identifiers": [identifier]}
    if comment:
        content["comment"] = comment

    with logged_in_user(ALICE):
        submission = client.post(
            f"/submissions",
            headers={"Authorization": "Fake token"},
            json=content,
        )
        assert submission.status_code == HTTPStatus.OK, submission.json()
        assert "submission_identifier" in submission.json()

    with logged_in_user(REVIEWER):
        queue = client.get("/submissions", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 1, "A successful request should result in a submission."
        [sub] = queue.json()
        assert "requestee_identifier" not in sub, "Submissions should not review who submitted."
        assert sub["comment"] == (comment if comment else ""), "Comment should be stored."


def test_user_needs_to_own_all_assets_for_submission(client, publication_factory):
    own = register_asset(publication_factory(), owner=ALICE, status=EntryStatus.DRAFT)
    bobs_publication = publication_factory()
    other = register_asset(bobs_publication, owner=BOB, status=EntryStatus.DRAFT)
    content: dict[str, str | list[str]] = {"asset_identifiers": [own, other]}

    with logged_in_user(ALICE):
        submission = client.post(
            f"/submissions",
            headers={"Authorization": "Fake token"},
            json=content,
        )
        reason = "Request should be rejected because Alice does not own `other`."
        assert submission.status_code == HTTPStatus.FORBIDDEN, reason
        assert "You do not have permission" in submission.json()["detail"]

    with DbSession() as session:
        session.add(bobs_publication)
        set_permission(user=ALICE, resource=bobs_publication.aiod_entry, session=session, type_=PermissionType.ADMIN)
        session.commit()

    with logged_in_user(ALICE):
        submission = client.post(
            f"/submissions",
            headers={"Authorization": "Fake token"},
            json=content,
        )
        reason = "Request should be accepted because Alice does now co-owns `other`."
        assert submission.status_code == HTTPStatus.OK, reason


def test_user_can_not_submit_other_for_review(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)

    with logged_in_user(BOB):
        submission = client.post(
            f"/submissions",
            headers={"Authorization": "Fake token"},
            json={"asset_identifiers": [identifier]},
        )
        assert submission.status_code == HTTPStatus.FORBIDDEN, submission.json()

    with logged_in_user(REVIEWER):
        queue = client.get("/submissions", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 0, "A rejected request should not result in a submission."


def test_a_draft_is_not_pending_for_review(client, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)

    with logged_in_user(REVIEWER):
        queue = client.get("/submissions", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 0, "An asset is only pending for review after submission."


def test_a_submitted_asset_is_pending_for_review(client, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)

    with logged_in_user(REVIEWER):
        queue = client.get("/submissions", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 1, "A submitted asset should be pending until a review is done."

def test_get_submission_by_id(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)

    with logged_in_user(REVIEWER):
        submission = client.get("/submissions/1", headers={"Authorization": "Fake token"})
        assert submission.status_code == HTTPStatus.OK, submission.json()

        submission_dict = submission.json()
        submission_date = submission_dict.pop("request_date")
        review_date = submission_dict["reviews"][0].pop("decision_date")
        assert submission_date < review_date
        reviews = submission_dict.pop("reviews")
        assets = submission_dict.pop("assets")
        assert submission_dict == {
            "identifier": 1,
            "comment": "",
        }
        assert reviews == [
            {
                "identifier": 1,
                "decision": "accepted",
                "comment": "foo",
                "submission_identifier": 1,
            }
        ]
        # Convert to loaded JSON, including e.g., stringification of dates
        publication_json = json.loads(publication.json())
        assert assets == [publication_json]


def test_get_submission_by_id_must_be_reviewer_or_owner(client, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    _register_user_in_db(REVIEWER)
    _register_user_in_db(BOB)

    for allowed_user in [REVIEWER, ALICE]:
        with logged_in_user(allowed_user):
            submission = client.get("/submissions/1", headers={"Authorization": "Fake token"})
            assert submission.status_code == HTTPStatus.OK, submission.json()

    with logged_in_user(BOB):
        submission = client.get("/submissions/1", headers={"Authorization": "Fake token"})
        # Probably should be changed to Administrators of the asset instead of just submitter.
        assert submission.status_code == HTTPStatus.FORBIDDEN, "Only reviewer and submitter should be able to see the review."


def test_unknown_submission_raises_404(client):
    with logged_in_user(REVIEWER):
        queue = client.get("/submissions/1", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    ("user", "mode", "assets", "reason"),
    [
        (REVIEWER, ListMode.PENDING, [2, 3], "Reviewer can see all pending reviews."),
        (REVIEWER, ListMode.COMPLETED, [1], "Reviewer can see all completed reviews."),
        (REVIEWER, ListMode.ALL, [1, 2, 3], "Reviewer can see all reviews."),
        (ALICE, ListMode.PENDING, [2], "Alice has one pending submission and can not see Bob's."),
        (ALICE, ListMode.COMPLETED, [1], "Alice only has one completed submission."),
        (ALICE, ListMode.ALL, [1, 2], "Alice can see all her reviews, but not Bob's."),
        (BOB, ListMode.PENDING, [3], "Bob has one pending submission and can not see Alice's."),
        (BOB, ListMode.COMPLETED, [], "Bob has no completed submission."),
        (BOB, ListMode.ALL, [3], "Bob can see all his reviews, but not Alice's."),
    ]
)
def test_submission_by_state_respects_privacy(user: KeycloakUser, mode: ListMode, assets: list[int], reason: str, client: TestClient, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)
    register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    register_asset(publication, owner=BOB, status=EntryStatus.SUBMITTED)

    with logged_in_user(user):
        queue = client.get(f"/submissions?mode={mode}", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        returned_submissions = [submission["identifier"] for submission in queue.json()]
        assert returned_submissions == assets, f"{reason} Response: {queue.json()}"


def test_an_published_asset_is_not_pending_for_review(client, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)

    with logged_in_user(REVIEWER):
        queue = client.get(
            f"/submissions?mode={ListMode.PENDING}", headers={"Authorization": "Fake token"}
        )
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert (
            len(queue.json()) == 0
        ), "After publication, the submission is no longer pending a review."

        queue = client.get(
            f"/submissions?mode={ListMode.COMPLETED}", headers={"Authorization": "Fake token"}
        )
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 1, "After publication, the review request is completed."


@pytest.mark.parametrize(
    ("user", "mode", "asset", "reason"),
    [
        (REVIEWER, ListMode.OLDEST, 2, "Reviewer can see both Alice and Bob's submission."),
        (REVIEWER, ListMode.NEWEST, 3, "Reviewer can see both Alice and Bob's submission."),
        (ALICE, ListMode.OLDEST, 2, "Alice only has one pending submission."),
        (ALICE, ListMode.NEWEST, 2, "Alice only has one pending submission."),
        (BOB, ListMode.OLDEST, 3, "Bob only has one pending submission."),
        (BOB, ListMode.NEWEST, 3, "Bob only has one pending submission."),
    ]
)
def test_retrieving_single_submission_works(user: KeycloakUser, mode: ListMode, asset: int, reason: str, client: TestClient, publication_factory):
    publication = publication_factory()
    oldest = publication_factory()
    newest = publication_factory()

    register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)
    register_asset(oldest, owner=ALICE, status=EntryStatus.SUBMITTED)
    register_asset(newest, owner=BOB, status=EntryStatus.SUBMITTED)

    with logged_in_user(user):
        queue = client.get(f"/submissions?mode={mode}", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert queue.json()[0]["identifier"] == asset, reason


def test_user_can_retract_assets(client, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    with logged_in_user(ALICE):
        response = client.post(
            f"/submissions/retract/1", headers={"Authorization": "Fake token"}
        )
        assert "review_identifier" in response.json()
        assert Decision.RETRACTED == response.json()["decision"]

    with logged_in_user(REVIEWER):
        queue = client.get(
            f"/submissions?mode={ListMode.PENDING}", headers={"Authorization": "Fake token"}
        )
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 0, "A retracted request should not remain pending."


def test_other_user_can_not_retract_assets(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)

    with logged_in_user(BOB):
        response = client.post(
            f"/submissions/retract/1", headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()


def test_user_needs_only_one_asset_to_retract(client, publication_factory):
    own = register_asset(publication_factory(), owner=ALICE, status=EntryStatus.DRAFT)
    bobs_publication = publication_factory()
    other = register_asset(bobs_publication, owner=BOB, status=EntryStatus.DRAFT)
    with DbSession() as session:
        session.add(bobs_publication)
        set_permission(user=ALICE, resource=bobs_publication.aiod_entry, session=session, type_=PermissionType.ADMIN)
        session.commit()

    content: dict[str, str | list[str]] = {"asset_identifiers": [own, other]}
    with logged_in_user(ALICE):
        submission = client.post(
            f"/submissions",
            headers={"Authorization": "Fake token"},
            json=content,
        )
        assert submission.status_code == HTTPStatus.OK
    submission_identifier = submission.json()["submission_identifier"]

    with logged_in_user(BOB):
        submission = client.post(
            f"/submissions/retract/{submission_identifier}",
            headers={"Authorization": "Fake token"},
            json=content,
        )
        reason = "Since Bob owns one of the two assets, he can retract the submission."
        assert submission.status_code == HTTPStatus.OK, reason


@pytest.mark.parametrize("status", EntryStatus)
def test_user_can_always_delete_asset(status: EntryStatus, publication, client):
    identifier = register_asset(publication, owner=ALICE, status=status)

    with logged_in_user(ALICE):
        response = client.delete(
            f"/publications/{identifier}",
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()


def test_user_can_edit_asset_in_draft(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    new_name = "Alice in Wonderland"

    with logged_in_user(ALICE):
        response = client.put(
            f"/publications/{identifier}",
            content=f'{{"name": "{new_name}"}}',
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()
        updated_publication = client.get(
            f"/publications/{identifier}",
            headers={"Authorization": "Fake token"},
        ).json()
        assert updated_publication["name"] == new_name


def test_user_cannot_edit_asset_in_submission(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    new_name = "Alice in Wonderland"

    with logged_in_user(ALICE):
        response = client.put(
            f"/publications/{identifier}",
            content=f'{{"name": "{new_name}"}}',
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()


def test_only_reviewer_can_approve_submission(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    _register_user_in_db(REVIEWER)

    with logged_in_user(ALICE):
        response = client.post(
            "/reviews",
            content=str(
                ReviewCreate(decision=Decision.ACCEPTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()

    with logged_in_user(REVIEWER):
        response = client.post(
            "/reviews",
            content=str(
                ReviewCreate(decision=Decision.ACCEPTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()

    response = client.get(f"/publications/{identifier}")
    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json()["aiod_entry"]["status"] == EntryStatus.PUBLISHED


def test_reviewer_can_reject_submission(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    _register_user_in_db(REVIEWER)

    with logged_in_user(REVIEWER):
        response = client.post(
            "/reviews",
            content=str(
                ReviewCreate(decision=Decision.REJECTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()

    # Because the rejected asset is back in draft status, it requires authentication to access.
    with logged_in_user(ALICE):
        response = client.get(
            f"/publications/{identifier}",
            headers={"Authorization": "Fake token"},
        )
    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json()["aiod_entry"]["status"] == EntryStatus.DRAFT


@pytest.mark.parametrize(
    "permission", [PermissionType.WRITE, PermissionType.ADMIN]
)
def test_reviewer_cannot_approve_own_submission(
        permission: PermissionType,
        publication_factory: Callable[[], Publication],
        client: TestClient
):
    # Create an asset and add REVIEWER as a collaborator (write/admin)
    _register_user_in_db(REVIEWER)

    publication = publication_factory()
    register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)

    with DbSession() as session:
        session.add(publication)
        set_permission(REVIEWER, publication.aiod_entry, session, type_=permission)
        session.commit()

    # See if the review endpoint correctly rejects collaborators from reviewing the asset
    with logged_in_user(REVIEWER):
        response = client.post(
            "/reviews",
            content=str(
                ReviewCreate(decision=Decision.ACCEPTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()


def test_permission_type_order():
    permissions = {PermissionType.READ, PermissionType.WRITE, PermissionType.ADMIN}
    please_update_msg = "Test needs to be updated when PermissionTypes are added or removed."
    assert set(PermissionType) == permissions, please_update_msg

    assert PermissionType.ADMIN > PermissionType.WRITE
    assert PermissionType.ADMIN > PermissionType.READ
    assert PermissionType.WRITE > PermissionType.READ


@pytest.mark.parametrize(
    "owner", [ALICE, BOB, REVIEWER]
)
def test_user_can_read(owner, publication):
    identifier = register_asset(publication, owner=owner, status=EntryStatus.PUBLISHED)
    # `user_can_*` require object to be in session (or eagerly loaded)
    with DbSession() as session:
        asset = session.get(Publication, identifier)

        users = [ALICE, BOB, REVIEWER]
        assert all(user_can_read(user, asset.aiod_entry) for user in users), "Published assets are public"


@pytest.mark.parametrize(
    "owner", [ALICE, BOB, REVIEWER]
)
def test_user_can_write(owner, publication):
    identifier = register_asset(publication, owner=owner, status=EntryStatus.PUBLISHED)
    with DbSession() as session:
        asset = session.get(Publication, identifier)

        assert user_can_write(owner, asset.aiod_entry)
        others = [u for u in [ALICE, BOB, REVIEWER] if u != owner]
        assert not any(user_can_write(non_owner, asset.aiod_entry) for non_owner in others)


@pytest.mark.parametrize(
    "owner", [ALICE, BOB, REVIEWER]
)
def test_user_can_administer(owner, publication):
    identifier = register_asset(publication, owner=owner, status=EntryStatus.PUBLISHED)
    with DbSession() as session:
        asset = session.get(Publication, identifier)

        assert user_can_administer(owner, asset.aiod_entry)
        others = [u for u in [ALICE, BOB, REVIEWER] if u != owner]
        assert not any(user_can_administer(non_owner, asset.aiod_entry) for non_owner in others)
