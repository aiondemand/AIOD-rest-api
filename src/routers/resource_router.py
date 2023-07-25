import abc
import datetime
import traceback
from typing import Literal, Union, Any
from typing import TypeVar, Type
from wsgiref.handlers import format_date_time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import and_, delete
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, Session, select
from starlette.responses import JSONResponse

from authentication import get_current_user
from config import KEYCLOAK_CONFIG
from converters.schema_converters.schema_converter import SchemaConverter
from database.model.agent import Agent
from database.model.agent_table import AgentTable
from database.model.ai_asset_old import AIAssetOld
from database.model.ai_asset_table_old import AIAssetOldTable
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.model.resource import (
    Resource,
    resource_create,
    resource_read,
)
from serialization import deserialize_resource_relationships


class Pagination(BaseModel):
    offset: int = 0
    limit: int = 100


RESOURCE = TypeVar("RESOURCE", bound=Resource)
RESOURCE_CREATE = TypeVar("RESOURCE_CREATE", bound=SQLModel)
RESOURCE_READ = TypeVar("RESOURCE_READ", bound=SQLModel)


class ResourceRouter(abc.ABC):
    """
    Abstract class for FastAPI resource router.

    It creates the basic endpoints for each resource:
    - GET /[resource]s/
    - GET /[resource]s/{identifier}
    - GET /platforms/{platform_name}/[resource]s/
    - GET /platforms/{platform_name}/[resource]s/{identifier}
    - POST /[resource]s
    - PUT /[resource]s/{identifier}
    - DELETE /[resource]s/{identifier}
    """

    def __init__(self):
        self.resource_class_create = resource_create(self.resource_class)
        self.resource_class_read = resource_read(self.resource_class)

    @property
    @abc.abstractmethod
    def version(self) -> int:
        """
        The API version.

        When introducing a breaking change, the current version should be deprecated, any previous
        versions removed, and a new version should be created. The breaking changes should only
        be implemented in the new version.
        """

    @property
    def deprecated_from(self) -> datetime.date | None:
        """
        The deprecation date. This should be the date of the release in which the resource has
        been deprecated.
        """
        return None

    @property
    @abc.abstractmethod
    def resource_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def resource_name_plural(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def resource_class(self):
        pass

    @property
    def schema_converters(self) -> dict[str, SchemaConverter[RESOURCE, Any]]:
        """
        If a resource can be served in different formats, the resource converter should return
        a dictionary of schema converters.

        Returns:
            a dictionary containing as key the name of a schema, and as value the schema
            converter. The key "aiod" should not be in this dictionary, as it is the default
            value and should result in just returning the AIOD_CLASS without conversion.
        """
        return {}

    def create(self, engine: Engine, url_prefix: str) -> APIRouter:
        router = APIRouter()
        version = f"v{self.version}"
        default_kwargs = {
            "response_model_exclude_none": True,
            "deprecated": self.deprecated_from is not None,
            "tags": [self.resource_name_plural],
        }
        available_schemas: list[Type] = [c.to_class for c in self.schema_converters.values()]
        response_model = Union[self.resource_class_read, *available_schemas]  # type:ignore
        response_model_plural = Union[  # type:ignore
            list[self.resource_class_read], *[list[s] for s in available_schemas]  # type:ignore
        ]

        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}",
            endpoint=self.get_resources_func(engine),
            response_model=response_model_plural,  # type: ignore
            name=f"List {self.resource_name_plural}",
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/counts/{self.resource_name_plural}/v0",
            endpoint=self.get_resource_count_func(engine),
            response_model=int,  # type: ignore
            name=f"Count of {self.resource_name_plural}",
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}",
            methods={"POST"},
            endpoint=self.register_resource_func(engine),
            name=self.resource_name,
            **default_kwargs,
        )
        router.add_api_route(
            path=url_prefix + f"/{self.resource_name_plural}/{version}/{{identifier}}",
            endpoint=self.get_resource_func(engine),
            response_model=response_model,  # type: ignore
            name=self.resource_name,
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}/{{identifier}}",
            methods={"PUT"},
            endpoint=self.put_resource_func(engine),
            name=self.resource_name,
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}/{{identifier}}",
            methods={"DELETE"},
            endpoint=self.delete_resource_func(engine),
            name=self.resource_name,
            **default_kwargs,
        )
        if issubclass(self.resource_class, Resource):
            router.add_api_route(
                path=f"{url_prefix}/platforms/{{platform}}/{self.resource_name_plural}/{version}",
                endpoint=self.get_platform_resources_func(engine),
                response_model=response_model_plural,  # type: ignore
                name=f"List {self.resource_name_plural}",
                **default_kwargs,
            )
            router.add_api_route(
                path=f"{url_prefix}/platforms/{{platform}}/{self.resource_name_plural}/{version}"
                f"/{{identifier}}",
                endpoint=self.get_platform_resource_func(engine),
                response_model=response_model,  # type: ignore
                name=self.resource_name,
                **default_kwargs,
            )
        return router

    def get_resources(
        self, engine: Engine, schema: str, pagination: Pagination, platform: str | None = None
    ):
        """Fetch all resources of this platform in given schema, using pagination"""
        _raise_error_on_invalid_schema(self._possible_schemas, schema)
        convert_schema = (
            self.schema_converters[schema].convert
            if schema != "aiod"
            else self.resource_class_read.from_orm
        )
        try:
            with Session(engine) as session:
                where_clause = (
                    (self.resource_class.platform == platform) if platform is not None else True
                )
                query = (
                    select(self.resource_class)
                    .where(where_clause)
                    .offset(pagination.offset)
                    .limit(pagination.limit)
                )

                return self._wrap_with_headers(
                    [convert_schema(resource) for resource in session.scalars(query).all()]
                )
        except Exception as e:
            raise _wrap_as_http_exception(e)

    def get_resource(
        self, engine: Engine, identifier: str, schema: str, platform: str | None = None
    ):
        """
        Get the resource identified by AIoD identifier (if platform is None) or by platform AND
        platform-identifier (if platform is not None), return in given schema.
        """
        _raise_error_on_invalid_schema(self._possible_schemas, schema)
        try:
            with Session(engine) as session:
                resource = self._retrieve_resource(session, identifier, platform=platform)
                if schema != "aiod":
                    return self.schema_converters[schema].convert(resource)
                return self._wrap_with_headers(self.resource_class_read.from_orm(resource))
        except Exception as e:
            raise _wrap_as_http_exception(e)

    def get_resources_func(self, engine: Engine):
        """
        Return a function that can be used to retrieve a list of resources.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resources(
            pagination: Pagination = Depends(Pagination),
            schema: Literal[tuple(self._possible_schemas)] = "aiod",  # type:ignore
        ):
            f"""Retrieve all meta-data of the {self.resource_name_plural}."""
            resources = self.get_resources(
                engine=engine, pagination=pagination, schema=schema, platform=None
            )
            return resources

        return get_resources

    def get_resource_count_func(self, engine: Engine):
        """
        Gets the total number of resources from the database.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resource_count():
            f"""Retrieve the number of {self.resource_name_plural}."""
            try:
                with Session(engine) as session:
                    return session.query(self.resource_class).count()
            except Exception as e:
                raise _wrap_as_http_exception(e)

        return get_resource_count

    def get_platform_resources_func(self, engine: Engine):
        """
        Return a function that can be used to retrieve a list of resources for a platform.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resources(
            platform: str,
            pagination: Pagination = Depends(Pagination),
            schema: Literal[tuple(self._possible_schemas)] = "aiod",  # type:ignore
        ):
            f"""Retrieve all meta-data of the {self.resource_name_plural} of given platform."""
            resources = self.get_resources(
                engine=engine, pagination=pagination, schema=schema, platform=platform
            )
            return resources

        return get_resources

    def get_resource_func(self, engine: Engine):
        """
        Return a function that can be used to retrieve a single resource.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resource(
            identifier: str, schema: Literal[tuple(self._possible_schemas)] = "aiod"  # type:ignore
        ):
            f"""
            Retrieve all meta-data for a {self.resource_name} identified by the AIoD identifier.
            """
            resource = self.get_resource(
                engine=engine, identifier=identifier, schema=schema, platform=None
            )
            return self._wrap_with_headers(resource)

        return get_resource

    def get_platform_resource_func(self, engine: Engine):
        """
        Return a function that can be used to retrieve a single resource of a platform.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resource(
            identifier: str,
            platform: str,
            schema: Literal[tuple(self._possible_schemas)] = "aiod",  # type:ignore
        ):
            f"""Retrieve all meta-data for a {self.resource_name} identified by the
            platform-specific-identifier."""
            return self.get_resource(
                engine=engine, identifier=identifier, schema=schema, platform=platform
            )

        return get_resource

    def register_resource_func(self, engine: Engine):
        """
        Return a function that can be used to register a resource.
        This function returns a function (instead of being that function directly) because the
        docstring is dynamic and used in Swagger.
        """
        clz_create = self.resource_class_create

        def register_resource(
            resource_create: clz_create,  # type: ignore
            user: dict = Depends(get_current_user),
        ):
            f"""Register a {self.resource_name} with AIoD."""
            if "groups" in user and KEYCLOAK_CONFIG.get("role") not in user["groups"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to edit Aiod resources.",
                )
            try:
                with Session(engine) as session:
                    try:
                        resource = self.create_resource(session, resource_create)
                        return self._wrap_with_headers({"identifier": resource.identifier})
                    except Exception as e:
                        self._raise_clean_http_exception(e, session, resource_create)
            except Exception as e:
                raise _wrap_as_http_exception(e)

        return register_resource

    def create_resource(self, session: Session, resource_create_instance: SQLModel):
        # Store a resource in the database
        parent = None
        if issubclass(self.resource_class, AIAssetOld):
            # example - datasets, publications, etc.
            parent = AIAssetOldTable(type=self.resource_class.__tablename__)
        elif issubclass(self.resource_class, Agent):
            # example - organisations
            parent = AgentTable(type=self.resource_class.__tablename__)
        if parent:
            session.add(parent)
            session.flush()
            resource = self.resource_class.from_orm(
                resource_create_instance, update={"identifier": parent.identifier}
            )
        else:
            resource = self.resource_class.from_orm(resource_create_instance)

        deserialize_resource_relationships(
            session, self.resource_class, resource, resource_create_instance
        )
        session.add(resource)
        session.commit()
        return resource

    def put_resource_func(self, engine: Engine):
        """
        Return a function that can be used to update a resource.
        This function returns a function (instead of being that function directly) because the
        docstring is dynamic and used in Swagger.
        """
        clz_create = self.resource_class_create

        def put_resource(
            identifier: int,
            resource_create_instance: clz_create,  # type: ignore
            user: dict = Depends(get_current_user),
        ):
            f"""Update an existing {self.resource_name}."""
            if "groups" in user and KEYCLOAK_CONFIG.get("role") not in user["groups"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to edit Aiod resources.",
                )

            try:
                with Session(engine) as session:
                    resource = self._retrieve_resource(session, identifier)
                    for attribute_name in resource.schema()["properties"]:
                        if hasattr(resource_create_instance, attribute_name):
                            new_value = getattr(resource_create_instance, attribute_name)
                            setattr(resource, attribute_name, new_value)
                    deserialize_resource_relationships(
                        session, self.resource_class, resource, resource_create_instance
                    )
                    try:
                        session.merge(resource)
                        session.commit()
                    except Exception as e:
                        self._raise_clean_http_exception(e, session, resource_create_instance)
                return self._wrap_with_headers(None)
            except Exception as e:
                raise _wrap_as_http_exception(e)

        return put_resource

    def delete_resource_func(self, engine: Engine):
        """
        Return a function that can be used to delete a resource.
        This function returns a function (instead of being that function directly) because the
        docstring is dynamic and used in Swagger.
        """

        def delete_resource(identifier: str, user: dict = Depends(get_current_user)):
            if "groups" in user and KEYCLOAK_CONFIG.get("role") not in user["groups"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to edit Aiod resources.",
                )

            try:
                with Session(engine) as session:
                    self._retrieve_resource(session, identifier)  # Raise error if it does not exist
                    statement = delete(self.resource_class).where(
                        self.resource_class.identifier == identifier
                    )
                    session.execute(statement)
                    session.commit()
                return self._wrap_with_headers(None)
            except Exception as e:
                if "foreign key" in str(e).lower():  # Should work regardless of db technology
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This resource cannot be deleted, because other resources are "
                        "related to it.",
                    )
                raise _wrap_as_http_exception(e)

        return delete_resource

    def _retrieve_resource(self, session, identifier, platform=None):
        if platform is None:
            query = select(self.resource_class).where(self.resource_class.identifier == identifier)
        else:
            if platform not in {n.name for n in PlatformName}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"platform '{platform}' not recognized.",
                )
            query = select(self.resource_class).where(
                and_(
                    self.resource_class.platform_identifier == identifier,
                    self.resource_class.platform == platform,
                )
            )
        resource = session.scalars(query).first()
        if not resource:
            if platform is None:
                msg = f"{self.resource_name.capitalize()} '{identifier}' not found in the database."
            else:
                msg = (
                    f"{self.resource_name.capitalize()} '{identifier}' of '{platform}' not found "
                    "in the database."
                )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        return resource

    @property
    def _possible_schemas(self) -> list[str]:
        return ["aiod"] + list(self.schema_converters.keys())

    def _wrap_with_headers(self, resource):
        if self.deprecated_from is None:
            return resource
        timestamp = datetime.datetime.combine(
            self.deprecated_from, datetime.time.min, tzinfo=datetime.timezone.utc
        ).timestamp()
        headers = {"Deprecated": format_date_time(timestamp)}
        return JSONResponse(content=jsonable_encoder(resource, exclude_none=True), headers=headers)

    def _raise_clean_http_exception(
        self, e: Exception, session: Session, resource_create: SQLModel
    ):
        """Raise an understandable exception based on this SQL IntegrityError."""
        session.rollback()
        if len(e.args) == 0:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected exception while processing your request. Please "
                "contact the maintainers.",
            ) from e
        error = e.args[0]
        # Note that the "real" errors are different from testing errors, because we use a
        # sqlite db while testing and a mysql db when running the application. The correct error
        # handling is therefore not tested. TODO: can we improve this?
        if "MySQLdb.IntegrityError" in error:
            fields = error.split("same_")[-1].split("'")[0]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"There already exists a {self.resource_name} with the same {fields}.",
            )
        if "UNIQUE constraint failed: " in error and ", " not in error:
            duplicate_field = error.split(".")[-1]
            query = select(self.resource_class).where(
                getattr(self.resource_class, duplicate_field)
                == getattr(resource_create, duplicate_field)
            )
            existing_resource = session.scalars(query).first()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"There already exists a {self.resource_name} with the same "
                f"{duplicate_field}, with "
                f"identifier={existing_resource.identifier}.",
            ) from e
        if "UNIQUE constraint failed: " in error:
            fields = error.split("constraint failed: ")[-1]
            field1, field2 = [field.split(".")[-1] for field in fields.split(", ")]
            query = select(self.resource_class).where(
                and_(
                    getattr(self.resource_class, field1) == getattr(resource_create, field1),
                    getattr(self.resource_class, field2) == getattr(resource_create, field2),
                )
            )
            existing_resource = session.scalars(query).first()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"There already exists a {self.resource_name} with the same "
                f"{field1} and {field2}, with "
                f"identifier={existing_resource.identifier}.",
            ) from e
        if (
            "FOREIGN KEY" in error
            and issubclass(self.resource_class, Resource)
            and resource_create.platform is not None
        ):
            query = select(Platform).where(Platform.name == resource_create.platform)
            if session.scalars(query).first() is None:
                raise HTTPException(
                    status_code=status.HTTP_412_PRECONDITION_FAILED,
                    detail=f"Platform {resource_create.platform} does not exist. "
                    f"You can register it using the POST platforms "
                    f"endpoint.",
                )
        if "platform_xnor_platform_id_null" in error:
            error_msg = (
                "If platform is NULL, platform_identifier should also be NULL, and vice versa."
            )
        else:
            error_msg = error.split("constraint failed: ")[-1]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg) from e


def _wrap_as_http_exception(exception: Exception) -> HTTPException:
    if isinstance(exception, HTTPException):
        return exception
    traceback.print_exc()
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "Unexpected exception while processing your request. Please contact the maintainers: "
            f"{exception}"
        ),
    )


def _raise_error_on_invalid_schema(possible_schemas, schema):
    if schema not in possible_schemas:
        raise HTTPException(
            detail=f"Invalid schema {schema}. Expected {' or '.join(possible_schemas)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
