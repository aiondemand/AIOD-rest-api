from http import HTTPStatus

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlmodel import Session

from authentication import KeycloakUser, get_user_or_raise
from database.authorization import Permission, PermissionType
from database.session import get_session
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses
from routers.helper_functions import get_all_asset_schemas


def create(url_prefix: str) -> APIRouter:
    router = APIRouter()
    version = "v1"

    router.get(
        f"{url_prefix}/user/resources/{version}",
        tags=["User"],
        description="Return all assets for which you have administrator rights",
        response_model=None,  # Required! Otherwise FastAPI infers it from type annotation.
        responses={
            HTTPStatus.OK: {
                "content": {
                    "application/json": {
                        "schema": {
                            "title": "List of assets owned by the user.",
                            "type": "array",
                            "items": {"anyOf": get_all_asset_schemas()},
                        }
                    }
                },
            }
        },
    )(get_resources_for_logged_in_user)
    return router


def get_resources_for_logged_in_user(
    user: KeycloakUser = Depends(get_user_or_raise),
    session: Session = Depends(get_session),
) -> list[AIoDConcept]:
    return _get_resources_for_user(user, session)


def _get_resources_for_user(user: KeycloakUser, session: Session) -> list[AIoDConcept]:
    # "Ownership" is currently equivalent to having ADMIN permissions
    stmt = (
        select(AIoDEntryORM)
        .join(Permission.aiod_entry)
        .where(
            Permission.user_identifier == user._subject_identifier,
            Permission.type_ == PermissionType.ADMIN,
        )
    )
    entries = session.scalars(stmt).all()
    assets_to_fetch = [entry.identifier for entry in entries]
    # We have AIoD entries, but want their respective asset information (e.g. publication).
    # We lack the information about what the type of the asset is, so unfortunately we
    # have to check all tables:
    found_assets = []
    for asset_type in non_abstract_subclasses(AIoDConcept):
        query = select(asset_type).where(asset_type.aiod_entry_identifier.in_(assets_to_fetch))
        assets = session.scalars(query).all()
        found_assets.extend(assets)
        if len(found_assets) == len(assets_to_fetch):
            return found_assets  # minor optimization since queries may be expensive

    raise RuntimeError(
        f"Expected to find assets for identifiers {assets_to_fetch}, "
        f"but only found {len(found_assets)} in total: {found_assets}."
    )
