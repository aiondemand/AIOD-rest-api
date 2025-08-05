from typing import List

from fastapi import APIRouter, Depends
from pydantic import create_model, Field
from sqlalchemy import select
from sqlmodel import Session

from routers.resource_routers import versioned_routers
from authentication import KeycloakUser, get_user_or_raise
from database.authorization import Permission, PermissionType
from database.session import get_session
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses
from routers.helper_functions import get_all_read_classes
from versioning import Version


def create(url_prefix: str, version: Version) -> APIRouter:
    router = APIRouter()

    # We define a custom response class here to ensure all the asset
    # types are included, and the (schema) documentation is generated.
    # It also makes sure assets are deserialized the same way as
    # direct access would have.
    suffix = "" if version == Version.LATEST else version.capitalize()
    Catalogue = create_model(
        f"Catalogue{suffix}",
        **{
            asset_type: (List[asset_read_class], Field())  # type: ignore[valid-type]
            for asset_type, asset_read_class in get_all_read_classes(version).items()
        },
    )

    @router.get(
        f"/user/resources",
        tags=["User"],
        description="Return all assets for which you have administrator rights",
        response_model=Catalogue,
    )
    def get_versioned_resources_for_user(
        user: KeycloakUser = Depends(get_user_or_raise),
        session: Session = Depends(get_session),
    ) -> dict[str, list[AIoDConcept]]:
        resources = _get_resources_for_user(user, session)
        orm_to_read = {
            r.resource_class.__tablename__: r.orm_to_read
            for r in versioned_routers.get(version, [])
        }
        return {
            asset_name: [orm_to_read[asset_name](asset) for asset in assets]
            for asset_name, assets in resources.items()
        }

    return router


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
