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

    @classmethod
    def from_db_model(cls, db_taxonomy: Taxonomy) -> "TaxonomyRead":
        """Create TaxonomyRead from database model.
        
        Note: When migrating to Pydantic v2, this can be replaced with 
        Field(serialization_alias="name") for the term field.
        """
        return cls(term=db_taxonomy.name, definition=db_taxonomy.definition)


class TaxonomyHierarchy(TaxonomyRead):
    subterms: list["TaxonomyHierarchy"] = Field(
        description="Direct subterms of this term.", default_factory=list
    )

    @classmethod
    def from_db_model(cls, db_taxonomy: Taxonomy) -> "TaxonomyHierarchy":
        """Create TaxonomyHierarchy from database model with children.
        
        Note: When migrating to Pydantic v2, this can be replaced with 
        Field(serialization_alias="name") for the term field and automatic
        serialization of nested relationships.
        """
        children = [cls.from_db_model(child) for child in db_taxonomy.children]
        return cls(
            term=db_taxonomy.name, 
            definition=db_taxonomy.definition, 
            subterms=children
        )


class TaxonomyRouter(EnumRouter):
    def __init__(self, resource_class: Type[Taxonomy]):
        super().__init__(resource_class)

    def create(self, url_prefix: str, version: Version = Version.LATEST) -> APIRouter:
        router = APIRouter()
        default_kwargs = {
            "response_model_exclude_none": True,
            "tags": ["Taxonomies"],
            "endpoint": self.get_official_terms_func(),
            "response_model": list[TaxonomyHierarchy],
            "name": self.resource_name,
        }

        new_path = f"/{self.resource_class.__plural__.replace(' ', '_')}"
        router.add_api_route(
            path=new_path,
            description=f"List definitions and descriptions of all valid {self.resource_class.__plural__}.",
            **default_kwargs,
        )
        old_path = f"/{self.resource_name_plural}"
        if version == Version.V2 and old_path != new_path:
            router.add_api_route(
                path=old_path,
                deprecated=True,
                description=(
                    "List definitions and descriptions of all valid "
                    f"{self.resource_class.__plural__}. "
                    f"Deprecated: use `{new_path}` instead."
                ),
                **default_kwargs,
            )
        return router

    def get_official_terms_func(self):
        def get_official():
            with DbSession() as session:
                query = select(self.resource_class)
                resources = session.scalars(query).all()
                # Use the new class method for cleaner, more maintainable code
                # This replaces the manual field mapping and prepares for Pydantic v2 migration
                taxonomies = [
                    TaxonomyHierarchy.from_db_model(term)
                    for term in resources
                    if term.official and term.parent is None
                ]
                return taxonomies

        return get_official
