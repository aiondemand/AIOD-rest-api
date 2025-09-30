from datetime import date
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship

from database.model.named_relation import Taxonomy, create_taxonomy
from database.model.agent.agent import AgentBase, Agent
from database.model.agent.agent_table import AgentTable
from database.model.agent.contact import Contact
from database.model.field_length import NORMAL, LONG
from database.model.helper_functions import many_to_many_link_factory
from database.model.relationships import ManyToOne, ManyToMany, OneToOne, OneToMany
from database.model.serializers import (
    AttributeSerializer,
    FindByNameDeserializer,
    FindByIdentifierDeserializer,
    FindByIdentifierDeserializerList,
)
from versioning import Version, VersionedResource, VersionedResourceCollection
from typing import cast
from sqlmodel import SQLModel
from database.model.resource_read_and_create import resource_read, resource_create
from versioning import schema_transform

from database.model.agent.network_membership import NetworkMembership
from database.model.agent.involvement_level import InvolvementLevel
from database.model.serializers import CastDeserializerList

# OrganisationInvolvementLevel: type[Taxonomy] = create_taxonomy(
#     class_name="OrganisationInvolvementLevel",
#     table_name="organisation_involvement_level",
#     plural_name="organisation involvement levels",
# )

# OrganisationNetworkMembership: type[Taxonomy] = create_taxonomy(
#     class_name="OrganisationNetworkMembership",
#     table_name="organisation_network_membership",
#     plural_name="organisation network memberships",
# )

OrganisationType: type[Taxonomy] = create_taxonomy(
    class_name="OrganisationType",
    table_name="organisation_type",
    plural_name="organisation types",
)

OrganisationActivityType: type[Taxonomy] = create_taxonomy(
    class_name="OrganisationActivityType",
    table_name="organisation_activity_type",
    plural_name="organisation activity types",
)

Turnover: type[Taxonomy] = create_taxonomy(
    class_name="Turnover",
    table_name="turnover",
    plural_name="turnovers",
)

NumberOfEmployees: type[Taxonomy] = create_taxonomy(
    class_name="NumberOfEmployees",
    table_name="number_of_employees",
    plural_name="numbers of employees",
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
    __abbreviation__ = "org"
    __plural__ = "organisations"

    contact_details: Optional[Contact] = Relationship(sa_relationship_kwargs={"uselist": False})

    type_identifier: int | None = Field(foreign_key=OrganisationType.__tablename__ + ".identifier")
    type: Optional[OrganisationType] = Relationship()  # type: ignore[valid-type]

    member: list[AgentTable] = Relationship(
        link_model=many_to_many_link_factory(
            "organisation",
            AgentTable.__tablename__,
            from_identifier_type=str,
            to_identifier_type=str,
        ),
    )

    turnover_identifier: int | None = Field(
        default=None,
        foreign_key="turnover.identifier",
        description="The revenue bracket of the organisation.",
    )
    turnover: Optional[Turnover] = Relationship()  # type: ignore[valid-type]

    number_of_employees_identifier: int | None = Field(
        default=None,
        foreign_key="number_of_employees.identifier",
        description="The employee size bracket of the organisation.",
    )
    number_of_employees: Optional[NumberOfEmployees] = Relationship()  # type: ignore[valid-type]

    has_activity_type_identifier: int | None = Field(
        default=None,
        foreign_key="organisation_activity_type.identifier",
        description="The activity type of the organisation.",
    )
    has_activity_type: Optional[OrganisationActivityType] = Relationship()  # type: ignore[valid-type]

    involved_in_area: list[InvolvementLevel] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Organisation.identifier==InvolvementLevel.organisation_identifier"
        }
    )

    has_membership_in: list[NetworkMembership] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "Organisation.identifier==NetworkMembership.organisation_identifier"
        }
    )

    class RelationshipConfig(Agent.RelationshipConfig):
        contact_details: str | None = OneToOne(
            description="The identifier of the contact details by which this organisation "
            "can be reached.",
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
        member: list[str] = ManyToMany(
            description="The identifier of an agent (e.g. organisation or person) that is a "
            "member of this organisation.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(AgentTable),
            default_factory_pydantic=list,
        )

        turnover: Optional[str] = ManyToOne(
            description="The approximate revenue bracket of the organisation in euros, see the taxonomy for more details.",
            identifier_name="turnover_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Turnover),
            example=">5 million euros",
        )

        number_of_employees: Optional[str] = ManyToOne(
            description=(
                "The number of employees of the organisation, see the taxonomy for more details."
            ),
            identifier_name="number_of_employees_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(NumberOfEmployees),
            example="<10",
        )

        has_activity_type: Optional[str] = ManyToOne(
            description="The activity type of the organisation.",
            identifier_name="has_activity_type_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(OrganisationActivityType),
            example="Applied research",
        )

        involved_in_area: list[InvolvementLevel] = OneToMany(
            description="The involvement levels that link this organisation to specific expertise areas.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=CastDeserializerList(InvolvementLevel),
            default_factory_pydantic=list,
        )

        has_membership_in: list[NetworkMembership] = OneToMany(
            description="The memberships that link this organisation to organisational networks.",
            _serializer=AttributeSerializer("identifier"),
            deserializer=CastDeserializerList(NetworkMembership),
            default_factory_pydantic=list,
        )


deserializer = FindByIdentifierDeserializer(Organisation)
Contact.RelationshipConfig.organisation.deserializer = deserializer  # type: ignore


def organisation_v3_to_v2() -> VersionedResource:
    """Drop new fields (has_activity_type, involved_in_area, has_membership_in) for V2 compatibility."""

    OrganisationV2Read = schema_transform(
        resource_read(Organisation),
        "OrganisationV2Read",
        remove_fields=[
            "has_activity_type",
            "involved_in_area",
            "has_membership_in",
        ],
    )

    OrganisationV2Create = schema_transform(
        resource_create(Organisation),
        "OrganisationV2Create",
        remove_fields=[
            "has_activity_type",
            "involved_in_area",
            "has_membership_in",
        ],
    )

    def orm_to_read(org: Organisation) -> OrganisationV2Read:  # type: ignore[valid-type]
        read = resource_read(Organisation).model_validate(org).model_dump()
        for f in ["has_activity_type", "involved_in_area", "has_membership_in"]:
            read.pop(f, None)
        return OrganisationV2Read.model_validate(read)

    def create_to_orm(org: OrganisationV2Create) -> Organisation:  # type: ignore[valid-type]
        fields = cast(SQLModel, org).model_dump()
        return Organisation.model_validate(fields)

    return VersionedResource(
        Organisation, OrganisationV2Create, OrganisationV2Read, create_to_orm, orm_to_read
    )


organisation_versions = VersionedResourceCollection(
    {
        Version.V3: VersionedResource(Organisation),
        Version.V2: organisation_v3_to_v2(),
        Version.LATEST: VersionedResource(Organisation),
    }
)
