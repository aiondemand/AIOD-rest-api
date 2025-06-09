from http import HTTPStatus
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import create_model, Field
from sqlalchemy import select
from sqlmodel import Session

from authentication import KeycloakUser, get_user_or_raise
from database.authorization import (
    Permission,
    PermissionType,
    user_can_administer,
    User,
    set_permission,
)
from database.session import get_session
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses
from routers.helper_functions import get_all_read_classes


def create(url_prefix: str) -> APIRouter:
    router = APIRouter()
    version = "v1"

    # We define a custom response class here to ensure all the asset
    # types are included, and the (schema) documentation is generated.
    # It also makes sure assets are deserialized the same way as
    # direct access would have.
    Catalogue = create_model(
        "Catalogue",
        **{
            asset_type: (List[asset_read_class], Field())  # type: ignore[valid-type]
            for asset_type, asset_read_class in get_all_read_classes().items()
        },
    )
    for path in [
        f"{url_prefix}/user/resources/{version}",
        f"{url_prefix}/v2/user/resources",
        f"{url_prefix}/user/resources",
    ]:
        router.get(
            path,
            tags=["User"],
            description="Return all assets for which you have administrator rights",
            response_model=Catalogue,
        )(get_resources_for_logged_in_user)

    for path in [
        f"{url_prefix}/v2/resources/permission",
        f"{url_prefix}/resources/permission",
    ]:
        router.post(
            path,
            tags=["User"],
            description="Give a user read, write, or administrator permission for an asset you have administrator rights to.",  # noqa: E501
        )(set_permission_endpoint)
    return router


def set_permission_endpoint(
    resource_identifier: Annotated[int, Body(description="The identifier for the asset.")],
    user_identifier: Annotated[str, Body(description="The identifier for the user.")],
    permission: Annotated[
        PermissionType, Body(description="The permission the user should have for the asset.")
    ],
    user: KeycloakUser = Depends(get_user_or_raise),
    session: Session = Depends(get_session),
) -> None:
    """Give a user some permission for an asset."""
    if (resource := session.get(AIoDEntryORM, resource_identifier)) is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Resource with identifier {resource_identifier} not found.",
        )
    if not user_can_administer(user, resource):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail=f"You do not have administrator rights for asset {resource_identifier}.",
        )
    if user._subject_identifier == user_identifier:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="You may not modify your own permissions, please ask a different administrator.",
        )
    if (other_user := session.get(User, user_identifier)) is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"User with identifier {user_identifier} not found.",
        )
    set_permission(other_user, resource, session, type_=permission)
    session.commit()


def get_resources_for_logged_in_user(
    user: KeycloakUser = Depends(get_user_or_raise),
    session: Session = Depends(get_session),
) -> dict[str, list[AIoDConcept]]:
    return _get_resources_for_user(user, session)


def _get_resources_for_user(user: KeycloakUser, session: Session) -> dict[str, list[AIoDConcept]]:
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
    asset_types = list(non_abstract_subclasses(AIoDConcept))
    found_assets: dict[str, list[AIoDConcept]] = {type_.__tablename__: [] for type_ in asset_types}
    for asset_type in asset_types:
        query = (
            select(asset_type)
            .where(asset_type.aiod_entry_identifier.in_(assets_to_fetch))
            .where(asset_type.date_deleted.is_(None))
        )
        assets = session.scalars(query).all()
        found_assets[asset_type.__tablename__] = list(assets)
        if sum(map(len, found_assets.values())) == len(assets_to_fetch):
            break
    return found_assets  # minor optimization since queries may be expensive
