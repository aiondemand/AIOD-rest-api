from datetime import date
from typing import Optional

from sqlmodel import Field, Relationship

from database.model.agent.agent import AgentBase, Agent
from database.model.agent.agent_table import AgentTable
from database.model.agent.contact import Contact
from database.model.agent.organisation_type import OrganisationType
from database.model.field_length import NORMAL, LONG
from database.model.helper_functions import many_to_many_link_factory
from database.model.relationships import ManyToOne, ManyToMany, OneToOne
from database.model.serializers import (
    AttributeSerializer,
    FindByNameDeserializer,
    FindByIdentifierDeserializer,
)


class OrganisationBase(AgentBase):
    date_founded: date | None = Field(
        description="The date on which the organisation was founded.",
        schema_extra={"example": "2022-01-01"},
    )
    legal_name: str | None = Field(
        description="The official legal name of the organisation.",
        schema_extra={"example": "The Organisation Name"},
        max_length=NORMAL,
    )
    ai_relevance: str | None = Field(
        description="A description of positioning of the organisation within "
        "the broader European AI ecosystem.",
        schema_extra={"example": "Part of CLAIRE, focussing on explainable AI."},
        max_length=LONG,
    )


class Organisation(OrganisationBase, Agent, table=True):  # type: ignore [call-arg]
    __tablename__ = "organisation"

    contact_details: Optional[Contact] = Relationship(sa_relationship_kwargs={"uselist": False})

    type_identifier: int | None = Field(foreign_key=OrganisationType.__tablename__ + ".identifier")
    type: Optional[OrganisationType] = Relationship()

    member: list[AgentTable] = Relationship(
        link_model=many_to_many_link_factory("organisation", AgentTable.__tablename__),
    )

    class RelationshipConfig(Agent.RelationshipConfig):
        contact_details: int | None = OneToOne(
            description="The contact details by which this organisation can be reached",
            deserializer=FindByIdentifierDeserializer(Contact),
            _serializer=AttributeSerializer("identifier"),
        )
        type: Optional[str] = ManyToOne(
            description="The type of organisation.",
            identifier_name="type_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(OrganisationType),
            example="Research Institution",
        )
        member: list[int] = ManyToMany(
            description="The identifier of an agent (e.g. organisation or person) that is a "
            "member of this organisation.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializer(AgentTable),
            default_factory_pydantic=list,
        )
