from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from authentication import KeycloakUser, get_user_or_raise, get_user_or_none
from database.session import get_session
from routers.helper_functions import get_asset_type_by_abbreviation
from routers.resource_routers import router_list

from typing import Type, Union


def create(url_prefix: str = "") -> APIRouter:
    router = APIRouter()
  
    for path in [
        f"{url_prefix}/v2/assets",
        f"{url_prefix}/assets",
    ]:

        @router.get(
            path,
            tags=["Assets"],
            description="Fetch any asset by its identifier.",
        )
        def asset(
            identifier: str,
            session: Session = Depends(get_session),
            user: KeycloakUser = Depends(get_user_or_none),
        ):
            
            asset_type_map = get_asset_type_by_abbreviation()
            prefix = identifier.split("_")[0]
            model_class = asset_type_map.get(prefix)

            if not model_class:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Unknown asset type '{prefix}'"
                )

            resource = session.exec(
                select(model_class).where(model_class.identifier == identifier)
            ).first()

            if not resource or getattr(resource, "date_deleted", None) is not None:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"No active asset found for identifier '{identifier}'"
                )

            for router in router_list:
                if router.resource_class == model_class:
                    return router.resource_class_read.from_orm(resource)

            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"No router found to deserialize asset with prefix '{prefix}'"
            )

    return router 

            
        
