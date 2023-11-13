from typing import Optional

from pydantic import condecimal
from sqlmodel import Relationship, Field

from database.model.agent.agent import AgentBase, Agent
from database.model.agent.contact import Contact
from database.model.agent.expertise import Expertise
from database.model.agent.language import Language
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.field_length import NORMAL
from database.model.helper_functions import many_to_many_link_factory
from database.model.relationships import ManyToMany, OneToOne
from database.model.serializers import (
    AttributeSerializer,
    FindByNameDeserializer,
    FindByIdentifierDeserializer,
)


class PersonBase(AgentBase):
    given_name: str | None = Field(
        description="Also known as forename or first name. The part of the personal name that "
        "identifies a person, potentially with a middle name as well.",
        max_length=NORMAL,
        schema_extra={"example": "Jane"},
    )
    surname: str | None = Field(
        description="Also known as last name or family name. The mostly hereditary part of the "
        "personal name.",
        max_length=NORMAL,
        schema_extra={"example": "Doe"},
    )
    price_per_hour_euro: condecimal(max_digits=4, decimal_places=2) | None = Field(  # type: ignore
        description="A ballpark figure of the per hour cost to hire this person.",
        schema_extra={"example": 75.50},
        default=None,
    )
    wants_to_be_contacted: bool = Field(
        description="Does this person want to be contacted about new opportunities relating their "
        "expertise?",
        default=False,
    )


class Person(PersonBase, Agent, table=True):  # type: ignore [call-arg]
    __tablename__ = "person"

    expertise: list[Expertise] = Relationship(
        link_model=many_to_many_link_factory("person", Expertise.__tablename__)
    )
    language: list[Language] = Relationship(
        link_model=many_to_many_link_factory("person", Language.__tablename__)
    )
    contact_details: Optional[Contact] = Relationship(sa_relationship_kwargs={"uselist": False})
    # TODO(jos): memberOf? This should probably be on Agent

    class RelationshipConfig(Agent.RelationshipConfig):
        contact_details: int | None = OneToOne(
            description="The contact details by which this person can be reached",
            deserializer=FindByIdentifierDeserializer(Contact),
            _serializer=AttributeSerializer("identifier"),
        )
        expertise: list[str] = ManyToMany(
            description="A skill this person masters.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Expertise),
            example=["transfer learning"],
            default_factory_pydantic=list,
            on_delete_trigger_orphan_deletion=list,
        )
        language: list[str] = ManyToMany(
            description="A language this person masters, in ISO639-3",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Language),
            example=["eng", "fra", "spa"],
            default_factory_pydantic=list,
        )


deserializer = FindByIdentifierDeserializer(Person)
AIoDEntryORM.RelationshipConfig.editor.deserializer = deserializer  # type: ignore
Contact.RelationshipConfig.person.deserializer = deserializer  # type: ignore
