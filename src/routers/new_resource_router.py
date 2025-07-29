from http import HTTPStatus
from http.client import HTTPException

from fastapi import APIRouter, Depends
from sqlmodel import SQLModel, Session

from authentication import KeycloakUser, get_user_or_none
from database.authorization import user_can_read
from error_handling.error_handling import as_http_exception
from database.model.concept.aiod_entry import EntryStatus
from database.model.resource_read_and_create import resource_read, resource_create
from database.session import DbSession, get_session


# Version?
# Schema Converter?


def create_router(
    database_model: type[SQLModel],
    resource_name: str,
    resource_name_plural: str,
) -> APIRouter:
    app = APIRouter()

    view_model = _from_database_to_read_schema(database_model)
    # create_model = _database_model_to_create_view(database_model)

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
        if user is None and resource.aiod_entry.status != EntryStatus.PUBLISHED:
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)
        if user_can_read(user, resource.aiod_entry):
            return result
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)

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
