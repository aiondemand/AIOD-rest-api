import abc
import os
from typing import TypeVar, Generic, Any, Type, Annotated

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.engine import Engine
from starlette import status

from authentication import get_current_user#, has_role
from database.model.concept.aiod_entry import AIoDEntryRead
from database.model.resource_read_and_create import resource_read

SORT = {"identifier": "asc"}
LIMIT_MAX = 1000

RESOURCE = TypeVar("RESOURCE")


class SearchResult(BaseModel, Generic[RESOURCE]):
    total_hits: int
    resources: list[RESOURCE]
    next_offset: list | None


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
    
    def create(self, engine: Engine, url_prefix: str) -> APIRouter:
        router = APIRouter()
        read_class = resource_read(self.resource_class)  # type: ignore
        
        # TODO: check parameters correctness
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
            
            if limit > LIMIT_MAX:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The limit should be maximum {LIMIT_MAX}. "
                           f"If you want more results, use pagination."
                )
            
            # Prepare query
            # -----------------------------------------------------------------
            
            # Matches of the search concept for each field
            if search_fields:
                
                # The selected fields must be present in the match fields
                if not set(search_fields).issubset(set(self.match_fields)):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"The available search fields for this entity "
                               f"are:{self.match_fields}"
                    )
                
                # Search in specific search fields
                query_matches = [{'match': {f: search_query}}
                                 for f in search_fields]
            
            else:
                
                # Search in any match field
                query_matches = [{'match': {f: search_query}}
                                 for f in self.match_fields]
            
            if platforms:
                
                # Matches of the platform field for each selected platform
                platform_matches = [{'match': {'platform': p}}
                                    for p in platforms]
                
                # Must match platform and search query on at least one field
                query = {
                    'bool': {
                        'must': {
                            'bool': {
                                'should': platform_matches,
                                'minimum_should_match': 1
                            }
                        },
                        'should': query_matches,
                        'minimum_should_match': 1
                    }
                }
            
            else:
                
                # Must match search concept on at least one field
                query = {
                    'bool': {
                        'should': query_matches,
                        'minimum_should_match': 1
                    }
                }
            
            # -----------------------------------------------------------------
            
#            result = self.client.search(index=self.es_index, query=query,
#                                        size=limit, sort=SORT,
#                                        search_after=offset)
            from_ = limit*(page - 1)
            result = self.client.search(index=self.es_index, query=query,
                                        from_=from_, size=limit, sort=SORT)
            
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
                next_offset=next_offset,
                resources=resources
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
            date_created=resource_dict["date_created"],
            status=resource_dict["status"],
        )
        return resource
