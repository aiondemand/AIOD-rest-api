import contextlib
import json
from http import HTTPStatus
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

from authentication import keycloak_openid, KeycloakUser
from database.authorization import (
    register_user,
    add_administrator,
)
from database.model.concept.aiod_entry import EntryStatus
from database.model.concept.concept import AIoDConcept
from database.review import Review, Decision, ReviewCreate, Submission
from database.session import DbSession
from routers.review_router import ListMode

ALICE = KeycloakUser("Alice", {"edit_aiod_resources"}, "alice-sub")
BOB = KeycloakUser("Bob", {"edit_aiod_resources"}, "bob-sub")
REVIEWER = KeycloakUser("Reviewer", {"reviewer", "edit_aiod_resources"}, "reviewer-sub")


def _register_user_in_db(user: KeycloakUser) -> KeycloakUser:
    with DbSession() as session:
        register_user(user, session)
        session.commit()
    return user


@contextlib.contextmanager
def logged_in_user(user: KeycloakUser):
    original = keycloak_openid.introspect
    keycloak_openid.introspect = Mock(
        return_value={
            "realm_access": {"roles": user.roles},
            "resource_access": {
                "account": {"roles": ["manage-account", "manage-account-links", "view-profile"]}
            },
            "scope": "openid profile email",
            "username": user.name,
            "token_type": "Bearer",
            "active": True,
            "sub": user._subject_identifier,
        }
    )
    yield
    keycloak_openid.introspect = original


def test_user_must_be_logged_in_to_publish(client, publication):
    response = client.post("/publications/v1", content=publication.json(), headers=None)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    with logged_in_user(ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()


def test_new_asset_is_draft(client, publication, mocked_privileged_token: Mock):
    with logged_in_user(ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()

        server_data = client.get(f"/publications/v1/{response.json()['identifier']}").json()
        assert server_data["aiod_entry"]["status"] == EntryStatus.DRAFT


def test_drafts_are_private(
    client,
    publication,
    mocked_privileged_token: Mock,
):
    with logged_in_user(ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()

    response = client.get(f"/publications/v1/{response.json()['identifier']}")
    pytest.skip("Privacy rules not yet implemented.")
    # assert response.status_code == HTTPStatus.FORBIDDEN
    # through list
    # through ES
    # with and without authentication


@pytest.mark.parametrize(
    "comment", [None, "foo"]
)
def test_user_can_submit_draft_for_review(comment, client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    content = f'{{"comment": "{comment}"}}' if comment else None

    with logged_in_user(ALICE):
        submission = client.post(
            f"/publications/submit/v1/{identifier}",
            headers={"Authorization": "Fake token"},
            content=content,
        )
        assert submission.status_code == HTTPStatus.OK, submission.json()
        assert "submission_identifier" in submission.json()

    with logged_in_user(REVIEWER):
        queue = client.get("/submissions/v1", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 1, "A successful request should result in a submission."
        [sub] = queue.json()
        assert "requestee_identifier" not in sub, "Submissions should not review who submitted."
        assert sub["comment"] == (comment if comment else ""), "Comment should be stored."


def test_user_can_not_submit_other_for_review(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)

    with logged_in_user(BOB):
        submission = client.post(
            f"/publications/submit/v1/{identifier}",
            headers={"Authorization": "Fake token"},
        )
        assert submission.status_code == HTTPStatus.FORBIDDEN, submission.json()

    with logged_in_user(REVIEWER):
        queue = client.get("/submissions/v1", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 0, "A rejected request should not result in a submission."


def test_a_draft_is_not_pending_for_review(client, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)

    with logged_in_user(REVIEWER):
        queue = client.get("/submissions/v1", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 0, "An asset is only pending for review after submission."


def test_a_submitted_asset_is_pending_for_review(client, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)

    with logged_in_user(REVIEWER):
        queue = client.get("/submissions/v1", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 1, "A submitted asset should be pending until a review is done."

def test_get_submission_by_id(client, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)

    with logged_in_user(REVIEWER):
        submission = client.get("/submissions/v1/1", headers={"Authorization": "Fake token"})
        assert submission.status_code == HTTPStatus.OK, submission.json()

        submission_dict = submission.json()
        submission_date = submission_dict.pop("request_date")
        review_date = submission_dict["reviews"][0].pop("decision_date")
        assert submission_date < review_date
        reviews = submission_dict.pop("reviews")
        asset = submission_dict.pop("asset")
        assert submission_dict == {
            "identifier": 1,
            "aiod_entry_identifier": 1,
            "comment": "",
            "asset_type": "publication",
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
        assert asset == publication_json

def test_get_submission_by_id_must_be_reviewer_or_owner(client, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    _register_user_in_db(REVIEWER)
    _register_user_in_db(BOB)

    for allowed_user in [REVIEWER, ALICE]:
        with logged_in_user(allowed_user):
            submission = client.get("/submissions/v1/1", headers={"Authorization": "Fake token"})
            assert submission.status_code == HTTPStatus.OK, submission.json()

    with logged_in_user(BOB):
        submission = client.get("/submissions/v1/1", headers={"Authorization": "Fake token"})
        # Probably should be changed to Administrators of the asset instead of just submitter.
        assert submission.status_code == HTTPStatus.FORBIDDEN, "Only reviewer and submitter should be able to see the review."


def test_unknown_submission_raises_404(client):
    with logged_in_user(REVIEWER):
        queue = client.get("/submissions/v1/1", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    ("user", "mode", "assets", "reason"),
    [
        (REVIEWER, ListMode.PENDING, [2, 3], "Reviewer can see all pending reviews."),
        (REVIEWER, ListMode.COMPLETED, [1], "Reviewer can see all completed reviews."),
        (ALICE, ListMode.PENDING, [2], "Alice has one pending submission and can not see Bob's."),
        (ALICE, ListMode.COMPLETED, [1], "Alice only has one completed submission."),
        (BOB, ListMode.PENDING, [3], "Bob has one pending submission and can not see Alice's."),
        (BOB, ListMode.COMPLETED, [], "Bob has no completed submission."),
    ]
)
def test_submission_by_state_respects_privacy(user: KeycloakUser, mode: ListMode, assets: list[int], reason: str, client: TestClient, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)
    register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    register_asset(publication, owner=BOB, status=EntryStatus.SUBMITTED)

    with logged_in_user(user):
        queue = client.get(f"/submissions/v1?mode={mode}", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        returned_submissions = [submission["identifier"] for submission in queue.json()]
        assert returned_submissions == assets, f"{reason} Response: {queue.json()}"

def test_an_published_asset_is_not_pending_for_review(client, publication):
    register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)

    with logged_in_user(REVIEWER):
        queue = client.get(
            f"/submissions/v1?mode={ListMode.PENDING}", headers={"Authorization": "Fake token"}
        )
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert (
            len(queue.json()) == 0
        ), "After publication, the submission is no longer pending a review."

        queue = client.get(
            f"/submissions/v1?mode={ListMode.COMPLETED}", headers={"Authorization": "Fake token"}
        )
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 1, "After publication, the review request is completed."


@pytest.mark.parametrize(
    ("user", "mode", "asset", "reason"),
    [
        (REVIEWER, ListMode.OLDEST, 2,"Reviewer can see both Alice and Bob's submission." ),
        (REVIEWER, ListMode.NEWEST, 3, "Reviewer can see both Alice and Bob's submission."),
        (ALICE, ListMode.OLDEST, 2, "Alice only has one pending submission."),
        (ALICE, ListMode.NEWEST, 2,"Alice only has one pending submission."),
        (BOB, ListMode.OLDEST, 3,"Bob only has one pending submission." ),
        (BOB, ListMode.NEWEST, 3,"Bob only has one pending submission."),
    ]
)
def test_retrieving_single_submission_works(user: KeycloakUser, mode: ListMode, asset: int, reason: str, client: TestClient, publication_factory):
    publication = publication_factory()
    oldest = publication_factory()
    oldest.platform_resource_identifier = "OLDEST"
    newest = publication_factory()
    newest.platform_resource_identifier = "NEWEST"

    register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)
    register_asset(oldest, owner=ALICE, status=EntryStatus.SUBMITTED)
    register_asset(newest, owner=BOB, status=EntryStatus.SUBMITTED)

    with logged_in_user(user):
        queue = client.get(f"/submissions/v1?mode={mode}", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert queue.json()[0]["aiod_entry_identifier"] == asset, reason


def test_user_can_retract_assets(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    with logged_in_user(ALICE):
        response = client.post(
            f"/publications/retract/v1/{identifier}", headers={"Authorization": "Fake token"}
        )
        assert "review_identifier" in response.json()
        assert Decision.RETRACTED == response.json()["decision"]

    with logged_in_user(REVIEWER):
        queue = client.get(
            f"/submissions/v1?mode={ListMode.PENDING}", headers={"Authorization": "Fake token"}
        )
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 0, "A retracted request should not remain pending."


def test_other_user_can_not_retract_assets(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)

    with logged_in_user(BOB):
        response = client.post(
            f"/publications/retract/v1/{identifier}", headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()


@pytest.mark.parametrize("status", EntryStatus)
def test_user_can_always_delete_asset(status: EntryStatus, publication, client):
    identifier = register_asset(publication, owner=ALICE, status=status)

    with logged_in_user(ALICE):
        response = client.delete(
            f"/publications/v1/{identifier}",
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()


def register_asset(asset: AIoDConcept, /, *, owner: KeycloakUser, status: EntryStatus):
    with DbSession() as session:
        session.add(asset)
        session.commit()

        register_user(owner, session)
        add_administrator(owner, asset, session)

        asset.aiod_entry.status = status
        if status in [EntryStatus.SUBMITTED, EntryStatus.PUBLISHED, EntryStatus.REJECTED]:
            submission = Submission(
                requestee_identifier=owner._subject_identifier,
                aiod_entry_identifier=asset.aiod_entry.identifier,
                asset_type=asset.__tablename__,
            )
            session.add(submission)
            if status == EntryStatus.PUBLISHED:
                register_user(REVIEWER, session)
                review = Review(
                    decision=Decision.ACCEPTED,
                    reviewer_identifier=REVIEWER._subject_identifier,
                    comment="foo",
                )
                review.submission = submission
                session.add(review)
        session.commit()
        return asset.identifier


def test_user_can_edit_asset_in_draft(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    new_name = "Alice in Wonderland"

    with logged_in_user(ALICE):
        response = client.put(
            f"/publications/v1/{identifier}",
            content=f'{{"name": "{new_name}"}}',
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()
        updated_publication = client.get(f"/publications/v1/{identifier}").json()
        assert updated_publication["name"] == new_name


def test_user_cannot_edit_asset_in_submission(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    new_name = "Alice in Wonderland"

    with logged_in_user(ALICE):
        response = client.put(
            f"/publications/v1/{identifier}",
            content=f'{{"name": "{new_name}"}}',
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()


def test_only_reviewer_can_approve_submission(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    _register_user_in_db(REVIEWER)

    with logged_in_user(ALICE):
        response = client.post(
            "/reviews/v1",
            content=str(
                ReviewCreate(decision=Decision.ACCEPTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()

    with logged_in_user(REVIEWER):
        response = client.post(
            "/reviews/v1",
            content=str(
                ReviewCreate(decision=Decision.ACCEPTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()

    response = client.get(f"/publications/v1/{identifier}")
    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json()["aiod_entry"]["status"] == EntryStatus.PUBLISHED


def test_reviewer_can_reject_submission(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    _register_user_in_db(REVIEWER)

    with logged_in_user(REVIEWER):
        response = client.post(
            "/reviews/v1",
            content=str(
                ReviewCreate(decision=Decision.REJECTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()

    response = client.get(f"/publications/v1/{identifier}")
    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json()["aiod_entry"]["status"] == EntryStatus.DRAFT


def test_reviewer_cannot_approve_own_submission(publication, client):
    register_asset(publication, owner=REVIEWER, status=EntryStatus.SUBMITTED)
    _register_user_in_db(REVIEWER)

    with logged_in_user(REVIEWER):
        response = client.post(
            "/reviews/v1",
            content=str(
                ReviewCreate(decision=Decision.ACCEPTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()
