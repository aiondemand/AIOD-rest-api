from typing import List, Optional
from sqlmodel import Relationship

from database.model.ai_resource.resource import AbstractAIResource, AIResourceBase
from database.model.ai_resource.resource_table import AIResourceORM
from database.model.helper_functions import many_to_many_link_factory
from database.model.resource_bundle.external_resource import ExternalResource

from database.model.relationships import ManyToMany
from database.model.serializers import (
    AttributeSerializer,
    FindByIdentifierDeserializerList,
    FindByNameDeserializerList,
)


class ResourceBundleBase(AIResourceBase):
    """
    A coherent collection of resources intended to be shared as a set
    """

    pass


class ResourceBundle(ResourceBundleBase, AbstractAIResource, table=True):  # type: ignore [call-arg]
    __tablename__ = "resource_bundle"

    # Many-to-Many relationship linking ResourceBundle to external resources (URLs)
    includes_external_resource: List[ExternalResource] = Relationship(
        link_model=many_to_many_link_factory("resource_bundle", ExternalResource.__tablename__)
    )

    # A list of AIResources that form part of this bundle
    includes_resources: List[AIResourceORM] = Relationship(
        link_model=many_to_many_link_factory("resource_bundle", AIResourceORM.__tablename__)
    )

    class RelationshipConfig(AbstractAIResource.RelationshipConfig):
        includes_external_resource: List[str] = ManyToMany(
            description="External resources (URLs) not in AIoD.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(ExternalResource),
            default_factory_pydantic=list,
        )

        includes_resources: List[int] = ManyToMany(
            description="AIResources included in this bundle.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(AIResourceORM),
            default_factory_pydantic=list,
        )
