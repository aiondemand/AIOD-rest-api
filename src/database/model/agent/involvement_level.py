# database/model/agent/involvement_level.py

from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from database.model.concept.concept import AIoDConceptBase, AIoDConcept
from database.model.agent.expertise import Expertise
from database.model.relationships import ManyToOne
from database.model.serializers import (
    AttributeSerializer,
    FindByNameDeserializer,
    FindByIdentifierDeserializer,
)
from sqlalchemy import Column, Integer, ForeignKey, String
from database.model.field_length import NORMAL, SHORT, IDENTIFIER_LENGTH

if TYPE_CHECKING:
    from database.model.agent.organisation import Organisation


class InvolvementLevel(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "involvement_level"

    identifier: Optional[int] = Field(default=None, primary_key=True)

    involvement_level: Optional[str] = Field(
        default=None, description="Involvement level (e.g., high, medium, low)."
    )

    organisation_identifier: str | None = Field(
        default=None,
        foreign_key="organisation.identifier",
        description="Identifier of the organisation that has this involvement.",
    )

    involvement_area_identifier: int | None = Field(
        default=None,
        foreign_key="expertise.identifier",
        description="Expertise area involved in this level.",
    )

    organisation: Optional["Organisation"] = Relationship(back_populates="involved_in_area")
    involvement_area: Optional["Expertise"] = Relationship()

    class RelationshipConfig:
        organisation: Optional[str] = ManyToOne(
            description="The organisation that has this membership.",
            identifier_name="organisation_identifier",
            _serializer=AttributeSerializer("identifier"),
        )
        involvement_area: Optional[str] = ManyToOne(
            description="The expertise area involved in this level.",
            identifier_name="involvement_area_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Expertise),
        )


# Ignored code below (attempt to separate base and ORM models for better serilization):
# class InvolvementLevelBase(SQLModel):
#     involvement_level: Optional[str] = Field(
#         default=None,
#         description="Involvement level (e.g., high, medium, low)."
#     )


# class InvolvementLevelORM(InvolvementLevelBase, table=True):  # type: ignore[call-arg]
#     __tablename__ = "involvement_level"

#     identifier: Optional[int] = Field(default=None, primary_key=True)

#     organisation_identifier: str | None = Field(
#         sa_column=Column(
#             String(IDENTIFIER_LENGTH),
#             ForeignKey("organisation.identifier", ondelete="CASCADE"),
#         )
#     )
#     organisation: Optional["Organisation"] = Relationship(
#         back_populates="involved_in_area"
#     )

#     involvement_area_identifier: int | None = Field(
#         sa_column=Column(Integer, ForeignKey("expertise.identifier", ondelete="CASCADE"))
#     )
#     involvement_area: Optional["Expertise"] = Relationship()

#     class RelationshipConfig:
#         organisation: Optional["Organisation"] = ManyToOne(
#             description="The organisation that has this membership.",
#             identifier_name="organisation_identifier",
#             _serializer=AttributeSerializer("identifier"),
#             deserializer=FindByIdentifierDeserializer("organisation"),
#         )
#         involvement_area: Optional["Expertise"] = ManyToOne(
#             description="The expertise area involved in this level.",
#             identifier_name="involvement_area_identifier",
#             _serializer=AttributeSerializer("name"),
#             deserializer=FindByNameDeserializer("expertise"),
#         )


# class InvolvementLevel(InvolvementLevelBase):
#     """A representation of an organisation’s involvement in an area with a given level."""

#     organisation: Optional["Organisation"] = Field(default=None)
#     involvement_area: Optional["Expertise"] = Field(default=None)
