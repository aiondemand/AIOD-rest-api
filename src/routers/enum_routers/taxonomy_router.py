from typing import Type

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from database.model.named_relation import Taxonomy
from routers.enum_routers.enum_router import EnumRouter
from database.session import DbSession


class TaxonomyRead(BaseModel):
    term: str = Field(description="A short, unique name for the term.")
    definition: str = Field(description="The definition of the term.")


class TaxonomyRouter(EnumRouter):
    def __init__(self, resource_class: Type[Taxonomy]):
        super().__init__(resource_class)

    def create(self, url_prefix: str) -> APIRouter:
        router = APIRouter()
        default_kwargs = {
            "response_model_exclude_none": True,
            "tags": ["Taxonomies"],
        }

        for path in [
            url_prefix + f"/v2/{self.resource_name_plural}",
            url_prefix + f"/{self.resource_name_plural}",
        ]:
            router.add_api_route(
                path=path,
                endpoint=self.get_official_terms_func(),
                response_model=list[TaxonomyRead],
                name=self.resource_name,
                **default_kwargs,
            )
        return router

    def get_official_terms_func(self):
        def get_official():
            with DbSession() as session:
                query = select(self.resource_class)
                resources = session.scalars(query).all()
                # TODO: With Pydantic V2 this can be 'automatic' by using `serialization_alias`
                return (
                    TaxonomyRead(term=term.name, definition=term.description)
                    for term in resources
                    if term.official
                )

        return get_official
