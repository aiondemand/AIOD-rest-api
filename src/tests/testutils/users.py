import contextlib
from typing import cast
from unittest.mock import Mock

from sqlalchemy import update
from sqlalchemy.orm.exc import DetachedInstanceError

from authentication import KeycloakUser, keycloak_openid, REVIEWER_ROLE
from database.authorization import register_user, set_permission, PermissionType
from database.model.concept.aiod_entry import EntryStatus, AIoDEntryORM
from database.model.concept.concept import AIoDConcept
from database.review import Submission, Review, Decision
from database.session import DbSession
from database.review import AssetReview

ALICE = KeycloakUser("Alice", set(), "alice000-0000-0000-0000-000000000000")
BOB = KeycloakUser("Bob", set(), "bob00000-0000-0000-0000-000000000000")
REVIEWER = KeycloakUser("Reviewer", {cast(str, REVIEWER_ROLE)}, "reviewer-0000-0000-0000-000000000000")
CONNECTOR_ROLE = "platform_example"


def _register_user_in_db(user: KeycloakUser) -> KeycloakUser:
    with DbSession() as session:
        register_user(user, session)
        session.commit()
    return user

def kc_connector_with_roles(*roles: str) -> KeycloakUser:
    """ Generates a connector user. """
    return KeycloakUser(
        name="Connector",
        roles={CONNECTOR_ROLE, *roles}, # type: ignore[arg-type]
        _subject_identifier="connector-sub",
    )

def kc_user_with_roles(*roles: str) -> KeycloakUser:
    """ Generates a user with name 'Dummy' and identifier 'Foo' and the provided roles. """
    return KeycloakUser(
        name="Dummy",
        roles=set(roles),
        _subject_identifier="Foo",
    )

@contextlib.contextmanager
def logged_in_user(user: KeycloakUser | None = None):
    """Act as if the specified user is logged in. If no user is specified, a new user will be generated. """
    original = keycloak_openid.introspect
    user = user or kc_user_with_roles()
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


def register_asset(asset: AIoDConcept, /, *, owner: KeycloakUser | None = None, status: EntryStatus = EntryStatus.PUBLISHED):
    owner = owner or kc_user_with_roles()

    try:
        if not asset.aiod_entry:
            asset.aiod_entry = AIoDEntryORM()
    except DetachedInstanceError:
        pass  # if the asset came from a database connection, it already has an entry

    with DbSession() as session:
        session.add(asset)
        session.commit()

        register_user(owner, session)
        set_permission(owner, asset.aiod_entry, session, type_=PermissionType.ADMIN)

        asset.aiod_entry.status = status
        if status in [EntryStatus.SUBMITTED, EntryStatus.PUBLISHED, EntryStatus.REJECTED]:
            submission = Submission(requestee_identifier=owner._subject_identifier)
            submission._assets.append(
                AssetReview(asset_identifier=asset.identifier, aiod_entry_identifier=asset.aiod_entry.identifier)
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

def bypass_reviewer_publish_everything() -> None:
    """Function to set the AIoD entry to published without a review.
    This function is a *test utility* to simplify test setups, and avoid
    e.g., authentication for get requests.
    """
    with DbSession() as session:
        session.exec(update(AIoDEntryORM).values(status=EntryStatus.PUBLISHED))
        session.commit()
