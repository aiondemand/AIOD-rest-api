import abc
import datetime
import traceback
from functools import partial
from typing import Annotated, Any, Literal, Sequence, Type, TypeVar, Union
from wsgiref.handlers import format_date_time

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import and_, func
from sqlalchemy.sql.operators import is_
from sqlmodel import SQLModel, Session, select, Field
from starlette.responses import JSONResponse

from authentication import User, get_user_or_none, get_user_or_raise
from config import KEYCLOAK_CONFIG
from converters.schema_converters.schema_converter import SchemaConverter
from database.model.ai_resource.resource import AbstractAIResource
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import (
    resource_create,
    resource_read,
)
from database.model.serializers import deserialize_resource_relationships
from database.session import DbSession
from error_handling import as_http_exception


class Pagination(BaseModel):
    """Offset-based pagination."""

    offset: int = Field(
        Query(
            description="Specifies the number of resources that should be skipped.", default=0, ge=0
        )
    )
    # Query inside field to ensure description is shown in Swagger.
    # Refer to https://github.com/tiangolo/fastapi/issues/4700
    limit: int = Field(
        Query(
            description="Specified the maximum number of resources that should be " "returned.",
            default=10,
            le=1000,
        )
    )


RESOURCE = TypeVar("RESOURCE", bound=AbstractAIResource)
RESOURCE_CREATE = TypeVar("RESOURCE_CREATE", bound=SQLModel)
RESOURCE_READ = TypeVar("RESOURCE_READ", bound=SQLModel)
RESOURCE_MODEL = TypeVar("RESOURCE_MODEL", bound=SQLModel)


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
    def resource_class(self) -> type[RESOURCE_MODEL]:
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

    def create(self, url_prefix: str) -> APIRouter:
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
            endpoint=self.get_resources_func(),
            response_model=response_model_plural,  # type: ignore
            name=f"List {self.resource_name_plural}",
            description=f"Retrieve all meta-data of the {self.resource_name_plural}.",
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/counts/{self.resource_name_plural}/v1",
            endpoint=self.get_resource_count_func(),
            response_model=int | dict[str, int],
            name=f"Count of {self.resource_name_plural}",
            description=f"Retrieve the number of {self.resource_name_plural}.",
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}",
            methods={"POST"},
            endpoint=self.register_resource_func(),
            name=self.resource_name,
            description=f"Register a {self.resource_name} with AIoD.",
            **default_kwargs,
        )
        router.add_api_route(
            path=url_prefix + f"/{self.resource_name_plural}/{version}/{{identifier}}",
            endpoint=self.get_resource_func(),
            response_model=response_model,  # type: ignore
            name=self.resource_name,
            description=f"Retrieve all meta-data for a {self.resource_name} identified by the AIoD "
            "identifier.",
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}/{{identifier}}",
            methods={"PUT"},
            endpoint=self.put_resource_func(),
            name=self.resource_name,
            description=f"Update an existing {self.resource_name}.",
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}/{{identifier}}",
            methods={"DELETE"},
            endpoint=self.delete_resource_func(),
            name=self.resource_name,
            description=f"Delete a {self.resource_name}.",
            **default_kwargs,
        )
        if hasattr(self.resource_class, "platform"):
            router.add_api_route(
                path=f"{url_prefix}/platforms/{{platform}}/{self.resource_name_plural}/{version}",
                endpoint=self.get_platform_resources_func(),
                response_model=response_model_plural,  # type: ignore
                name=f"List {self.resource_name_plural}",
                description=f"Retrieve all meta-data of the {self.resource_name_plural} of given "
                f"platform.",
                **default_kwargs,
            )
            router.add_api_route(
                path=f"{url_prefix}/platforms/{{platform}}/{self.resource_name_plural}/{version}"
                f"/{{identifier}}",
                endpoint=self.get_platform_resource_func(),
                response_model=response_model,  # type: ignore
                name=self.resource_name,
                description=f"Retrieve all meta-data for a {self.resource_name} identified by the "
                "platform-specific-identifier.",
                **default_kwargs,
            )
        return router

    def get_resources(
        self,
        schema: str,
        pagination: Pagination,
        user: User | None = None,
        platform: str | None = None,
    ):
        """Fetch all resources of this platform in given schema, using pagination"""
        _raise_error_on_invalid_schema(self._possible_schemas, schema)
        with DbSession(autoflush=False) as session:
            try:
                convert_schema = (
                    partial(self.schema_converters[schema].convert, session)
                    if schema != "aiod"
                    else self.resource_class_read.from_orm
                )
                resources: Any = self._retrieve_resources_and_post_process(
                    session, pagination, user, platform
                )
                return self._wrap_with_headers([convert_schema(resource) for resource in resources])
            except Exception as e:
                raise as_http_exception(e)

    def get_resource(
        self, identifier: str, schema: str, user: User | None = None, platform: str | None = None
    ):
        """
        Get the resource identified by AIoD identifier (if platform is None) or by platform AND
        platform-identifier (if platform is not None), return in given schema.
        """
        _raise_error_on_invalid_schema(self._possible_schemas, schema)
        try:
            with DbSession(autoflush=False) as session:
                resource: Any = self._retrieve_resource_and_post_process(
                    session, identifier, user, platform=platform
                )
                if schema != "aiod":
                    return self.schema_converters[schema].convert(session, resource)
                return self._wrap_with_headers(self.resource_class_read.from_orm(resource))
        except Exception as e:
            raise as_http_exception(e)

    def get_resources_func(self):
        """
        Return a function that can be used to retrieve a list of resources.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resources(
            pagination: Pagination = Depends(),
            schema: self._possible_schemas_type = "aiod",  # type:ignore
            user: User | None = Depends(get_user_or_none),
        ):
            resources = self.get_resources(
                pagination=pagination, schema=schema, user=user, platform=None
            )
            return resources

        return get_resources

    def get_resource_count_func(self):
        """
        Gets the total number of resources from the database.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resource_count(
            detailed: Annotated[
                bool, Query(description="If true, a more detailed output is returned.")
            ] = False,
        ):
            try:
                with DbSession() as session:
                    if not detailed:
                        return (
                            session.query(self.resource_class)
                            .where(is_(self.resource_class.date_deleted, None))
                            .count()
                        )
                    else:
                        count_list = (
                            session.query(
                                self.resource_class.platform,
                                func.count(self.resource_class.identifier),
                            )
                            .where(is_(self.resource_class.date_deleted, None))
                            .group_by(self.resource_class.platform)
                            .all()
                        )
                        return {
                            platform if platform else "aiod": count
                            for platform, count in count_list
                        }
            except Exception as e:
                raise as_http_exception(e)

        return get_resource_count

    def get_platform_resources_func(self):
        """
        Return a function that can be used to retrieve a list of resources for a platform.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resources(
            platform: Annotated[
                str,
                Path(
                    description="Return resources of this platform",
                    example="huggingface",
                ),
            ],
            pagination: Annotated[Pagination, Depends(Pagination)],
            schema: self._possible_schemas_type = "aiod",  # type:ignore
            user: User | None = Depends(get_user_or_none),
        ):
            resources = self.get_resources(
                pagination=pagination, schema=schema, user=user, platform=platform
            )
            return resources

        return get_resources

    def get_resource_func(self):
        """
        Return a function that can be used to retrieve a single resource.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resource(
            identifier: str,
            schema: self._possible_schemas_type = "aiod",  # type: ignore
            user: User | None = Depends(get_user_or_none),
        ):
            resource = self.get_resource(
                identifier=identifier, schema=schema, user=user, platform=None
            )
            return self._wrap_with_headers(resource)

        return get_resource

    def get_platform_resource_func(self):
        """
        Return a function that can be used to retrieve a single resource of a platform.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resource(
            identifier: Annotated[
                str,
                Path(
                    description="The identifier under which the resource is known by the platform.",
                ),
            ],
            platform: Annotated[
                str,
                Path(
                    description="Return resources of this platform",
                    example="huggingface",
                ),
            ],
            schema: self._possible_schemas_type = "aiod",  # type:ignore
            user: User | None = Depends(get_user_or_none),
        ):
            return self.get_resource(
                identifier=identifier, schema=schema, user=user, platform=platform
            )

        return get_resource

    def register_resource_func(self):
        """
        Return a function that can be used to register a resource.
        This function returns a function (instead of being that function directly) because the
        docstring is dynamic and used in Swagger.
        """
        clz_create = self.resource_class_create

        def register_resource(
            resource_create: clz_create,  # type: ignore
            user: User = Depends(get_user_or_raise),
        ):
            if not user.has_any_role(
                KEYCLOAK_CONFIG.get("role"),
                f"create_{self.resource_name_plural}",
                f"crud_{self.resource_name_plural}",
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You do not have permission to create {self.resource_name_plural}.",
                )
            try:
                with DbSession() as session:
                    try:
                        resource = self.create_resource(session, resource_create, user)
                        return self._wrap_with_headers({"identifier": resource.identifier})
                    except Exception as e:
                        self._raise_clean_http_exception(e, session, resource_create)
            except Exception as e:
                raise as_http_exception(e)

        return register_resource

    def create_resource(self, session: Session, resource_create_instance: SQLModel, user: User):
        """Store a resource in the database"""
        resource = self.resource_class.from_orm(resource_create_instance)
        deserialize_resource_relationships(
            session, self.resource_class, resource, resource_create_instance
        )
        resource.aiod_entry.creator_identifier = user.subject_identifier
        session.add(resource)
        session.commit()
        return resource

    def put_resource_func(self):
        """
        Return a function that can be used to update a resource.
        This function returns a function (instead of being that function directly) because the
        docstring is dynamic and used in Swagger.
        """
        clz_create = self.resource_class_create

        def put_resource(
            identifier: int,
            resource_create_instance: clz_create,  # type: ignore
            user: User = Depends(get_user_or_raise),
        ):
            if not user.has_any_role(
                KEYCLOAK_CONFIG.get("role"),
                f"update_{self.resource_name_plural}",
                f"crud_{self.resource_name_plural}",
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You do not have permission to edit {self.resource_name_plural}.",
                )

            with DbSession() as session:
                try:
                    resource: Any = self._retrieve_resource(session, identifier)
                    if not resource.owned_by(user):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=(
                                f"You do not have permission to edit "
                                f"{self.resource_name} {identifier}."
                            ),
                        )
                    for attribute_name in resource.schema()["properties"]:
                        if hasattr(resource_create_instance, attribute_name):
                            new_value = getattr(resource_create_instance, attribute_name)
                            setattr(resource, attribute_name, new_value)
                    deserialize_resource_relationships(
                        session, self.resource_class, resource, resource_create_instance
                    )
                    if hasattr(resource, "aiod_entry"):
                        resource.aiod_entry.date_modified = datetime.datetime.utcnow()
                    try:
                        session.merge(resource)
                        session.commit()
                    except Exception as e:
                        self._raise_clean_http_exception(e, session, resource_create_instance)
                    return self._wrap_with_headers(None)
                except Exception as e:
                    raise self._raise_clean_http_exception(e, session, resource_create_instance)

        return put_resource

    def delete_resource_func(self):
        """
        Return a function that can be used to delete a resource.
        This function returns a function (instead of being that function directly) because the
        docstring is dynamic and used in Swagger.
        """

        def delete_resource(
            identifier: str,
            user: User = Depends(get_user_or_raise),
        ):
            with DbSession() as session:
                if not user.has_any_role(
                    KEYCLOAK_CONFIG.get("role"),
                    f"delete_{self.resource_name_plural}",
                    f"crud_{self.resource_name_plural}",
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You do not have permission to delete {self.resource_name_plural}.",
                    )
                try:
                    # Raise error if it does not exist
                    resource: Any = self._retrieve_resource(session, identifier)
                    if not resource.owned_by(user):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=(
                                f"You do not have permission to delete "
                                f"{self.resource_name} {identifier}."
                            ),
                        )
                    if (
                        hasattr(self.resource_class, "__deletion_config__")
                        and not self.resource_class.__deletion_config__["soft_delete"]
                    ):
                        session.delete(resource)
                    else:
                        resource.date_deleted = datetime.datetime.utcnow()
                        session.add(resource)
                    session.commit()
                    return self._wrap_with_headers(None)
                except Exception as e:
                    raise as_http_exception(e)

        return delete_resource

    def _retrieve_resource(
        self,
        session: Session,
        identifier: int | str,
        platform: str | None = None,
    ) -> type[RESOURCE_MODEL]:
        """
        Retrieve a resource from the database based on the provided identifier
        and platform (if applicable).
        """
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
                    self.resource_class.platform_resource_identifier == identifier,
                    self.resource_class.platform == platform,
                )
            )
        resource = session.scalars(query).first()
        if not resource or resource.date_deleted is not None:
            name = (
                f"{self.resource_name.capitalize()} '{identifier}'"
                if platform is None
                else f"{self.resource_name.capitalize()} '{identifier}' of '{platform}'"
            )
            msg = (
                "not found in the database."
                if not resource
                else "not found in the database, " "because it was deleted."
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} {msg}")
        return resource

    def _retrieve_resources(
        self,
        session: Session,
        pagination: Pagination,
        platform: str | None = None,
    ) -> Sequence[type[RESOURCE_MODEL]]:
        """
        Retrieve a sequence of resources from the database based on the provided identifier
        and platform (if applicable).
        """
        where_clause = and_(
            is_(self.resource_class.date_deleted, None),
            (self.resource_class.platform == platform) if platform is not None else True,
        )
        query = (
            select(self.resource_class)
            .where(where_clause)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        resources: Sequence = session.scalars(query).all()
        return resources

    def _retrieve_resource_and_post_process(
        self,
        session: Session,
        identifier: int | str,
        user: User | None = None,
        platform: str | None = None,
    ) -> type[RESOURCE_MODEL]:
        """
        Retrieve a resource from the database based on the provided identifier
        and platform (if applicable). The user parameter can be used by subclasses to
        implement further verification on user access to the resource.
        """
        resource: type[RESOURCE_MODEL] = self._retrieve_resource(session, identifier, platform)
        [processed_resource] = self._mask_or_filter([resource], session, user)
        return processed_resource

    def _retrieve_resources_and_post_process(
        self,
        session: Session,
        pagination: Pagination,
        user: User | None = None,
        platform: str | None = None,
    ) -> Sequence[type[RESOURCE_MODEL]]:
        """
        Retrieve a sequence of resources from the database based on the provided identifier
        and platform (if applicable). The user parameter can be used by subclasses to
        implement further verification on user access to the resource.
        """
        resources: Sequence[type[RESOURCE_MODEL]] = self._retrieve_resources(
            session, pagination, platform
        )
        return self._mask_or_filter(resources, session, user)

    @staticmethod
    def _mask_or_filter(
        resources: Sequence[type[RESOURCE_MODEL]], session: Session, user: User | None
    ) -> Sequence[type[RESOURCE_MODEL]]:
        """
        Can be implemented in children to post process resources based on user roles
        or something else.
        """
        return resources

    @property
    def _possible_schemas(self) -> list[str]:
        return ["aiod"] + list(self.schema_converters.keys())

    @property
    def _possible_schemas_type(self):
        return Annotated[
            Literal[tuple(self._possible_schemas)],  # type: ignore
            Query(
                description="Return the resource(s) in this schema.",
                include_in_schema=len(self._possible_schemas) > 1,
            ),
        ]

    def _wrap_with_headers(self, resource):
        if self.deprecated_from is None:
            return resource
        timestamp = datetime.datetime.combine(
            self.deprecated_from, datetime.time.min, tzinfo=datetime.timezone.utc
        ).timestamp()
        headers = {"Deprecated": format_date_time(timestamp)}
        return JSONResponse(content=jsonable_encoder(resource, exclude_none=True), headers=headers)

    def _raise_clean_http_exception(
        self, e: Exception, session: Session, resource_create: AIoDConcept
    ):
        """Raise an understandable exception based on this SQL IntegrityError."""
        session.rollback()
        if isinstance(e, HTTPException):
            raise e
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
        if "_same_platform_and_platform_id" in error:
            query = select(self.resource_class).where(
                and_(
                    getattr(self.resource_class, "platform") == resource_create.platform,
                    getattr(self.resource_class, "platform_resource_identifier")
                    == resource_create.platform_resource_identifier,
                    is_(getattr(self.resource_class, "date_deleted"), None),
                )
            )
            existing_resource = session.scalars(query).first()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"There already exists a {self.resource_name} with the same platform and "
                f"platform_resource_identifier, with identifier={existing_resource.identifier}.",
            ) from e
        if ("UNIQUE" in error and "platform.name" in error) or (
            "Duplicate entry" in error and "platform_name" in error
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"There already exists a {self.resource_name} with the same name.",
            ) from e

        if "FOREIGN KEY" in error and resource_create.platform is not None:
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
                "If platform is NULL, platform_resource_identifier should also be NULL, "
                "and vice versa."
            )
            status_code = status.HTTP_400_BAD_REQUEST
        elif "contact_person_and_organisation_not_both_filled" in error:
            error_msg = "Person and organisation cannot be both filled."
            status_code = status.HTTP_400_BAD_REQUEST
        elif "constraint failed" in error:
            error_msg = error.split("constraint failed: ")[-1]
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            raise e
            # error_msg = "Unexpected exception."
            # status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=error_msg) from e


def _raise_error_on_invalid_schema(possible_schemas, schema):
    if schema not in possible_schemas:
        raise HTTPException(
            detail=f"Invalid schema {schema}. Expected {' or '.join(possible_schemas)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
