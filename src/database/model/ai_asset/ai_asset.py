import abc
import copy
from datetime import datetime
from typing import Optional, Any
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from database.model.agent.person import Person
from database.model.ai_asset.ai_asset_table import AIAssetTable
from database.model.ai_asset.distribution import Distribution, distribution_factory
from database.model.ai_asset.license import License
from database.model.ai_resource.resource import AIResourceBase, AIResource
from database.model.field_length import NORMAL
from database.model.helper_functions import many_to_many_link_factory
from database.model.models_and_experiments.runnable_distribution import (
    runnable_distribution_factory,
)
from database.model.relationships import OneToMany, ManyToOne, ManyToMany, OneToOne
from database.model.serializers import (
    AttributeSerializer,
    CastDeserializer,
    FindByNameDeserializer,
    FindByIdentifierDeserializer,
)

if TYPE_CHECKING:
    from database.model.knowledge_asset.publication import Publication


class AIAssetBase(AIResourceBase, metaclass=abc.ABCMeta):
    date_published: datetime | None = Field(
        description="The datetime (utc) on which this AIAsset was first published on an external "
        "platform. ",
        default=None,
        schema_extra={"example": "2022-01-01T15:15:00.000"},
    )
    is_accessible_for_free: bool = Field(
        description="A flag to signal that this asset is accessible at no cost.", default=True
    )
    version: str | None = Field(
        description="The version of this asset.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "1.1.0"},
    )


class AIAsset(AIAssetBase, AIResource, metaclass=abc.ABCMeta):
    ai_asset_id: int | None = Field(
        foreign_key=AIAssetTable.__tablename__ + ".identifier", index=True
    )
    ai_asset_identifier: AIAssetTable | None = Relationship()

    citation: list["Publication"] = Relationship()
    distribution: list = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})
    license_identifier: int | None = Field(foreign_key=License.__tablename__ + ".identifier")
    license: Optional[License] = Relationship()
    creator: list["Person"] = Relationship()

    def __init_subclass__(cls):
        """
        Fixing problems with the inheritance of relationships, and creating linking tables.
        The latter cannot be done in the class variables, because it depends on the table-name of
        the child class.
        """
        cls.__annotations__.update(AIAsset.__annotations__)
        relationships = copy.deepcopy(AIAsset.__sqlmodel_relationships__)
        is_not_abstract = cls.__tablename__ != "knowledgeasset"
        if is_not_abstract:
            cls.update_relationships_asset(relationships)
        cls.__sqlmodel_relationships__.update(relationships)

    class RelationshipConfig(AIResource.RelationshipConfig):
        ai_asset_identifier: int | None = OneToOne(
            identifier_name="ai_asset_id",
            serializer=AttributeSerializer("identifier"),
            include_in_create=False,
            default_factory_orm=lambda type_: AIAssetTable(type=type_),
            on_delete_trigger_deletion_by="ai_asset_id",
        )
        distribution: list[Distribution] = OneToMany(default_factory_pydantic=list)
        license: Optional[str] = ManyToOne(
            identifier_name="license_identifier",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(License),
            example="https://creativecommons.org/share-your-work/public-domain/cc0/",
        )
        citation: list[int] = ManyToMany(
            description="A bibliographic reference.",
            serializer=AttributeSerializer("identifier"),
            default_factory_pydantic=list,
            example=[],
        )
        creator: list[int] = ManyToMany(
            description="Links to identifiers of the persons that created this asset.",
            serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializer(Person),
            default_factory_pydantic=list,
            example=[],
        )

    @classmethod
    def update_relationships_asset(cls, relationships: dict):
        cls.update_relationships(relationships)

        factory = (
            distribution_factory
            if cls.__tablename__ not in ("ml_model", "experiment")
            else runnable_distribution_factory
        )
        distribution: Any = factory(table_from=cls.__tablename__)
        cls.__annotations__["distribution"] = list[distribution]
        cls.RelationshipConfig.distribution = copy.copy(AIAsset.RelationshipConfig.distribution)
        deserializer = CastDeserializer(distribution)
        cls.RelationshipConfig.distribution.deserializer = deserializer  # type: ignore

        relationships["creator"].link_model = many_to_many_link_factory(
            table_from=cls.__tablename__,
            table_to="person",
            table_prefix="creator",
        )
        relationships["citation"].link_model = many_to_many_link_factory(
            table_from=cls.__tablename__,
            table_to="publication",
            table_prefix="citation",
        )
        if cls.__tablename__ == "publication":

            def get_identifier():
                from database.model.knowledge_asset.publication import Publication

                return Publication.identifier

            relationships["citation"].sa_relationship_kwargs = dict(
                primaryjoin=lambda: get_identifier()
                == relationships["citation"].link_model.from_identifier,
                secondaryjoin=lambda: get_identifier()
                == relationships["citation"].link_model.linked_identifier,
            )
