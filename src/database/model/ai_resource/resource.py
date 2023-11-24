"""
Abstract classes that need to be inherited by all AIResources.
Not to be confused with the AIResourceORM, AIResourceRead and AIResourceCreate which are the
AIResource tables in the database, creating an ai_resource_identifier for every AIResource and
defining relationships between AIResources.
"""

import abc
import copy
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Field, Relationship

from database.model.agent.contact import Contact
from database.model.ai_asset.distribution import Distribution, distribution_factory
from database.model.ai_resource.alternate_name import AlternateName
from database.model.ai_resource.application_area import ApplicationArea
from database.model.ai_resource.industrial_sector import IndustrialSector
from database.model.ai_resource.keyword import Keyword
from database.model.ai_resource.note import note_factory, Note
from database.model.ai_resource.relevantlink import RelevantLink
from database.model.ai_resource.research_area import ResearchArea
from database.model.ai_resource.resource_table import AIResourceORM
from database.model.ai_resource.scientific_domain import ScientificDomain
from database.model.ai_resource.text import TextORM, Text
from database.model.concept.concept import AIoDConceptBase, AIoDConcept
from database.model.field_length import NORMAL
from database.model.helper_functions import many_to_many_link_factory, non_abstract_subclasses
from database.model.relationships import OneToMany, OneToOne, ManyToMany
from database.model.serializers import (
    AttributeSerializer,
    CastDeserializer,
    CastDeserializerList,
    FindByIdentifierDeserializerList,
    FindByNameDeserializerList,
)


class AIResourceBase(AIoDConceptBase, metaclass=abc.ABCMeta):
    name: str = Field(max_length=NORMAL, schema_extra={"example": "The name of this resource"})
    date_published: datetime | None = Field(
        description="The datetime (utc) on which this resource was first published on an external "
        "platform. Note the difference between `.aiod_entry.date_created` and "
        "`.date_published`: the former is automatically set to the datetime the "
        "resource was created on AIoD, while the latter can optionally be set to an "
        "earlier datetime that the resource was published on an external platform.",
        default=None,
        schema_extra={"example": "2022-01-01T15:15:00.000"},
    )
    same_as: str | None = Field(
        description="Url of a reference Web page that unambiguously indicates this resource's "
        "identity.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "https://www.example.com/resource/this_resource"},
    )


class AbstractAIResource(AIResourceBase, AIoDConcept, metaclass=abc.ABCMeta):
    ai_resource_id: int | None = Field(
        foreign_key="ai_resource.identifier", index=True, unique=True
    )
    ai_resource_identifier: AIResourceORM | None = Relationship()

    description_identifier: int | None = Field(index=True, foreign_key="text.identifier")
    description: TextORM | None = Relationship()

    alternate_name: list[AlternateName] = Relationship()
    keyword: list[Keyword] = Relationship()
    relevant_link: list[RelevantLink] = Relationship()

    application_area: list[ApplicationArea] = Relationship()
    industrial_sector: list[IndustrialSector] = Relationship()
    research_area: list[ResearchArea] = Relationship()
    scientific_domain: list[ScientificDomain] = Relationship()

    contact: list[Contact] = Relationship()
    creator: list[Contact] = Relationship()

    media: list = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})
    note: list = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})

    def __init_subclass__(cls):
        """
        Fixing problems with the inheritance of relationships, and creating linking tables.
        The latter cannot be done in the class variables, because it depends on the table-name of
        the child class.
        """
        cls.__annotations__.update(AbstractAIResource.__annotations__)
        relationships = copy.deepcopy(AbstractAIResource.__sqlmodel_relationships__)
        is_not_abstract = cls.__tablename__ not in ("aiasset", "agent", "knowledgeasset")
        if is_not_abstract:
            cls.update_relationships(relationships)
        cls.__sqlmodel_relationships__.update(relationships)

    class RelationshipConfig(AIoDConcept.RelationshipConfig):
        ai_resource_identifier: int | None = OneToOne(
            description="This resource can be identified by its own identifier, but also by the "
            "resource_identifier.",
            identifier_name="ai_resource_id",
            _serializer=AttributeSerializer("identifier"),
            include_in_create=False,
            default_factory_orm=lambda type_: AIResourceORM(type=type_),
            on_delete_trigger_deletion_by="ai_resource_id",
        )
        description: Optional[Text] = OneToOne(
            deserializer=CastDeserializer(TextORM),
            on_delete_trigger_deletion_by="description_identifier",
        )
        alternate_name: list[str] = ManyToMany(
            description="An alias for the item, commonly used for the resource instead of the "
            "name.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(AlternateName),
            example=["alias 1", "alias 2"],
            default_factory_pydantic=list,
            on_delete_trigger_orphan_deletion=lambda: [
                f"{a.__tablename__}_alternate_name_link"
                for a in non_abstract_subclasses(AbstractAIResource)
            ],
        )
        keyword: list[str] = ManyToMany(
            description="Keywords or tags used to describe this resource, providing additional "
            "context.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(Keyword),
            example=["keyword1", "keyword2"],
            default_factory_pydantic=list,
            on_delete_trigger_orphan_deletion=lambda: [
                f"{a.__tablename__}_keyword_link"
                for a in non_abstract_subclasses(AbstractAIResource)
            ],
        )
        relevant_link: list[str] = ManyToMany(
            description="URLs of relevant resources. These resources should not be part of AIoD ("
            "use relevant_resource otherwise). This field should only be used if there "
            "is no more specific field.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(RelevantLink),
            example=[
                "https://www.example.com/a_relevant_link",
                "https://www.example.com/another_relevant_link",
            ],
            default_factory_pydantic=list,
            on_delete_trigger_orphan_deletion=lambda: [
                f"{a.__tablename__}_relevant_link_link"
                for a in non_abstract_subclasses(AbstractAIResource)
            ],
        )
        application_area: list[str] = ManyToMany(
            description="The objective of this AI resource.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(ApplicationArea),
            example=["Fraud Prevention", "Voice Assistance", "Disease Classification"],
            default_factory_pydantic=list,
        )
        industrial_sector: list[str] = ManyToMany(
            description="A business domain where a resource is or can be used.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(IndustrialSector),
            example=["Finance", "eCommerce", "Healthcare"],
            default_factory_pydantic=list,
        )
        research_area: list[str] = ManyToMany(
            description="The research area is similar to the scientific_domain, but more "
            "high-level.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(ResearchArea),
            example=["Explainable AI", "Physical AI"],
            default_factory_pydantic=list,
        )
        scientific_domain: list[str] = ManyToMany(
            description="The scientific domain is related to the methods with which an objective "
            "is reached.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(ScientificDomain),
            example=["Anomaly Detection", "Voice Recognition", "Computer Vision."],
            default_factory_pydantic=list,
        )
        # TODO(jos): documentedIn - KnowledgeAsset. This should probably be defined on ResourceTable
        contact: list[int] = ManyToMany(
            description="Contact information of persons/organisations that can be contacted about "
            "this resource.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(Contact),
            default_factory_pydantic=list,
        )
        creator: list[int] = ManyToMany(
            description="Contact information of persons/organisations that created this resource.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(Contact),
            default_factory_pydantic=list,
        )
        media: list[Distribution] = OneToMany(
            description="Images or videos depicting the resource or associated with it. ",
            default_factory_pydantic=list,  # no deletion trigger: cascading delete is used
        )
        note: list[Note] = OneToMany(
            description="Notes on this AI resource.",
            default_factory_pydantic=list,  # no deletion trigger: cascading delete is used
        )

        is_part_of: list[int] = ManyToMany(
            default_factory_pydantic=list,
            deserializer=FindByIdentifierDeserializerList(AIResourceORM),
            _serializer=AttributeSerializer("identifier"),
            deserialized_path="ai_resource_identifier",
        )
        has_part: list[int] = ManyToMany(
            default_factory_pydantic=list,
            deserializer=FindByIdentifierDeserializerList(AIResourceORM),
            _serializer=AttributeSerializer("identifier"),
            deserialized_path="ai_resource_identifier",
        )
        relevant_resource: list[int] = ManyToMany(
            default_factory_pydantic=list,
            deserializer=FindByIdentifierDeserializerList(AIResourceORM),
            _serializer=AttributeSerializer("identifier"),
            deserialized_path="ai_resource_identifier",
        )
        relevant_to: list[int] = ManyToMany(
            default_factory_pydantic=list,
            deserializer=FindByIdentifierDeserializerList(AIResourceORM),
            _serializer=AttributeSerializer("identifier"),
            deserialized_path="ai_resource_identifier",
        )

    @classmethod
    def update_relationships(cls, relationships: dict[str, Any]):
        distribution: Any = distribution_factory(
            table_from=cls.__tablename__, distribution_name="media"
        )
        cls.__annotations__["media"] = list[distribution]
        cls.RelationshipConfig.media = copy.copy(cls.RelationshipConfig.media)
        distribution_deserializer = CastDeserializerList(distribution)
        cls.RelationshipConfig.media.deserializer = distribution_deserializer  # type: ignore

        note: Any = note_factory(table_from=cls.__tablename__)
        cls.__annotations__["note"] = list[note]
        cls.RelationshipConfig.note = copy.copy(cls.RelationshipConfig.note)
        cls.RelationshipConfig.note.deserializer = CastDeserializerList(note)  # type: ignore

        for table_to in (
            "alternate_name",
            "keyword",
            "relevant_link",
            "application_area",
            "industrial_sector",
            "research_area",
            "scientific_domain",
        ):
            relationships[table_to].link_model = many_to_many_link_factory(
                table_from=cls.__tablename__, table_to=table_to
            )

        link_model_contact = many_to_many_link_factory(
            table_from=cls.__tablename__,
            table_to=Contact.__tablename__,
            table_prefix="contact",
        )
        link_model_creator = many_to_many_link_factory(
            table_from=cls.__tablename__,
            table_to=Contact.__tablename__,
            table_prefix="creator",
        )
        relationships["contact"].link_model = link_model_contact
        relationships["creator"].link_model = link_model_creator

        relationships["description"].sa_relationship_kwargs = dict(
            foreign_keys=f"[{cls.__name__}.description_identifier]"
        )
