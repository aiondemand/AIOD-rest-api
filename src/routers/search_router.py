import abc
from typing import TypeVar, Generic, Any, Type, Annotated

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.engine import Engine
from sqlmodel import Session, select
from starlette import status

from authentication import get_current_user#, has_role
from database.model.concept.aiod_entry import AIoDEntryRead
from database.model.resource_read_and_create import resource_read
from database.model.platform.platform import Platform
from .resource_router import _wrap_as_http_exception

SORT = {"identifier": "asc"}
LIMIT_MAX = 1000

RESOURCE = TypeVar("RESOURCE")


class SearchResult(BaseModel, Generic[RESOURCE]):
    total_hits: int
    resources: list[RESOURCE]
    next_offset: list | None
    current_page: int
    page_size: int

class SearchRouter(Generic[RESOURCE], abc.ABC):
    """
    Providing search functionality in ElasticSearch
    """
    
    def __init__(self, client: Elasticsearch):
        self.client: Elasticsearch = client
    
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
    def match_fields(self) -> set:
        """The set of indexed fields"""
    
    def create(self, engine: Engine, url_prefix: str) -> APIRouter:
        router = APIRouter()
        read_class = resource_read(self.resource_class)  # type: ignore
        
        @router.get(f"{url_prefix}/search/{self.resource_name_plural}/v1",
                    tags=["search"])
        def search(
            platforms: Annotated[list[str] | None, Query()] = None,
            search_query: str = "",
            search_fields: Annotated[list[str] | None, Query()] = None,
            limit: int = 10,
            page: int = 1
#            offset: Annotated[list[str] | None, Query()] = None
        ) -> SearchResult[read_class]:  # type: ignore
            f"""
            Search for {self.resource_name_plural}.
            """
            
            # Parameter correctness
            # -----------------------------------------------------------------
            
            try:
                with Session(engine) as session:
                    query = select(Platform)
                    database_platforms = session.scalars(query).all()
                    platform_names = set([p.name for p in database_platforms])
            except Exception as e:
                raise _wrap_as_http_exception(e)
            
            if platforms and not set(platforms).issubset(platform_names):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The available platformas are: {platform_names}"
                )
            
            fields = search_fields if search_fields else self.match_fields
            if not set(fields).issubset(self.match_fields):
                raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"The available search fields for this entity "
                               f"are: {self.match_fields}"
                        )
            
            if limit > LIMIT_MAX:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The limit should be maximum {LIMIT_MAX}. "
                           f"If you want more results, use pagination."
                )
            
            if page < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The page numbers start by 1."
                )
            
            # Prepare query
            # -----------------------------------------------------------------
            
            # Matches of the search concept for each field
            query_matches = [{'match': {f: search_query}} for f in fields]
            
            # Must match search concept on at least one field
            query = {
                'bool': {
                    'should': query_matches,
                    'minimum_should_match': 1
                }
            }
            if platforms:
                
                # Matches of the platform field for each selected platform
                platform_matches = [{'match': {'platform': p}}
                                    for p in platforms]
                
                # Must match platform and search query on at least one field
                query['bool']['must'] = {'bool': {'should': platform_matches,
                                                  'minimum_should_match': 1}}
            
            # Launch search query
            # -----------------------------------------------------------------
            
            from_ = limit*(page - 1)
            result = self.client.search(index=self.es_index, query=query,
                                        from_=from_, size=limit, sort=SORT)
            
            # Launch database query
            # -----------------------------------------------------------------
            
            try:
                with Session(engine) as session:
                    query = select(Platform)
                    database_platforms = session.scalars(query).all()
                    platform_names = set([p.name for p in database_platforms])
            except Exception as e:
                raise _wrap_as_http_exception(e)
            
            # Manage results
            # -----------------------------------------------------------------
            
            total_hits = result["hits"]["total"]["value"]
            resources: list[read_class] = [  # type: ignore
                self._cast_resource(read_class, hit["_source"])  # type: ignore
                for hit in result["hits"]["hits"]
            ]
            next_offset = (
                result["hits"]["hits"][-1]["sort"]
                if len(result["hits"]["hits"]) > 0 else None
            )
            return SearchResult[read_class](  # type: ignore
                total_hits=total_hits,
                resources=resources,
                next_offset=next_offset,
                current_page=page,
                page_size=limit
            )
        
        return router
    
    def _cast_resource(
        self, resource_class: RESOURCE, resource_dict: dict[str, Any]
    ) -> Type[RESOURCE]:
        kwargs = {
            self.key_translations.get(key, key): val
            for key, val in resource_dict.items()
            if key != "type" and not key.startswith("@")
        }
        resource = resource_class(**kwargs)  # type: ignore
        resource.aiod_entry = AIoDEntryRead(
            date_modified=resource_dict["date_modified"],
#            date_created=resource_dict["date_created"],
#            status=resource_dict["status"],
        )
        return resource
