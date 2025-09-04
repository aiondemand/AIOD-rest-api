from typing import Optional

from pydantic import condecimal
from sqlmodel import Relationship, Field

from database.model.agent.agent import AgentBase, Agent
from database.model.agent.contact import Contact
from database.model.agent.expertise import Expertise
from database.model.agent.language import Language
from database.model.agent.organisation import Organisation
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.field_length import NORMAL
from database.model.helper_functions import many_to_many_link_factory
from database.model.relationships import ManyToMany, OneToOne
from database.model.serializers import (
    AttributeSerializer,
    FindByIdentifierDeserializer,
    FindByIdentifierDeserializerList,
    FindByNameDeserializerList,
)
from versioning import Version, VersionedResource, VersionedResourceCollection


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
    __abbreviation__ = "prsn"
    __plural__ = "persons"

    expertise: list[Expertise] = Relationship(
        link_model=many_to_many_link_factory(
            "person", Expertise.__tablename__, from_identifier_type=str
        )
    )
    languages: list[Language] = Relationship(
        link_model=many_to_many_link_factory(
            "person", Language.__tablename__, from_identifier_type=str
        )
    )
    contact_details: Optional[Contact] = Relationship(sa_relationship_kwargs={"uselist": False})

    member_of: list[Organisation] = Relationship(
        link_model=many_to_many_link_factory(
            "person", Organisation.__tablename__, from_identifier_type=str, to_identifier_type=str
        )
    )

    class RelationshipConfig(Agent.RelationshipConfig):
        contact_details: str | None = OneToOne(
            description="The identifier of the contact details by which this person can be reached",
            deserializer=FindByIdentifierDeserializer(Contact),
            _serializer=AttributeSerializer("identifier"),
        )
        expertise: list[str] = ManyToMany(
            description="A skill this person masters.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(Expertise),
            example=["transfer learning"],
            default_factory_pydantic=list,
            on_delete_trigger_orphan_deletion=list,
        )
        languages: list[str] = ManyToMany(
            description="A language this person masters, in ISO639-3",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(Language),
            example=["eng", "fra", "spa"],
            default_factory_pydantic=list,
        )

        member_of: list[str] = ManyToMany(
            description="The list of Organisations that a Person affiliates with.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(Organisation),
            example=[],
            default_factory_pydantic=list,
        )


deserializer_list = FindByIdentifierDeserializerList(Person)
AIoDEntryORM.RelationshipConfig.editor.deserializer = deserializer_list  # type: ignore
deserializer_single = FindByIdentifierDeserializer(Person)
Contact.RelationshipConfig.person.deserializer = deserializer_single  # type: ignore

person_versions = VersionedResourceCollection(
    {
        Version.V2: VersionedResource(Person),
        Version.LATEST: VersionedResource(Person),
    }
)
