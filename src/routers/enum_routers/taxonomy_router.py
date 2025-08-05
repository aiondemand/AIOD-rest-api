from typing import Type, Union

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from database.model.named_relation import Taxonomy
from routers.enum_routers.enum_router import EnumRouter
from database.session import DbSession
from versioning import Version


class TaxonomyRead(BaseModel):
    term: str = Field(description="A short, unique name for the term.")
    definition: str = Field(description="The definition of the term.")


class TaxonomyHierarchy(TaxonomyRead):
    subterms: list["TaxonomyHierarchy"] = Field(
        description="Direct subterms of this term.", default_factory=list
    )


class TaxonomyRouter(EnumRouter):
    def __init__(self, resource_class: Type[Taxonomy]):
        super().__init__(resource_class)

    def create(self, url_prefix: str, version: Version = Version.LATEST) -> APIRouter:
        router = APIRouter()
        default_kwargs = {
            "response_model_exclude_none": True,
            "tags": ["Taxonomies"],
        }

        router.add_api_route(
            path=f"/{self.resource_name_plural}",
            endpoint=self.get_official_terms_func(),
            response_model=list[TaxonomyHierarchy],
            name=self.resource_name,
            **default_kwargs,
        )
        return router

    def get_official_terms_func(self):
        def create_hierarchical_representation(term):
            children = [create_hierarchical_representation(t) for t in term.children]
            return TaxonomyHierarchy(term=term.name, definition=term.definition, subterms=children)

        def get_official():
            with DbSession() as session:
                query = select(self.resource_class)
                resources = session.scalars(query).all()
                # TODO: With Pydantic V2 this can be 'automatic' by using `serialization_alias`
                taxonomies = [
                    create_hierarchical_representation(term)
                    for term in resources
                    if term.official and term.parent is None
                ]
                return taxonomies

        return get_official
