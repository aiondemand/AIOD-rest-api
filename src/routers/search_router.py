import os
from typing import TypeVar, Generic, Any, Type

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.engine import Engine
from starlette import status

from authentication import get_current_user, has_role
from database.model.concept.aiod_entry import AIoDEntryRead
from database.model.knowledge_asset.publication import Publication
from database.model.resource_read_and_create import resource_read
from routers.router import AIoDRouter

SORT = {"identifier": "asc"}
LIMIT_MAX = 1000

RESOURCE = TypeVar("RESOURCE")


class SearchResult(BaseModel, Generic[RESOURCE]):
    total_hits: int
    resources: list[RESOURCE]
    next_offset: list | None


class SearchRouter(AIoDRouter):
    def __init__(self):
        self.client: Elasticsearch | None = None

    def create(self, engine: Engine, url_prefix: str) -> APIRouter:
        router = APIRouter()
        user_name = os.getenv("ES_USER")
        pw = os.getenv("ES_PASSWORD")
        self.client = Elasticsearch("http://localhost:9200", basic_auth=(user_name, pw))

        publication_class = resource_read(Publication)

        @router.get(url_prefix + "/search/publications/v1", tags=["search"])
        def search_publication(
            name: str = "",
            limit: int = 10,
            offset: str | None = None,  # TODO: this should not be a string
            user: dict = Depends(get_current_user),
        ) -> SearchResult[publication_class]:  # type: ignore
            if limit > LIMIT_MAX:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The limit should be maximum {LIMIT_MAX}. If you want more results, "
                    f"use pagination.",
                )

            if not has_role(user, os.getenv("ES_ROLE")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to search Aiod resources.",
                )
            if self.client is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Client not initialized",
                )
            query = {"bool": {"must": {"match": {"name": name}}}}
            result = self.client.search(
                index="publication", query=query, size=limit, sort=SORT, search_after=offset
            )

            total_hits = result["hits"]["total"]["value"]
            resources: list[publication_class] = [  # type: ignore
                _cast_resource(
                    publication_class, hit["_source"], key_translations={"publication_type": "type"}
                )
                for hit in result["hits"]["hits"]
            ]
            next_offset = (
                result["hits"]["hits"][-1]["sort"] if len(result["hits"]["hits"]) > 0 else None
            )
            return SearchResult[publication_class](  # type: ignore
                total_hits=total_hits,
                next_offset=next_offset,
                resources=resources,
            )

        return router


def _cast_resource(
    resource_class: RESOURCE, resource_dict: dict[str, Any], key_translations: dict[str, str]
) -> Type[RESOURCE]:
    kwargs = {
        key_translations.get(key, key): val
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
