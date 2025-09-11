import abc
import datetime
import traceback
from functools import partial
from typing import Annotated, Any, Literal, Sequence, Type, TypeVar, Union, Callable, cast
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy import and_, func
from sqlalchemy.sql.operators import is_
from sqlmodel import SQLModel, Session, select

from authentication import KeycloakUser, get_user_or_none, get_user_or_raise
from converters.schema_converters.schema_converter import SchemaConverter
from database.authorization import (
    user_can_administer,
    set_permission,
    register_user,
    PermissionType,
    user_can_write,
    user_can_read,
)
from database.model.ai_resource.resource import AIResource
from database.model.concept.aiod_entry import AIoDEntryORM, EntryStatus
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.model.serializers import deserialize_resource_relationships
from database.review import Submission, SubmissionCreateV2, AssetReview
from database.session import DbSession
from dependencies.filtering import ResourceFilters, ResourceFiltersParams
from dependencies.pagination import Pagination, PaginationParams
from error_handling import as_http_exception
from database.model.ai_asset.distribution import Distribution
from versioning import Version, VersionedResource

from http import HTTPStatus
import base64

RESOURCE = TypeVar("RESOURCE", bound=AIResource)
RESOURCE_CREATE = TypeVar("RESOURCE_CREATE", bound=SQLModel)
RESOURCE_READ = TypeVar("RESOURCE_READ", bound=SQLModel)
RESOURCE_MODEL = TypeVar("RESOURCE_MODEL", bound=SQLModel)


class ResourceRouter(abc.ABC):
    """
    Abstract class for FastAPI resource router.

    It creates the basic endpoints for each resource:
    - GET /[resource]s/
    - GET /counts/[resource]s/
    - GET /[resource]s/{identifier}
    - GET /platforms/{platform_name}/[resource]s/
    - GET /platforms/{platform_name}/[resource]s/{identifier}
    - POST /[resource]s
    - PUT /[resource]s/{identifier}
    - DELETE /[resource]s/{identifier}
    """

    def __init__(self, resource: VersionedResource | None = None):
        resource = resource or VersionedResource(self.resource_class)
        self.resource_class_create = resource.resource_class_create
        self.resource_class_read = resource.resource_class_read
        self.create_to_orm = resource.create_to_orm
        self.orm_to_read = resource.orm_to_read

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

    def create(self, url_prefix: str, version: Version = Version.LATEST) -> APIRouter:
        router = APIRouter()
        default_kwargs = {
            "response_model_exclude_none": True,
            "tags": [self.resource_name_plural],
        }
        available_schemas: list[Type] = [c.to_class for c in self.schema_converters.values()]
        response_model = Union[self.resource_class_read, *available_schemas]  # type:ignore
        response_model_plural = Union[  # type:ignore
            list[self.resource_class_read], *[list[s] for s in available_schemas]  # type:ignore
        ]

        router.add_api_route(
            path=f"/{self.resource_name_plural}",
            endpoint=self.get_resources_func(),
            response_model=response_model_plural,  # type: ignore
            name=f"List {self.resource_name_plural}",
            description=f"Retrieve all meta-data of the {self.resource_name_plural}.",
            **default_kwargs,
        )

        router.add_api_route(
            path=f"/counts/{self.resource_name_plural}",
            endpoint=self.get_resource_count_func(),
            response_model=int | dict[str, int],
            name=f"Count of {self.resource_name_plural}",
            description=f"Retrieve the number of {self.resource_name_plural}.",
            **default_kwargs,
        )

        if version == Version.V2:
            router.add_api_route(
                path=f"/{self.resource_name_plural}/submit/{{identifier}}",
                methods={"POST"},
                endpoint=self.get_submit_func(),
                name=self.resource_name,
                description=(
                    "DEPRECATED: Use `POST /submissions` instead. <br>"
                    f"Submit a {self.resource_name} for review."
                ),
                deprecated=True,
                **default_kwargs,
            )

        router.add_api_route(
            path=f"/{self.resource_name_plural}",
            methods={"POST"},
            endpoint=self.register_resource_func(),
            name=self.resource_name,
            description=f"Register a {self.resource_name} with AIoD.",
            **default_kwargs,
        )

        router.add_api_route(
            path=f"/{self.resource_name_plural}/{{identifier}}",
            endpoint=self.get_resource_func(),
            response_model=response_model,  # type: ignore
            name=self.resource_name,
            description=f"Retrieve all meta-data for a {self.resource_name} identified by the AIoD "
            "identifier.",
            **default_kwargs,
        )

        router.add_api_route(
            path=f"/{self.resource_name_plural}/{{identifier}}",
            methods={"PUT"},
            endpoint=self.put_resource_func(),
            name=self.resource_name,
            description=f"Update an existing {self.resource_name}.",
            **default_kwargs,
        )

        router.add_api_route(
            path=f"/{self.resource_name_plural}/{{identifier}}",
            methods={"DELETE"},
            endpoint=self.delete_resource_func(),
            name=self.resource_name,
            description=f"Delete a {self.resource_name}.",
            **default_kwargs,
        )

        if hasattr(self.resource_class, "platform"):
            router.add_api_route(
                path=f"/platforms/{{platform}}/{self.resource_name_plural}",
                endpoint=self.get_platform_resources_func(),
                response_model=response_model_plural,  # type: ignore
                name=f"List {self.resource_name_plural}",
                description=f"Retrieve all meta-data of the {self.resource_name_plural} of given "
                f"platform.",
                **default_kwargs,
            )

            router.add_api_route(
                path=f"/platforms/{{platform}}/{self.resource_name_plural}/{{identifier}}",
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
        resource_filters: ResourceFilters,
        user: KeycloakUser | None = None,
        platform: str | None = None,
        get_image: bool = False,
    ):
        """Fetch all published resources of this platform in given schema, using pagination"""
        _raise_error_on_invalid_schema(self._possible_schemas, schema)
        with DbSession(autoflush=False) as session:
            try:
                # mypy does a weird thing here where each individual branch type checks fine,
                # but together it fails to type check. Likely to do with partial being an object.
                convert_schema = (
                    cast(Callable, partial(self.schema_converters[schema].convert, session))
                    if schema != "aiod"
                    else cast(Callable, self.orm_to_read)
                )
                resources: Any = self._retrieve_resources_and_post_process(
                    session, pagination, resource_filters, user, platform
                )
                for resource in resources:
                    if not get_image and hasattr(resource, "media") and resource.media:
                        for media_obj in resource.media:
                            media_obj.binary_blob = None

                    # Add image blobs if requested
                    if get_image:
                        self._add_binary_bytes_to_resource(session, resource)

                return [convert_schema(resource) for resource in resources]
            except Exception as e:
                raise as_http_exception(e)

    def get_resource(
        self,
        identifier: str,
        schema: str,
        user: KeycloakUser | None = None,
        platform: str | None = None,
        get_image: bool = False,
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

                # Remove images if not requested
                if not get_image and hasattr(resource, "media") and resource.media:
                    for media_obj in resource.media:
                        media_obj.binary_blob = None

                if get_image:
                    resource = self._add_binary_bytes_to_resource(session, resource)

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

                if schema != "aiod":
                    return self.schema_converters[schema].convert(session, resource)
                return self.orm_to_read(resource)
        except Exception as e:
            raise as_http_exception(e)

    def get_resources_func(self):
        """
        Return a function that can be used to retrieve a list of resources.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resources(
            pagination: PaginationParams,
            resource_filters: ResourceFiltersParams,
            schema: self._possible_schemas_type = "aiod",  # type:ignore
            user: KeycloakUser | None = Depends(get_user_or_none),
        ):
            resources = self.get_resources(
                schema=schema,
                pagination=pagination,
                resource_filters=resource_filters,
                user=user,
                platform=None,
            )
            return resources

        return get_resources

    def get_resource_count_func(self):
        """
        Gets the total number of published resources from the database.
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
                            .join(self.resource_class.aiod_entry, isouter=True)
                            .where(
                                is_(self.resource_class.date_deleted, None),
                                AIoDEntryORM.status == EntryStatus.PUBLISHED,
                            )
                            .count()
                        )
                    else:
                        count_list = (
                            session.query(
                                self.resource_class.platform,
                                func.count(self.resource_class.identifier),
                            )
                            .join(self.resource_class.aiod_entry, isouter=True)
                            .where(
                                is_(self.resource_class.date_deleted, None),
                                AIoDEntryORM.status == EntryStatus.PUBLISHED,
                            )
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
            pagination: PaginationParams,
            resource_filters: ResourceFiltersParams,
            schema: self._possible_schemas_type = "aiod",  # type:ignore
            user: KeycloakUser | None = Depends(get_user_or_none),
        ):
            resources = self.get_resources(
                schema=schema,
                pagination=pagination,
                resource_filters=resource_filters,
                user=user,
                platform=platform,
            )
            return resources

        return get_resources

    def _add_binary_bytes_to_resource(self, session: Session, resource: AIoDConcept):
        """
        Attach binary_blob bytes as base64 encoded image from the resource's media.
        """
        if hasattr(resource, "media") and resource.media:
            for media_obj in resource.media:
                if media_obj.binary_blob:
                    media_obj.binary_blob = base64.b64encode(media_obj.binary_blob).decode("utf-8")
                else:
                    media_obj.binary_blob = None
        return resource

    def get_resource_func(self):
        """
        Return a function that can be used to retrieve a single resource.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resource(
            identifier: str,
            schema: self._possible_schemas_type = "aiod",  # type: ignore
            user: KeycloakUser | None = Depends(get_user_or_none),
        ):
            resource = self.get_resource(
                identifier=identifier, schema=schema, user=user, platform=None
            )

            return resource

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
            user: KeycloakUser | None = Depends(get_user_or_none),
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
            user: KeycloakUser = Depends(get_user_or_raise),
        ):
            platform = getattr(resource_create, "platform", None)
            platform_resource_identifier = getattr(
                resource_create, "platform_resource_identifier", None
            )
            if user.is_connector:
                # Check if connector belongs to the specific platform it is registering the resource for.
                if platform is None or not user.is_connector_for_platform(platform):
                    raise HTTPException(
                        status_code=HTTPStatus.FORBIDDEN,
                        detail=f"No permission to upload assets for {platform} platform.",
                    )
                if platform_resource_identifier is None:
                    raise HTTPException(
                        status_code=HTTPStatus.FORBIDDEN,
                        detail=f"Platform resource identifier may not be none.",
                    )

            # Normal user: must NOT provide platform/platform_resource_identifier
            else:
                if platform is not None or platform_resource_identifier is not None:
                    raise HTTPException(
                        status_code=HTTPStatus.FORBIDDEN,
                        detail="No permission to set platform or platform resource identifier.",
                    )

            _raise_if_contains_binary_blob(resource_create)
            try:
                with DbSession() as session:
                    try:
                        resource = self.create_resource(session, resource_create, user)

                        register_user(user, session)
                        set_permission(
                            user, resource.aiod_entry, session, type_=PermissionType.ADMIN
                        )
                        session.commit()
                        return {"identifier": resource.identifier}
                    except Exception as e:
                        self._raise_clean_http_exception(e, session, resource_create)
            except Exception as e:
                raise as_http_exception(e)

        return register_resource

    def create_resource(
        self,
        session: Session,
        resource_create_instance: SQLModel,
        user: KeycloakUser | None = None,
    ):
        """Store a resource in the database"""
        resource = self.create_to_orm(resource_create_instance)
        deserialize_resource_relationships(
            session, self.resource_class, resource, resource_create_instance, user
        )
        session.add(resource)
        session.flush()

        if resource.platform is None and resource.platform_resource_identifier is None:
            # Set these fields as required for normal users
            resource.platform = PlatformName.aiod
            resource.platform_resource_identifier = resource.identifier

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
            identifier: str,
            resource_create_instance: clz_create,  # type: ignore
            user: KeycloakUser = Depends(get_user_or_raise),
        ):
            with DbSession() as session:
                try:
                    resource: Any = self._retrieve_resource(session, identifier)
                    _raise_if_contains_binary_blob(resource_create_instance)
                    if not (
                        user_can_write(user, resource.aiod_entry)
                        or user.has_role(f"update_{self.resource_name_plural}")
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You do not have permission to edit {self.resource_name_plural}.",
                        )

                    if resource.aiod_entry.status == EntryStatus.SUBMITTED:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="You cannot edit an asset under submission.",
                        )
                    # TODO: Versioning, probably need to change the Create instance into
                    # ORM object and then do the updates so they are of the same schema.
                    for attribute_name in resource.schema()["properties"]:
                        if hasattr(resource_create_instance, attribute_name):
                            new_value = getattr(resource_create_instance, attribute_name)
                            setattr(resource, attribute_name, new_value)
                    deserialize_resource_relationships(
                        session, self.resource_class, resource, resource_create_instance, user
                    )
                    if hasattr(resource, "aiod_entry"):
                        resource.aiod_entry.date_modified = datetime.datetime.utcnow()
                    try:
                        session.merge(resource)
                        session.commit()
                    except Exception as e:
                        self._raise_clean_http_exception(e, session, resource_create_instance)
                    return None
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
            user: KeycloakUser = Depends(get_user_or_raise),
        ):
            with DbSession() as session:
                try:
                    # Raise error if it does not exist
                    resource: Any = self._retrieve_resource(session, identifier)
                    if not (
                        user_can_administer(user, resource.aiod_entry)
                        or user.has_role(f"delete_{self.resource_name_plural}")
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You do not have permission to delete {self.resource_name_plural}.",
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
                    return None
                except Exception as e:
                    raise as_http_exception(e)

        return delete_resource

    def get_submit_func(self):
        """Return a function that can be used to submit a single resource for review."""

        def submit_resource(
            identifier: str,
            submission: SubmissionCreateV2 | None = None,
            user: KeycloakUser = Depends(get_user_or_raise),
        ):
            with DbSession() as session:
                resource = self._retrieve_resource(identifier=identifier, session=session)  # type: ignore

                if not resource.aiod_entry.status == EntryStatus.DRAFT:
                    msg = (
                        f"Cannot submit {self.resource_name} {identifier} "
                        f"since it has '{resource.aiod_entry.status}' status."
                    )
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

                if not user_can_administer(user, resource.aiod_entry):
                    # Could choose to instead give same error as if resource does not exist.
                    msg = f"You do not have permission to submit {self.resource_name} {identifier}."
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

                resource.aiod_entry.status = EntryStatus.SUBMITTED
                review_request = Submission(
                    requestee_identifier=user._subject_identifier,
                    comment=submission.comment if submission else "",
                )
                review_request._assets.append(
                    AssetReview(
                        asset_identifier=resource.identifier,
                        aiod_entry_identifier=resource.aiod_entry.identifier,
                    )
                )
                session.add(review_request)
                session.commit()
                return {"submission_identifier": review_request.identifier}

        return submit_resource

    def _retrieve_resource(
        self,
        session: Session,
        identifier: int | str,
        platform: str | None = None,
        *,
        is_entry_identifier: bool = False,
    ) -> type[RESOURCE_MODEL]:
        """
        Retrieve a resource from the database based on the provided identifier
        and platform (if applicable).
        """
        if platform is None:
            if is_entry_identifier:
                query = select(self.resource_class).where(
                    self.resource_class.aiod_entry_identifier == identifier
                )
            else:
                query = select(self.resource_class).where(
                    self.resource_class.identifier == identifier
                )
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
                else "not found in the database, because it was deleted."
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} {msg}")
        return resource

    def _retrieve_resources(
        self,
        session: Session,
        pagination: Pagination,
        resource_filters: ResourceFilters,
        platform: str | None = None,
    ) -> Sequence[type[RESOURCE_MODEL]]:
        """
        Retrieve a sequence of published resources from the database based on the
        provided identifier, platform and resource filters (if applicable).
        """
        where_clause = and_(
            is_(self.resource_class.date_deleted, None),
            (self.resource_class.platform == platform) if platform is not None else True,
            AIoDEntryORM.date_modified >= resource_filters.date_modified_after
            if resource_filters.date_modified_after is not None
            else True,
            AIoDEntryORM.date_modified < resource_filters.date_modified_before
            if resource_filters.date_modified_before is not None
            else True,
            AIoDEntryORM.status == EntryStatus.PUBLISHED,
        )
        query = (
            select(self.resource_class)
            .join(self.resource_class.aiod_entry, isouter=True)
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
        user: KeycloakUser | None = None,
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
        resource_filters: ResourceFilters,
        user: KeycloakUser | None = None,
        platform: str | None = None,
    ) -> Sequence[type[RESOURCE_MODEL]]:
        """
        Retrieve a sequence of resources from the database based on the provided identifier
        and platform (if applicable). The user parameter can be used by subclasses to
        implement further verification on user access to the resource.
        """
        resources: Sequence[type[RESOURCE_MODEL]] = self._retrieve_resources(
            session, pagination, resource_filters, platform
        )
        return self._mask_or_filter(resources, session, user)

    @staticmethod
    def _mask_or_filter(
        resources: Sequence[type[RESOURCE_MODEL]], session: Session, user: KeycloakUser | None
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
        if isinstance(e, ValueError) and "taxonomy" in error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
            )
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


def _raise_if_contains_binary_blob(item):
    distributions = []
    if hasattr(item, "distribution") and (distribution := getattr(item, "distribution")):
        distributions += distribution
    if hasattr(item, "media") and (media := getattr(item, "media")):
        distributions += media

    if any((isinstance(item, Distribution) and item.binary_blob) for item in distributions):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Setting `binary_blob` is forbidden. Consider using `content_url` instead.",
        )
