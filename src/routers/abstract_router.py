import abc
import datetime
import traceback
from typing import Generic, TypeVar, Type, List
from wsgiref.handlers import format_date_time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import Engine, select, and_, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from converters.abstract_converter import ResourceConverter
from database.model.resource import OrmResource
from platform_names import PlatformName
from schemas import AIoDResource


class Pagination(BaseModel):
    offset: int = 0
    limit: int = 100


ORM_CLASS = TypeVar("ORM_CLASS", bound=OrmResource)
AIOD_CLASS = TypeVar("AIOD_CLASS", bound=AIoDResource)


class ResourceRouter(abc.ABC, Generic[ORM_CLASS, AIOD_CLASS]):
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
    def converter(self) -> ResourceConverter[AIOD_CLASS, ORM_CLASS]:
        pass

    @property
    @abc.abstractmethod
    def aiod_class(self) -> Type[AIOD_CLASS]:
        pass

    @property
    @abc.abstractmethod
    def orm_class(self) -> Type[ORM_CLASS]:
        pass

    def create(self, engine: Engine, url_prefix: str) -> APIRouter:
        router = APIRouter()
        version = f"v{self.version}"
        default_kwargs = {
            "response_model_exclude_none": True,
            "deprecated": self.deprecated_from is not None,
        }

        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}",
            endpoint=self.list_resources_func(engine),
            response_model=List[self.aiod_class],  # type: ignore
            name=f"List {self.resource_name_plural}",
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}",
            methods={"POST"},
            endpoint=self.register_resource_func(engine),
            response_model=self.aiod_class,  # type: ignore
            name=self.resource_name,
            **default_kwargs,
        )
        router.add_api_route(
            path=url_prefix + f"/{self.resource_name_plural}/{version}/{{identifier}}",
            endpoint=self.get_resource_func(engine),
            response_model=self.aiod_class,  # type: ignore
            name=self.resource_name,
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}/{{identifier}}",
            methods={"PUT"},
            endpoint=self.put_resource_func(engine),
            response_model=self.aiod_class,  # type: ignore
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
        router.add_api_route(
            path=f"{url_prefix}/platforms/{{platform}}/{self.resource_name_plural}/{version}",
            endpoint=self.list_platform_resources_func(engine),
            response_model=List[self.aiod_class],  # type: ignore
            name=f"List {self.resource_name_plural}",
            **default_kwargs,
        )
        router.add_api_route(
            path=f"{url_prefix}/platforms/{{platform}}/{self.resource_name_plural}/{version}"
            f"/{{identifier}}",
            endpoint=self.get_platform_resource_func(engine),
            response_model=self.aiod_class,  # type: ignore
            name=self.resource_name,
            **default_kwargs,
        )
        return router

    def list_resources_func(self, engine: Engine):
        def list_resources(pagination: Pagination = Depends(Pagination)):
            f"""
            Lists all {self.resource_name_plural} registered with AIoD.

            Query Parameter
            ------
             * platforms, list[str], optional: if provided, list only resources from the given
             platform.
            """
            try:
                with Session(engine) as session:
                    query = select(self.orm_class).offset(pagination.offset).limit(pagination.limit)
                    return self._wrap_with_headers(
                        [
                            self.converter.orm_to_aiod(resource)
                            for resource in session.scalars(query).all()
                        ]
                    )
            except Exception as e:
                raise _wrap_as_http_exception(e)

        return list_resources

    def list_platform_resources_func(self, engine: Engine):
        def list_resources(platform: str, pagination: Pagination = Depends(Pagination)):
            f"""Retrieve all meta-data of the {self.resource_name_plural} of a single platform."""
            try:
                with Session(engine) as session:
                    query = (
                        select(self.orm_class)
                        .where(self.orm_class.platform == platform)
                        .offset(pagination.offset)
                        .limit(pagination.limit)
                    )
                    return self._wrap_with_headers(
                        [
                            self.converter.orm_to_aiod(resource)
                            for resource in session.scalars(query).all()
                        ]
                    )
            except Exception as e:
                raise _wrap_as_http_exception(e)

        return list_resources

    def get_resource_func(self, engine: Engine):
        def get_resource(identifier: str):
            f"""Retrieve all meta-data for a specific {self.resource_name}."""
            try:
                with Session(engine) as session:
                    resource = self._retrieve_resource(session, identifier)
                    aiod_resource = self.converter.orm_to_aiod(resource)
                    return self._wrap_with_headers(aiod_resource)
            except Exception as e:
                raise _wrap_as_http_exception(e)

        return get_resource

    def get_platform_resource_func(self, engine: Engine):
        def get_resource(platform: str, identifier: str):
            f"""Retrieve all meta-data for a specific {self.resource_name} identified by the
            platform-specific-identifier."""
            try:
                with Session(engine) as session:
                    resource = self._retrieve_resource(session, identifier, platform=platform)
                    aiod_resource = self.converter.orm_to_aiod(resource)
                    return self._wrap_with_headers(aiod_resource)
            except Exception as e:
                raise _wrap_as_http_exception(e)

        return get_resource

    def register_resource_func(self, engine: Engine):
        clz = self.aiod_class

        def register_resource(resource: clz):  # type: ignore
            f"""Register a {self.resource_name} with AIoD."""
            try:
                with Session(engine) as session:
                    resource = self.converter.aiod_to_orm(
                        session, resource, return_existing_if_present=False
                    )
                    session.add(resource)
                    try:
                        session.commit()
                    except IntegrityError:
                        session.rollback()
                        query = select(self.orm_class).where(
                            and_(
                                self.orm_class.platform == resource.platform,
                                self.orm_class.platform_identifier == resource.platform_identifier,
                            )
                        )
                        existing_resource = session.scalars(query).first()
                        raise HTTPException(
                            status_code=409,
                            detail=f"There already exists a {self.resource_name} with the same "
                            f"platform and name, with identifier={existing_resource.identifier}.",
                        )

                    aiod_resource = self.converter.orm_to_aiod(resource)
                    return self._wrap_with_headers(aiod_resource)
            except Exception as e:
                raise _wrap_as_http_exception(e)

        return register_resource

    def put_resource_func(self, engine: Engine):
        clz = self.aiod_class

        def put_resource(identifier: str, resource: clz):  # type: ignore
            f"""Update an existing {self.resource_name}."""
            try:
                with Session(engine) as session:
                    self._retrieve_resource(session, identifier)  # Raise error if it does not exist
                    resource_orm = self.converter.aiod_to_orm(
                        session, resource, return_existing_if_present=False
                    )
                    resource_orm.identifier = identifier
                    session.merge(resource_orm)
                    session.commit()
                    new_resource = self._retrieve_resource(session, identifier)
                    converted = self.converter.orm_to_aiod(new_resource)
                    return self._wrap_with_headers(converted)
            except Exception as e:
                raise _wrap_as_http_exception(e)

        return put_resource

    def delete_resource_func(self, engine: Engine):
        def delete_resource(identifier: str):
            try:
                with Session(engine) as session:
                    self._retrieve_resource(session, identifier)  # Raise error if it does not exist
                    statement = delete(self.orm_class).where(
                        self.orm_class.identifier == identifier
                    )
                    session.execute(statement)
                    session.commit()
                return self._wrap_with_headers(None)
            except Exception as e:
                raise _wrap_as_http_exception(e)

        return delete_resource

    def _retrieve_resource(self, session, identifier, platform=None):
        if platform is None:
            query = select(self.orm_class).where(self.orm_class.identifier == identifier)
        else:
            if platform not in {n.name for n in PlatformName}:
                raise HTTPException(
                    status_code=400, detail=f"platform '{platform}' not recognized."
                )
            query = select(self.orm_class).where(
                and_(
                    self.orm_class.platform_identifier == identifier,
                    self.orm_class.platform == platform,
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
            raise HTTPException(status_code=404, detail=msg)
        return resource

    def _wrap_with_headers(self, resource):
        if self.deprecated_from is None:
            return resource
        timestamp = datetime.datetime.combine(
            self.deprecated_from, datetime.time.min, tzinfo=datetime.timezone.utc
        ).timestamp()
        headers = {"Deprecated": format_date_time(timestamp)}
        return JSONResponse(content=jsonable_encoder(resource, exclude_none=True), headers=headers)


def _wrap_as_http_exception(exception: Exception) -> HTTPException:
    if isinstance(exception, HTTPException):
        return exception

    # This is an unexpected error. A mistake on our part. End users should not be informed about
    # details of problems they are not expected to fix, so we give a generic response and log the
    # error.
    traceback.print_exc()
    return HTTPException(
        status_code=500,
        detail=(
            "Unexpected exception while processing your request. Please contact the maintainers."
        ),
    )
