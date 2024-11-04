import traceback
from typing import Any, Sequence

from fastapi import Depends, HTTPException, status, APIRouter
from sqlmodel import SQLModel, Session, select

from authentication import User, get_user_or_raise
from config import KEYCLOAK_CONFIG
from database.model.platform.platform import Platform
from database.model.resource_read_and_create import resource_create, resource_read
from database.model.serializers import deserialize_resource_relationships
from database.session import DbSession
from dependencies.pagination import Pagination, PaginationParams
from error_handling import as_http_exception


class PlatformRouter:
    """
    Router class for FastAPI Platform router.

    It creates the basic endpoints for Platform:
    - GET /platforms/
    - GET /counts/platforms/
    - GET /platforms/{identifier}
    - POST /platforms
    - PUT /platforms/{identifier}
    - DELETE /platforms/{identifier}
    """

    def __init__(self):
        self.resource_class_create = resource_create(self.resource_class)
        self.resource_class_read = resource_read(self.resource_class)

    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "platform"

    @property
    def resource_name_plural(self) -> str:
        return "platforms"

    @property
    def resource_class(self) -> type[Platform]:
        return Platform

    def create(self, url_prefix: str) -> APIRouter:
        router = APIRouter()
        version = f"v{self.version}"
        default_kwargs = {
            "response_model_exclude_none": True,
            "deprecated": False,
            "tags": [self.resource_name_plural],
        }
        response_model = self.resource_class_read  # type:ignore
        response_model_plural = list[self.resource_class_read]  # type:ignore

        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}",
            endpoint=self.get_resources_func(),
            response_model=response_model_plural,  # type: ignore
            name=f"List {self.resource_name_plural}",
            description=f"Retrieve all meta-data of the {self.resource_name_plural}.",
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/counts/{self.resource_name_plural}/{version}",
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
        return router

    def get_resources(self, pagination: Pagination):
        """Fetch all resources."""
        with DbSession(autoflush=False) as session:
            try:
                resources: Any = self._retrieve_resources(session, pagination)
                return [self.resource_class_read.model_validate(resource) for resource in resources]
            except Exception as e:
                raise as_http_exception(e)

    def get_resource(self, identifier: str):
        """Get the resource identified by AIoD identifier."""
        try:
            with DbSession(autoflush=False) as session:
                resource: Any = self._retrieve_resource(session, identifier)
                return self.resource_class_read.model_validate(resource)
        except Exception as e:
            raise as_http_exception(e)

    def get_resources_func(self):
        """
        Return a function that can be used to retrieve a list of resources.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resources(pagination: PaginationParams):
            resources = self.get_resources(pagination=pagination)
            return resources

        return get_resources

    def get_resource_count_func(self):
        """
        Gets the total number of resources from the database.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resource_count():
            try:
                with DbSession() as session:
                    return session.query(self.resource_class).count()

            except Exception as e:
                raise as_http_exception(e)

        return get_resource_count

    def get_resource_func(self):
        """
        Return a function that can be used to retrieve a single resource.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        return self.get_resource

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
                        resource = self.create_resource(session, resource_create)
                        return {"identifier": resource.identifier}
                    except Exception as e:
                        self._raise_clean_http_exception(e, session)
            except Exception as e:
                raise as_http_exception(e)

        return register_resource

    def create_resource(self, session: Session, resource_create_instance: SQLModel):
        """Store a resource in the database"""
        resource = self.resource_class.model_validate(resource_create_instance)
        deserialize_resource_relationships(
            session, self.resource_class, resource, resource_create_instance
        )
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
                        self._raise_clean_http_exception(e, session)
                    return None
                except Exception as e:
                    raise self._raise_clean_http_exception(e, session)

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
                    session.delete(resource)
                    session.commit()
                    return None
                except Exception as e:
                    raise as_http_exception(e)

        return delete_resource

    def _retrieve_resource(
        self,
        session: Session,
        identifier: int | str,
    ) -> Platform:
        """Retrieve a resource from the database based on the provided identifier."""
        query = select(self.resource_class).where(self.resource_class.identifier == identifier)

        resource = session.scalars(query).first()
        if not resource:
            name = f"{self.resource_name.capitalize()} '{identifier}'"
            msg = "not found in the database."
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} {msg}")
        return resource

    def _retrieve_resources(
        self,
        session: Session,
        pagination: Pagination,
    ) -> Sequence[Platform]:
        """
        Retrieve a sequence of resources from the database based on the provided identifier.
        """
        query = select(self.resource_class).offset(pagination.offset).limit(pagination.limit)
        resources: Sequence = session.scalars(query).all()
        return resources

    def _raise_clean_http_exception(self, e: Exception, session: Session):
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
        if ("UNIQUE" in error and "platform.name" in error) or (
            "Duplicate entry" in error and "platform_name" in error
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"There already exists a {self.resource_name} with the same name.",
            ) from e
        if "constraint failed" in error:
            error_msg = error.split("constraint failed: ")[-1]
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            raise e
        raise HTTPException(status_code=status_code, detail=error_msg) from e
