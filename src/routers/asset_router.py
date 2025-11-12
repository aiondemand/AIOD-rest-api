import re
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
import logging

from authentication import (
    KeycloakUser,
    get_user_or_none,
    get_user_or_raise,
    get_user_by_username,
    get_user_by_sub,
)
from database.authorization import user_can_administer, set_permission, Permission, register_user
from database.session import get_session
from database.model.helper_functions import get_asset_by_identifier
from routers.resource_routers import versioned_routers
from database.model.concept.aiod_entry import EntryStatus
from database.authorization import user_can_read, PermissionType
from versioning import Version

logger = logging.getLogger(__file__)


def create(url_prefix: str = "", version: Version = Version.LATEST) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/assets/permissions",
        tags=["Assets"],
        description="Manage permissions that a user has for an asset.",
    )
    def add_or_update_permission(
        asset_identifier: str = Body(
            description="The identifier of the asset for which to update the permission."
        ),
        user: str = Body(
            description="The username or subject identifier of the user.",
            examples=["jsmith01", "4a80f256-3928-4cfa-ba66-5e22bb36fc01"],
        ),
        permission_type: PermissionType | None = Body(
            description="The permission to add for the user. "
            "If not set, their permissions will be removed.",
            default=None,
        ),
        session: Session = Depends(get_session),
        current_user: KeycloakUser = Depends(get_user_or_raise),
    ):
        _, resource = get_asset_by_identifier(asset_identifier, session)
        if not user_can_administer(current_user, resource.aiod_entry):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"You are not allowed to update permissions for asset {asset_identifier}.",
            )
        sub_pattern = r"\S{8}(-\S{4}){3}-\S{12}"
        if re.match(sub_pattern, user):
            other = KeycloakUser(name="unknown", roles=set(), _subject_identifier=user)
        else:
            other = get_user_by_username(user)  # type: ignore[assignment]
        if not other:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"User with name {user!r} not found.",
            )

        register_user(other, session)  # Should be replaced by KC pushing to REST API
        if other._subject_identifier == current_user._subject_identifier:
            # This request is more likely to be an accident than on purpose.
            # Additionally, we do not want to allow people to accidentally remove all
            # administrators from an asset which this restriction ensures.
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="You cannot change permissions that pertain to yourself.",
            )
        if permission_type:
            set_permission(other, resource.aiod_entry, session, type_=permission_type)
            session.commit()
        else:
            key = {
                "user_identifier": other._subject_identifier,
                "aiod_entry_identifier": resource.aiod_entry.identifier,
            }
            permission = session.get(Permission, key)
            if permission:
                session.delete(permission)
                session.commit()

    @router.get(
        "/assets/permissions/{identifier}",
        tags=["Assets"],
        description="Show the permissions for this asset. Requires admin rights of the asset.",
    )
    def show_permission(
        identifier: str,
        session: Session = Depends(get_session),
        current_user: KeycloakUser = Depends(get_user_or_raise),
    ):
        _, resource = get_asset_by_identifier(identifier, session)
        if not user_can_administer(current_user, resource.aiod_entry):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"You are not allowed to see permissions for asset {identifier}.",
            )

        permissions = select(Permission).where(
            Permission.aiod_entry_identifier == resource.aiod_entry.identifier
        )
        users = []
        for permission in session.scalars(permissions).all():
            if (user := get_user_by_sub(permission.user_identifier)) is not None:
                users.append({"name": user.name, "permission": permission.type_})
            else:
                logger.warning(f"Could not find user for sub {permission.user_identifier}.")
        return users

    @router.get(
        f"/assets/{{identifier}}",
        tags=["Assets"],
        description="Fetch any asset by its identifier.",
    )
    def asset(
        identifier: str,
        session: Session = Depends(get_session),
        user: KeycloakUser = Depends(get_user_or_none),
    ):
        """
        Get the resource identified by AIoD identifier, return in aiod schema.
        """
        model_class, resource = get_asset_by_identifier(identifier, session)

        if not resource or resource.date_deleted is not None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"No active asset found for identifier '{identifier}'",
            )

        if resource.aiod_entry.status != EntryStatus.PUBLISHED:
            if user is None:
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED,
                    detail="This asset is not published. It requires authentication to access.",
                )
            if not user_can_read(user, resource.aiod_entry):
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail="You are not allowed to view this resource.",
                )

        for router in versioned_routers.get(version, []):
            if router.resource_class == model_class:
                return router.orm_to_read(resource)

        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"No router found to deserialize asset of type '{model_class.__name__}'",
        )

    return router
