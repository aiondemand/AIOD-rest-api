import datetime
import re
from typing import List
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from pydantic import create_model
from sqlalchemy import select
from sqlmodel import Session

from dependencies.pagination import PaginationParams
from dependencies.sorting import SortingParams, SortDirection, Sort
from routers.resource_routers import versioned_routers
from authentication import (
    KeycloakUser,
    get_user_or_raise,
    get_user_by_username,
    get_user_by_sub,
    keycloak_api,
)
from database.authorization import Permission, PermissionType
from database.session import get_session
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses
from routers.helper_functions import get_all_read_classes
from versioning import Version
from keycloak import KeycloakGetError, KeycloakError


class RoleAssignmentRequest(BaseModel):
    """Request body for assigning a Keycloak role to a user."""

    user: str = Field(
        description="Username or subject identifier of the target user.",
        examples=["jsmith01", "4a80f256-3928-4cfa-ba66-5e22bb36fc01"],
    )
    role_name: str = Field(
        description="Name of the Keycloak realm role to assign.",
        examples=["review_aiod_resources", "admin_aiod_resources"],
    )


class RoleAssignmentResponse(BaseModel):
    """Response after assigning a role to a user."""

    message: str = Field(description="Confirmation message about the role assignment.")
    user: str = Field(description="Username of the user who received the role.")
    role_name: str = Field(description="Name of the role that was assigned.")


def create(url_prefix: str, version: Version) -> APIRouter:
    router = APIRouter()

    # We define a custom response class here to ensure all the asset
    # types are included, and the (schema) documentation is generated.
    # It also makes sure assets are deserialized the same way as
    # direct access would have.
    suffix = version.prefix.capitalize()
    Catalogue = create_model(
        f"Catalogue{suffix}",
        **{
            asset_type: (List[asset_read_class], Field())  # type: ignore[valid-type]
            for asset_type, asset_read_class in get_all_read_classes(version).items()
        },
    )

    resources_for_user_description = "Return all assets for which you have administrator rights."
    if version == Version.V2:
        resources_for_user_description += (
            " For backwards compatibility reasons, if `limit=10` no limit is applied."
            " In V3 and later, the default limit of 10 is respected."
        )

    @router.get(
        "/user/resources",
        description=resources_for_user_description,
        tags=["User"],
        response_model=Catalogue,
    )
    def get_versioned_resources_for_user(
        pagination: PaginationParams,
        sorting: SortingParams,
        user: KeycloakUser = Depends(get_user_or_raise),  # noqa: B008
        session: Session = Depends(get_session),  # noqa: B008
    ) -> dict[str, list[AIoDConcept]]:
        limit: int | None = pagination.limit
        if limit == 10 and version == Version.V2:
            limit = None

        resources = _get_resources_for_user(
            user,
            session,
            offset=pagination.offset,
            limit=limit,
            sort_by=sorting.sort,
            sort_direction=sorting.direction,
        )
        all_assets = [asset for assets in resources.values() for asset in assets]
        for resource in [a for a in all_assets if hasattr(a, "media")]:
            for media in resource.media:
                media.binary_blob = None

        orm_to_read = {
            r.resource_class.__tablename__: r.orm_to_read
            for r in versioned_routers.get(version, [])
        }

        def sort_function(asset):
            value = getattr(asset.aiod_entry, sorting.sort)
            direction = -1 if sorting.direction == SortDirection.DESC else 1
            return direction * datetime.datetime.timestamp(value)

        return {
            asset_name: sorted(
                (orm_to_read[asset_name](asset) for asset in assets),
                key=sort_function,
            )
            for asset_name, assets in resources.items()
        }

    @router.post(
        "/user/roles",
        tags=["User"],
        description="Assign a Keycloak role to a user. Requires admin permissions.",
        response_model=RoleAssignmentResponse,
    )
    def assign_role(
        request: RoleAssignmentRequest = Body(
            description="The user and role to assign.",
        ),
        current_user: KeycloakUser = Depends(get_user_or_raise),
    ) -> RoleAssignmentResponse:
        """
        Assign a Keycloak realm role to a user.

        This endpoint lets admins assign roles to users via the REST API instead of
        having to use the Keycloak admin console. It checks that the requesting user
        is an admin, validates that both the target user and role exist, and then
        assigns the role in Keycloak.
        """
        if not current_user.is_admin:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="You must be an administrator to assign roles to users.",
            )

        # Figure out if we got a username or a subject identifier (UUID)
        sub_pattern = r"\S{8}(-\S{4}){3}-\S{12}"
        if re.match(sub_pattern, request.user):
            target_user = get_user_by_sub(request.user)
        else:
            target_user = get_user_by_username(request.user)

        if not target_user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"User '{request.user}' not found.",
            )

        kc_admin = keycloak_api()

        # Make sure the role actually exists in Keycloak before trying to assign it
        try:
            role = kc_admin.get_realm_role(request.role_name)
        except KeycloakGetError as e:
            if "not found" in str(e).lower() or e.error_message == "Role not found":
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Role '{request.role_name}' not found in Keycloak.",
                ) from e
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Error checking role existence: {str(e)}",
            ) from e
        except KeycloakError as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Keycloak error: {str(e)}",
            ) from e

        # Check if the role is already assigned - saves us a Keycloak API call
        try:
            user_roles = kc_admin.get_user_realm_roles(
                user_id=target_user._subject_identifier
            )
            existing_role_names = {r.get("name") for r in user_roles if r.get("name")}
            if request.role_name in existing_role_names:
                return RoleAssignmentResponse(
                    message=(
                        f"Role '{request.role_name}' is already assigned to "
                        f"user '{target_user.name}'."
                    ),
                    user=target_user.name,
                    role_name=request.role_name,
                )
        except KeycloakError:
            # If checking existing roles fails, we'll still try to assign
            # Keycloak will handle it if there's a real problem
            pass

        # Actually assign the role
        try:
            kc_admin.assign_user_realm_roles(
                user_id=target_user._subject_identifier,
                roles=[role],
            )
        except KeycloakError as e:
            # Sometimes Keycloak returns an error if the role is already assigned
            error_msg = str(e).lower()
            if "already" in error_msg or "duplicate" in error_msg:
                return RoleAssignmentResponse(
                    message=(
                        f"Role '{request.role_name}' is already assigned to "
                        f"user '{target_user.name}'."
                    ),
                    user=target_user.name,
                    role_name=request.role_name,
                )
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Error assigning role to user: {str(e)}",
            ) from e

        return RoleAssignmentResponse(
            message=(
                f"Role '{request.role_name}' successfully assigned to "
                f"user '{target_user.name}'."
            ),
            user=target_user.name,
            role_name=request.role_name,
        )

    return router


def _get_resources_for_user(
    user: KeycloakUser,
    session: Session,
    *,
    offset: int = 0,
    limit: int | None = None,
    sort_by: Sort = Sort.DATE_MODIFIED,
    sort_direction: SortDirection = SortDirection.DESC,
) -> dict[str, list[AIoDConcept]]:
    # "Ownership" is currently equivalent to having ADMIN permissions
    sort_attribute = getattr(AIoDEntryORM, sort_by.lower())
    sort = sort_attribute.asc() if sort_direction == SortDirection.ASC else sort_attribute.desc()
    stmt = (
        select(AIoDEntryORM)
        .join(Permission.aiod_entry)
        .where(
            Permission.user_identifier == user._subject_identifier,
            Permission.type_ == PermissionType.ADMIN,
        )
        .order_by(sort, AIoDEntryORM.identifier.asc())  # type: ignore[attr-defined]
        .offset(offset)
    )
    if limit:
        stmt = stmt.limit(limit)
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
