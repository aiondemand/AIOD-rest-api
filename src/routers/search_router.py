import abc
from typing import TypeVar, Generic, Any, Type, Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import SQLModel, select
from starlette import status

from database.model.concept.aiod_entry import AIoDEntryRead
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform import Platform
from database.model.resource_read_and_create import resource_read
from database.session import DbSession
from .resource_router import _wrap_as_http_exception
from .search_routers.elasticsearch import ElasticsearchSingleton

SORT = {"identifier": "asc"}
LIMIT_MAX = 1000

RESOURCE = TypeVar("RESOURCE", bound=AIoDConcept)


class SearchResult(BaseModel, Generic[RESOURCE]):
    total_hits: int
    resources: list
    limit: int
    offset: int


class SearchRouter(Generic[RESOURCE], abc.ABC):
    """
    Providing search functionality in ElasticSearch
    """

    @property
    @abc.abstractmethod
    def es_index(self) -> str:
        """The name of the elasticsearch index"""

    @property
    @abc.abstractmethod
    def resource_name_plural(self) -> str:
        """The name of the resource (plural)"""

    @property
    def key_translations(self) -> dict[str, str]:
        """If an attribute is called differently in elasticsearch than in our
        metadata model, you can define a translation dictionary here. The key
        should be the name in elasticsearch, the value the name in our data
        model."""
        return {}

    @property
    @abc.abstractmethod
    def resource_class(self) -> RESOURCE:
        """The resource class"""

    @property
    @abc.abstractmethod
    def indexed_fields(self) -> set[str]:
        """The set of indexed fields"""

    def create(self, url_prefix: str) -> APIRouter:
        router = APIRouter()
        read_class = resource_read(self.resource_class)  # type: ignore

        @router.get(f"{url_prefix}/search/{self.resource_name_plural}/v1", tags=["search"])
        def search(
            platforms: Annotated[list[str] | None, Query()] = None,
            search_query: str = "",
            search_fields: Annotated[list[str] | None, Query()] = None,
            limit: Annotated[int | None, Query(ge=1, le=LIMIT_MAX)] = 10,
            offset: Annotated[int | None, Query(ge=0)] = 0,
            get_all: bool = True,
        ) -> SearchResult[read_class]:  # type: ignore
            f"""
            Search for {self.resource_name_plural}.
            """
            try:
                with DbSession() as session:
                    query = select(Platform)
                    database_platforms = session.scalars(query).all()
                    platform_names = {p.name for p in database_platforms}
            except Exception as e:
                raise _wrap_as_http_exception(e)

            if platforms and not set(platforms).issubset(platform_names):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The available platforms are: {platform_names}",
                )
            fields = search_fields if search_fields else self.indexed_fields
            if not set(fields).issubset(self.indexed_fields):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The available search fields for this entity "
                    f"are: {self.indexed_fields}",
                )
            query_matches = [{"match": {f: search_query}} for f in fields]
            query = {"bool": {"should": query_matches, "minimum_should_match": 1}}
            if platforms:
                platform_matches = [{"match": {"platform": p}} for p in platforms]
                query["bool"]["must"] = {
                    "bool": {"should": platform_matches, "minimum_should_match": 1}
                }
            result = ElasticsearchSingleton().client.search(
                index=self.es_index, query=query, from_=offset, size=limit, sort=SORT
            )
            total_hits = result["hits"]["total"]["value"]
            if get_all:
                resources: list[SQLModel] = [
                    self._db_query(read_class, self.resource_class, hit["_source"]["identifier"])
                    for hit in result["hits"]["hits"]
                ]
            else:
                resources: list[Type[RESOURCE]] = [  # type: ignore
                    self._cast_resource(read_class, hit["_source"])
                    for hit in result["hits"]["hits"]
                ]
            return SearchResult[RESOURCE](  # type: ignore
                total_hits=total_hits,
                resources=resources,
                limit=limit,
                offset=offset,
            )

        return router

    def _db_query(
        self,
        read_class: Type[SQLModel],
        resource_class: RESOURCE,
        identifier: int,
    ) -> SQLModel:
        try:
            with DbSession() as session:
                query = select(resource_class).where(resource_class.identifier == identifier)
                resource = session.scalars(query).first()
                if not resource:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Resource not found in the database.",
                    )
                return read_class.from_orm(resource)
        except Exception as e:
            raise _wrap_as_http_exception(e)

    def _cast_resource(
        self, read_class: Type[SQLModel], resource_dict: dict[str, Any]
    ) -> Type[RESOURCE]:
        kwargs = {
            self.key_translations.get(key, key): val
            for key, val in resource_dict.items()
            if key != "type" and not key.startswith("@")
        }
        resource = read_class(**kwargs)
        resource.aiod_entry = AIoDEntryRead(
            date_modified=resource_dict["date_modified"], status=None
        )
        resource.description = {"plain": resource_dict["plain"], "html": resource_dict["html"]}
        return resource
