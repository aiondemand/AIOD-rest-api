from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from authentication import KeycloakUser, get_user_or_none
from database.session import get_session
from routers.helper_functions import get_asset_type_by_abbreviation
from routers.resource_routers import router_list
from database.model.concept.aiod_entry import EntryStatus
from database.authorization import user_can_read


def create(url_prefix: str = "") -> APIRouter:
    router = APIRouter()

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
        asset_type_map = get_asset_type_by_abbreviation()
        prefix = identifier.split("_")[0]
        model_class = asset_type_map.get(prefix)

        if not model_class:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Unknown asset type with identifier '{identifier}'",
            )

        resource = session.get(model_class, identifier)

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

        for router in router_list:
            if router.resource_class == model_class:
                return router.resource_class_read.from_orm(resource)

        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"No router found to deserialize asset of type '{model_class.__name__}'",
        )

    return router
