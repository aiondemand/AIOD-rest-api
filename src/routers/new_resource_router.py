from http import HTTPStatus
from http.client import HTTPException
from typing import Callable

from fastapi import APIRouter, Depends
from sqlmodel import SQLModel, Session

from authentication import KeycloakUser, get_user_or_none, get_user_or_raise
from database.authorization import user_can_read
from error_handling.error_handling import as_http_exception
from database.model.concept.aiod_entry import EntryStatus
from database.model.resource_read_and_create import resource_read, resource_create
from database.session import DbSession, get_session
from database.model.serializers import deserialize_resource_relationships


# Version?
# Schema Converter?


def create_router(
    database_model: type[SQLModel],
    resource_name: str,
    resource_name_plural: str,
    orm_to_read_schema: Callable[[type[SQLModel]], type[SQLModel]] = resource_read,
    orm_to_create_schema: Callable[[type[SQLModel]], type[SQLModel]] = resource_create,
    orm_to_read_object: Callable[[SQLModel], SQLModel] | None = None,
    create_object_to_orm: Callable[[SQLModel], SQLModel] | None = None,
) -> APIRouter:
    app = APIRouter()

    view_model = orm_to_read_schema(database_model)
    create_model = orm_to_create_schema(database_model)
    orm_to_read_object = orm_to_read_object or view_model.model_validate
    create_object_to_orm = create_object_to_orm or database_model.model_validate

    @app.get(
        f"/{resource_name_plural}/{{identifier}}",
        name=resource_name,
        description=f"Retrieve all metadata for the {resource_name} identified by the AIoD identifier.",
    )
    def get_resource(
        identifier: str,
        user: KeycloakUser | None = Depends(get_user_or_none),
        session: Session = Depends(get_session),
    ) -> view_model:
        # todo: add schema check (why not by pydantic+fastapi?)
        resource = session.get(database_model, identifier)
        # todo: convert schema
        result = view_model.from_orm(resource)
        return result
        if user is None and resource.aiod_entry.status != EntryStatus.PUBLISHED:
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)
        if user_can_read(user, resource.aiod_entry):
            return result
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)

    @app.post(
        f"/{resource_name_plural}",
        name=resource_name,
        description=f"Register a {resource_name}.",
    )
    def create_resource(
        asset: create_model,
        user: KeycloakUser | None = Depends(get_user_or_raise),
        session: Session = Depends(get_session),
    ) -> view_model:
        resource = create_object_to_orm(asset)
        deserialize_resource_relationships(session, database_model, resource, asset, user)
        session.add(resource)
        # add logic for ensuring platform resource identifiers and the likes
        session.commit()
        return orm_to_read_object(resource)

    ...  # other methods

    return app


# Ideally we just update the methods below:
def _from_database_to_create_object(resource: SQLModel) -> SQLModel: ...


def _from_database_to_create_schema(database_schema: type[SQLModel]) -> type[SQLModel]:
    return resource_read(database_schema)


def _from_database_to_read_object(resource: SQLModel) -> SQLModel:
    return


def _from_database_to_read_schema(database_schema: type[SQLModel]) -> type[SQLModel]:
    return resource_create(database_schema)


def _from_create_to_database_object(resource: SQLModel) -> SQLModel: ...


# AddedFieldRouter = create_router(...)
# RemovedFieldRouter = create_router(...)
# ChangedFieldRouter = create_router(...)
