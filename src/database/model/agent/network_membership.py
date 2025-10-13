from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from database.model.agent.organisational_network import OrganisationalNetwork
from database.model.relationships import ManyToOne
from database.model.serializers import (
    AttributeSerializer,
    StrictFindByNameFieldDeserializer,
)

if TYPE_CHECKING:
    from database.model.agent.organisation import Organisation


class NetworkMembership(SQLModel, table=True):  # type: ignore[call-arg]
    """
    NetworkMembership links an Organisation to an OrganisationalNetwork and carries
    the `with_network_role` property.
    """

    __tablename__ = "network_membership"

    identifier: Optional[int] = Field(default=None, primary_key=True)

    with_network_role: Optional[str] = Field(
        default=None,
        description="Role of the organisation within the network (e.g. 'Founding Member')",
    )
    organisation_identifier: str | None = Field(
        default=None,
        foreign_key="organisation.identifier",
        description="Identifier of the organisation that has this membership.",
    )
    in_network_identifier: str | None = Field(
        default=None,
        foreign_key="organisational_network.identifier",
        description="Identifier of the organisational network.",
    )

    organisation: Optional["Organisation"] = Relationship(back_populates="has_membership_in")
    in_network: Optional["OrganisationalNetwork"] = Relationship()

    class RelationshipConfig:
        organisation: Optional[str] = ManyToOne(
            description="The organisation that has this membership.",
            identifier_name="organisation_identifier",
            _serializer=AttributeSerializer("identifier"),
        )
        in_network: Optional[str] = ManyToOne(
            description="The organisational network this membership belongs to.",
            identifier_name="in_network_identifier",
            _serializer=AttributeSerializer("identifier"),
            deserializer=StrictFindByNameFieldDeserializer(OrganisationalNetwork, field="name"),
        )
