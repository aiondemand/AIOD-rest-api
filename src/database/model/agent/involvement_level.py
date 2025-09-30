# database/model/agent/involvement_level.py

from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from database.model.concept.concept import AIoDConceptBase, AIoDConcept
from database.model.agent.expertise import Expertise
from database.model.relationships import ManyToOne
from database.model.serializers import AttributeSerializer

if TYPE_CHECKING:
    from database.model.agent.organisation import Organisation


class InvolvementLevel(SQLModel, table=True):  # type: ignore[call-arg]

    __tablename__ = "involvement_level"

    identifier: Optional[int] = Field(default=None, primary_key=True)

    involvement_level: Optional[str] = Field(
        default=None,
        description="Involvement level (e.g., high, medium, low)."
    )

    organisation_identifier: str | None = Field(
        default=None,
        foreign_key="organisation.identifier",
        description="Identifier of the organisation that has this involvement."
    )

    involvement_area_identifier: int | None = Field(
        default=None,
        foreign_key="expertise.identifier",
        description="Expertise area involved in this level."
    )
    

    organisation: Optional["Organisation"] = Relationship(
        back_populates="involved_in_area"
    )
    involvement_area: Optional["Expertise"] = Relationship()


    class RelationshipConfig:
        organisation: Optional[str] = ManyToOne(
            description="The organisation that has this membership.",
            identifier_name="organisation_identifier",
            _serializer=AttributeSerializer("identifier"),
        )
        involvement_area: Optional[int] = ManyToOne(
            description="The expertise area involved in this level.",
            identifier_name="involvement_area_identifier",
            _serializer=AttributeSerializer("identifier"),
        )
