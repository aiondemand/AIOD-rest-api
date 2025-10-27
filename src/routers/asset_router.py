from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session

from authentication import KeycloakUser, get_user_or_none, get_user_or_raise, get_user_by_username
from database.authorization import user_can_administer, set_permission, Permission, register_user
from database.session import get_session
from routers.helper_functions import get_asset_type_by_abbreviation
from routers.resource_routers import versioned_routers
from database.model.concept.aiod_entry import EntryStatus
from database.authorization import user_can_read, PermissionType
from versioning import Version


def create(url_prefix: str = "", version: Version = Version.LATEST) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/assets/permissions",
        tags=["Assets"],
        description="Add or update permissions that a user has for an asset.",
    )
    def add_or_update_permission(
        asset_identifier: str = Body(
            description="The identifier of the asset for which to update the permission."
        ),
        username: str = Body(
            description="The username of the user for which to update the permission."
        ),
        permission_type: PermissionType = Body(),
        session: Session = Depends(get_session),
        user: KeycloakUser = Depends(get_user_or_raise),
    ):
        _, resource = get_asset_by_identifier(asset_identifier, session)
        if not user_can_administer(user, resource.aiod_entry):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"You are not allowed to grant permissions for asset {asset_identifier}.",
            )
        other = get_user_by_username(username)
        if not other:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"User with name {username!r} not found."
            )
        register_user(other, session)  # Should be replaced by KC pushing to REST API
        if other._subject_identifier == user._subject_identifier:
            # This request is more likely to be an accident that purpose.
            # Additionally, we do not want to allow people to accidentally remove all
            # administrators from an asset which this restriction ensures.
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="You cannot change permissions that pertain to yourself.",
            )
        set_permission(other, resource.aiod_entry, session, type_=permission_type)
        session.commit()

    @router.delete(
        "/assets/permissions",
        tags=["Assets"],
        description="Remove permissions that a user has for an asset.",
    )
    def delete_permission(
        asset_identifier: str = Body(
            description="The identifier of the asset for which to remove the permission."
        ),
        username: str = Body(
            description="The username of the user for which to remove the permission."
        ),
        session: Session = Depends(get_session),
        user: KeycloakUser = Depends(get_user_or_raise),
    ):
        _, resource = get_asset_by_identifier(asset_identifier, session)
        if not user_can_administer(user, resource.aiod_entry):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"You are not allowed to remove permissions for asset {asset_identifier}.",
            )
        other = get_user_by_username(username)
        if not other:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"User with name {username!r} not found."
            )
        if other._subject_identifier == user._subject_identifier:
            # This request is more likely to be an accident that purpose.
            # Additionally, we do not want to allow people to accidentally remove all
            # administrators from an asset which this restriction ensures.
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="You cannot remove permissions that pertain to yourself.",
            )

        key = {
            "user_identifier": other._subject_identifier,
            "aiod_entry_identifier": resource.aiod_entry.identifier,
        }
        permission = session.get(Permission, key)
        if permission:
            session.delete(permission)
            session.commit()

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

    def get_asset_by_identifier(identifier, session):
        asset_type_map = get_asset_type_by_abbreviation()
        prefix = identifier.split("_")[0]
        model_class = asset_type_map.get(prefix)
        if not model_class:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Unknown asset type with identifier '{identifier}'",
            )
        resource = session.get(model_class, identifier)
        return model_class, resource

    return router
