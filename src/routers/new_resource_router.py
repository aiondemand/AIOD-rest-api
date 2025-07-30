from http import HTTPStatus
from http.client import HTTPException
from typing import Callable

from fastapi import APIRouter, Depends
from pydantic import create_model
from pydantic.fields import FieldInfo
from sqlmodel import SQLModel, Session, Field

from authentication import KeycloakUser, get_user_or_none, get_user_or_raise
from database.authorization import user_can_read
from database.model.concept.aiod_entry import EntryStatus
from database.model.resource_read_and_create import resource_read, resource_create
from database.session import get_session
from database.model.serializers import deserialize_resource_relationships
from database.model.case_study.case_study import CaseStudy

# Version?
# Schema Converter?


def create_router(
    orm_model: type[SQLModel],
    resource_name: str,
    resource_name_plural: str,
    read_schema: type[SQLModel] | None = None,
    create_schema: type[SQLModel] | None = None,
    orm_to_read: Callable[[SQLModel], SQLModel] | None = None,
    create_to_orm: Callable[[SQLModel], SQLModel] | None = None,
) -> APIRouter:
    app = APIRouter()

    read_schema = read_schema or resource_read(orm_model)
    create_schema = create_schema or resource_create(orm_model)
    orm_to_read_object = orm_to_read or read_schema.model_validate
    create_object_to_orm = create_to_orm or orm_model.model_validate

    @app.get(
        f"/{resource_name_plural}/{{identifier}}",
        name=resource_name,
        description=f"Retrieve all metadata for the {resource_name} identified by the AIoD identifier.",
    )
    def get_resource(
        identifier: str,
        user: KeycloakUser | None = Depends(get_user_or_none),
        session: Session = Depends(get_session),
    ) -> read_schema:
        # todo: add schema check (why not by pydantic+fastapi?)
        resource = session.get(orm_model, identifier)
        # todo: convert schema
        return orm_to_read_object(resource)
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
        asset: create_schema,
        user: KeycloakUser | None = Depends(get_user_or_raise),
        session: Session = Depends(get_session),
    ):  # -> read_schema:
        resource = create_object_to_orm(asset)
        deserialize_resource_relationships(session, orm_model, resource, asset, user)
        session.add(resource)
        # add logic for ensuring platform resource identifiers and the likes
        session.commit()
        return resource.identifier
        # return orm_to_read_object(resource)

    ...  # other methods

    return app


def schema_transform(
    original: type[SQLModel],
    new_name,
    add_fields: dict[str, tuple[type, FieldInfo]] = None,
    update_fields: dict[str, tuple[type, FieldInfo]] = None,
    remove_fields: list[str] = None,
) -> tuple[type[SQLModel], type[SQLModel]]:
    add_fields = add_fields or {}
    update_fields = update_fields or {}
    remove_fields = remove_fields or []

    create_fields = {
        name: (model_field.annotation, model_field.field_info)
        for name, model_field in resource_create(original).__fields__.items()
    }
    create_fields.update(add_fields | update_fields)
    read_fields = {
        name: (model_field.annotation, model_field.field_info)
        for name, model_field in resource_read(original).__fields__.items()
    }
    read_fields.update(add_fields | update_fields)
    for field in remove_fields:
        del read_fields[field]
        del create_fields[field]

    read_schema = create_model(f"{new_name}Read", __base__=original.__base__, **read_fields)
    create_schema = create_model(f"{new_name}Create", __base__=original.__base__, **create_fields)
    return read_schema, create_schema


CaseStudyV3Read, CaseStudyV3Create = schema_transform(
    CaseStudy,
    "CaseStudyV3",
    add_fields=dict(foo=(str, Field(default="bar", max_length=42))),
)


def create_to_orm(case_study: CaseStudyV3Create) -> CaseStudy:
    """Defines how to go from the new Create schema to the ORM schema"""
    old_style = CaseStudy.model_validate(case_study)
    old_style.name = f"{old_style.name}-{case_study.foo}"
    return old_style


def orm_to_read(case_study: CaseStudy) -> CaseStudyV3Read:
    """Defines how to go from the ORM schema to the new Read schema"""
    old_read = resource_read(CaseStudy).model_validate(case_study)
    new_read = CaseStudyV3Read.model_validate(old_read.model_dump())

    # Add the actual updates, this is just an example
    if "-" in new_read.name:
        new_read.name, new_read.foo = new_read.name.rsplit("-", 1)
    return new_read


AddedFieldRouter = create_router(
    CaseStudy,
    "case_study_added",
    "case_studies_added",
    read_schema=CaseStudyV3Read,
    create_schema=CaseStudyV3Create,
    create_to_orm=create_to_orm,
    orm_to_read=orm_to_read,
)
