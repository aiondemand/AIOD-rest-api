from sqlmodel import Relationship

from database.model.agent.agent import AgentBase, Agent
from database.model.agent.expertise import Expertise
from database.model.agent.language import Language
from database.model.ai_resource.resource import AIResource
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.helper_functions import link_factory
from database.model.relationships import ResourceRelationshipList
from database.model.serializers import (
    AttributeSerializer,
    FindByNameDeserializer,
    FindByIdentifierDeserializer,
)


class PersonBase(AgentBase):
    pass


class Person(PersonBase, Agent, table=True):  # type: ignore [call-arg]
    __tablename__ = "person"

    expertise: list[Expertise] = Relationship(
        link_model=link_factory("person", Expertise.__tablename__)
    )
    language: list[Language] = Relationship(
        link_model=link_factory("person", Language.__tablename__)
    )
    # TODO(jos): memberOf? This should probably be on Agent

    class RelationshipConfig(Agent.RelationshipConfig):
        expertise: list[str] = ResourceRelationshipList(
            description="A skill this person masters.",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Expertise),
            example=["transfer learning"],
            default_factory_pydantic=list,
        )
        language: list[str] = ResourceRelationshipList(
            description="A language this person masters, in ISO639-3",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Language),
            example=["eng", "fra", "spa"],
            default_factory_pydantic=list,
        )


deserializer = FindByIdentifierDeserializer(Person)
AIResource.RelationshipConfig.contact.deserializer = deserializer  # type: ignore
AIoDEntryORM.RelationshipConfig.editor.deserializer = deserializer  # type: ignore
