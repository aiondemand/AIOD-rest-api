from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, Integer, ForeignKey, String
from sqlmodel import Field, Relationship

from database.model.agent.email import Email
from database.model.agent.location import LocationORM, Location
from database.model.agent.telephone import Telephone
from database.model.concept.concept import AIoDConceptBase, AIoDConcept
from database.model.field_length import NORMAL, IDENTIFIER_LENGTH
from database.model.helper_functions import many_to_many_link_factory
from database.model.relationships import ManyToMany, OneToMany, OneToOne
from database.model.serializers import (
    AttributeSerializer,
    CastDeserializerList,
    FindByNameDeserializerList,
)
from versioning import Version, VersionedResource, VersionedResourceCollection

if TYPE_CHECKING:
    from database.model.agent.person import Person
    from database.model.agent.organisation import Organisation


class ContactBase(AIoDConceptBase):
    name: str | None = Field(
        max_length=NORMAL,
        description="The name of this contact, especially useful if "
        "it is not known whether this contact is a person "
        "or organisation. For persons, it is preferred to "
        "store this information as contact.person.surname "
        "and contact.person.firstname. For organisations, "
        "store it as contact.organisation.legal_name.",
        schema_extra={"example": "Ada Lovelace"},
    )


class Contact(ContactBase, AIoDConcept, table=True):  # type: ignore [call-arg]
    __tablename__ = "contact"
    __abbreviation__ = "con"
    __plural__ = "contacts"

    email: list[Email] = Relationship(
        link_model=many_to_many_link_factory(
            table_from="contact", from_identifier_type=str, table_to=Email.__tablename__
        )
    )
    location: list[LocationORM] = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})
    telephone: list[Telephone] = Relationship(
        link_model=many_to_many_link_factory(
            table_from="contact", from_identifier_type=str, table_to=Telephone.__tablename__
        )
    )
    organisation_identifier: str | None = Field(
        sa_column=Column(String(IDENTIFIER_LENGTH), ForeignKey("organisation.identifier"))
    )
    organisation: Optional["Organisation"] = Relationship(
        back_populates="contact_details", sa_relationship_kwargs={"uselist": False}
    )
    person_identifier: str | None = Field(
        sa_column=Column(String(IDENTIFIER_LENGTH), ForeignKey("person.identifier"))
    )
    person: Optional["Person"] = Relationship(
        back_populates="contact_details", sa_relationship_kwargs={"uselist": False}
    )

    class RelationshipConfig(AIoDConcept.RelationshipConfig):
        email: list[str] = ManyToMany(
            description="An email address.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(Email),
            on_delete_trigger_orphan_deletion=lambda: ["contact_email_link"],
            default_factory_pydantic=list,
        )
        location: list[Location] = OneToMany(
            deserializer=CastDeserializerList(LocationORM),
            default_factory_pydantic=list,  # no deletion trigger: cascading delete is used
        )
        telephone: list[str] = ManyToMany(
            description="A telephone number, including the land code.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializerList(Telephone),
            on_delete_trigger_orphan_deletion=lambda: ["contact_telephone_link"],
            default_factory_pydantic=list,
        )
        organisation: Optional[str] = OneToOne(
            _serializer=AttributeSerializer("identifier"),
        )
        person: Optional[str] = OneToOne(
            _serializer=AttributeSerializer("identifier"),
        )

    @property
    def contact_name(self) -> str | None:
        if self.organisation and self.organisation.legal_name:
            return self.organisation.legal_name
        if self.person and (self.person.surname or self.person.given_name):
            return ", ".join(
                [name for name in (self.person.surname, self.person.given_name) if name]
            )
        return self.name


contact_versions = VersionedResourceCollection(
    {
        Version.V2: VersionedResource(Contact),
        Version.LATEST: VersionedResource(Contact),
    }
)
